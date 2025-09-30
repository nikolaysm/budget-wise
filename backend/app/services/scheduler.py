# scheduler.py

"""
Central APScheduler setup with job registration.

We use AsyncIOScheduler inside the FastAPI process.
Jobs:
 - auto_category_suggestions: periodically attempt ML category suggestion
   (non-destructive; logs counts for now – extend to auto-assign)
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import get_settings
from app.daos.account_dao import AccountDAO
from app.daos.category_dao import CategoryDAO
from app.daos.transaction_dao import TransactionDAO
from app.services.transaction_service import TransactionService

logger = logging.getLogger(get_settings().app_logger_name)

scheduler: AsyncIOScheduler | None = None
JOB_ID_SUGGEST = "auto_category_suggestions"
PG_LOCK_KEY = 0xA1C0_57A7  # stable 32-bit int per job


@contextmanager
def _db_session() -> Iterator[Session]:
    gen = get_db()
    try:
        db: Session = next(gen)
        try:
            yield db
        finally:
            # let the dependency generator run its teardown/close
            try:
                next(gen)
            except StopIteration:
                pass
    except StopIteration as e:
        raise RuntimeError("get_db() yielded no session") from e


def _try_pg_lock(db: Session, key: int) -> bool:
    # SELECT pg_try_advisory_lock(key)
    val = db.scalar(select(func.pg_try_advisory_lock(key)))
    return bool(val)


def _unlock_pg(db: Session, key: int) -> None:
    db.scalar(select(func.pg_advisory_unlock(key)))


async def _suggest_categories_job() -> None:
    """Async wrapper; do blocking work in a thread pool; guard with advisory lock."""
    import asyncio

    loop = asyncio.get_running_loop()

    def _work() -> tuple[int, int]:
        with _db_session() as db:
            if not _try_pg_lock(db, PG_LOCK_KEY):
                logger.info("Job %s skipped (another node holds the lock)", JOB_ID_SUGGEST)
                return 0, 0
            try:
                service = TransactionService(
                    TransactionDAO(db), AccountDAO(db), CategoryDAO(db), db
                )
                suggestions = service.bulk_suggest_categories(limit=25)
                non_null = [s for s in suggestions if s.get("suggested")]
                return len(non_null), len(suggestions)
            except Exception:  # pragma: no cover
                logger.exception("Scheduler suggestion job failed")
                return 0, 0
            finally:
                _unlock_pg(db, PG_LOCK_KEY)

    non_null, total = await loop.run_in_executor(None, _work)
    logger.info(
        "Scheduler: category suggestions produced %d/%d non-null (run at %s)",
        non_null,
        total,
        datetime.now(UTC).isoformat(),
    )


def start_scheduler() -> None:
    """Start background scheduler if enabled and not already running."""
    global scheduler
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled by configuration")
        return
    if scheduler is not None and scheduler.running:
        return

    # Persist jobs in Postgres so schedule survives restarts
    jobstores = {"default": SQLAlchemyJobStore(url=settings.database_url)}

    job_defaults = {"coalesce": True, "max_instances": 1, "misfire_grace_time": 120}

    sched = AsyncIOScheduler(
        timezone=settings.scheduler_timezone,
        jobstores=jobstores,
        job_defaults=job_defaults,
    )

    sched.add_job(
        _suggest_categories_job,
        CronTrigger(minute="*/30"),
        id=JOB_ID_SUGGEST,
        replace_existing=True,
        jitter=30,  # small spread to avoid thundering herd on resume
    )

    sched.start()
    scheduler = sched
    logger.info("APScheduler started; jobs: %s", [j.id for j in sched.get_jobs()])


def shutdown_scheduler() -> None:  # pragma: no cover
    """Shutdown scheduler if running."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
