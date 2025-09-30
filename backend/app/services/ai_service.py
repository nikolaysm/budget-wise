"""AI Inference Service

This module provides hybrid category classification for transaction text:

Workflow:
    1. Normalize noisy banking description text (unicode, boilerplate removal, punctuation stripping, token de-dup).
    2. Compute OpenAI embedding for the normalized text + candidate labels; rank by cosine similarity.
    3. (Optional) If embedding confidence is low (hybrid 'auto' mode) fall back to an LLM (chat completion JSON output)
         to choose the best label with a model-estimated confidence.

Key Features:
    * Thread-safe LRU + TTL caching on full embedding prediction sets.
    * Banking-specific noise regex to improve semantic signal.
    * Deterministic normalization to maximize cache hit rate.
    * Simple pluggable LLM fallback gated by configured completion model.

The previous corruption has been fully removed; this version intentionally keeps
the surface API lean while being easy to extend.
"""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt
from threading import Lock

# Third-party
from openai import OpenAI, OpenAIError

# Local
from app.core.config import get_settings

logger = logging.getLogger(get_settings().app_logger_name)

DEFAULT_EMBED_MODEL = "text-embedding-3-small"
MAX_LABELS = 128  # hard cap to avoid excessive token / embedding cost

DASHES = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"
BANK_NOISE = re.compile(
    rf"""(?ix)
    \b(
        BANCONTACT(?:/MISTER\s*CASH)? | CONTACTLESS | AANKOOP | BETALING | PAYMENT | PURCHASE |
        KAART | CARD | REF(?:\.||ERENCE)? | VAL(?:\.||ID)? | POS | SEPA | VIREMENT | IBAN | ATM | TERMINAL |
        TRANSACT(?:IE|ION) | ONLINE\s*BANK(?:ING)?
    )\b
    | [:/;\\\-{DASHES}]+ | \bX{{2,}}\b | \bBE\d{{2,}}\b | \d{{2,}}
    """,
    re.UNICODE,
)
_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)


@dataclass(slots=True)
class CategoryPrediction:
    label: str
    score: float


class _LRUCache:
    def __init__(self, capacity: int, ttl_sec: float | None = None) -> None:
        self.capacity = max(capacity, 0)
        self.ttl = ttl_sec
        self._store: OrderedDict[tuple, tuple[float, list[CategoryPrediction]]] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = Lock()

    def get(self, key: tuple) -> list[CategoryPrediction] | None:
        if not self.capacity:
            return None
        now = time.time()
        with self._lock:
            if key in self._store:
                ts, val = self._store[key]
                if self.ttl and (now - ts) > self.ttl:
                    del self._store[key]
                    self.misses += 1
                    return None
                self._store.move_to_end(key)
                self.hits += 1
                return val
            self.misses += 1
            return None

    def put(self, key: tuple, value: list[CategoryPrediction]) -> None:
        if not self.capacity:
            return
        with self._lock:
            self._store[key] = (time.time(), value)
            self._store.move_to_end(key)
            while len(self._store) > self.capacity:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0

    @property
    def size(self) -> int:  # pragma: no cover
        with self._lock:
            return len(self._store)


class AIInferenceService:
    """Embedding + optional LLM classification service.

    Parameters
    ----------
    embed_model: str | None
        Override embedding model name; otherwise taken from settings or default.
    cache_size: int
        Max number of distinct embedding result sets cached.
    cache_ttl_sec: float | None
        Optional per-entry time-to-live in seconds; None disables expiry.
    """

    def __init__(
        self,
        *,
        embed_model: str | None = None,
        cache_size: int = 128,
        cache_ttl_sec: float | None = 3600.0,
    ) -> None:
        settings = get_settings()
        self._settings = settings
        self._embed_model = embed_model or settings.openai_embedding_model or DEFAULT_EMBED_MODEL
        self._llm_model = settings.openai_completion_model
        self._cache = _LRUCache(cache_size, ttl_sec=cache_ttl_sec)
        self._last_meta: dict | None = None
        self._openai: OpenAI | None = None
        if settings.openai_api_key:
            try:
                self._openai = OpenAI(
                    api_key=settings.openai_api_key, timeout=settings.openai_timeout_sec
                )
            except Exception as exc:  # pragma: no cover
                logger.error("OpenAI client init failed: %s", exc)
        logger.info(
            "AIInferenceService ready embed_model=%s llm_model=%s cache=%d ttl=%s",
            self._embed_model,
            self._llm_model,
            cache_size,
            cache_ttl_sec,
        )

    def clear_cache(self) -> None:  # pragma: no cover
        self._cache.clear()

    def cache_stats(self) -> dict:  # pragma: no cover
        return {"size": self._cache.size, "hits": self._cache.hits, "misses": self._cache.misses}

    @staticmethod
    def _normalize_text(s: str) -> str:
        """Normalize raw transaction description for better semantic matching.

        Steps:
          1. Trim & unicode normalize (NFKC)
          2. Remove banking boilerplate & digit noise
          3. Strip punctuation to spaces
          4. Collapse whitespace
          5. De-duplicate tokens (case-insensitive) preserving order
        """
        s = (s or "").strip()
        s = unicodedata.normalize("NFKC", s)
        s = BANK_NOISE.sub(" ", s)
        s = _PUNCT.sub(" ", s)
        s = re.sub(r"\s+", " ", s).strip()
        out: list[str] = []
        seen: set[str] = set()
        for tok in s.split():
            k = tok.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(tok)
        return " ".join(out)

    # ------------- Embedding path -------------
    def predict(
        self,
        *,
        text: str,
        candidate_labels: Sequence[str],
        multi_label: bool = False,  # reserved
    ) -> list[CategoryPrediction]:
        return self._predict_embeddings(text=text, candidate_labels=candidate_labels)

    def _predict_embeddings(
        self,
        *,
        text: str,
        candidate_labels: Sequence[str],
    ) -> list[CategoryPrediction]:
        if not self._openai:
            return []
        norm = self._normalize_text(text)
        labels = [lbl.strip() for lbl in candidate_labels if lbl and lbl.strip()]
        seen: set[str] = set()
        labels = [lbl for lbl in labels if not (lbl in seen or seen.add(lbl))][:MAX_LABELS]
        if not labels or not norm:
            return []
        cache_key = ("emb", norm[:4000], tuple(labels))
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._last_meta = {"provider": "openai", "cache_hit": True, "labels": len(labels)}
            return cached
        start = time.perf_counter()
        try:
            inputs = [norm, *labels]
            resp = self._openai.embeddings.create(model=self._embed_model, input=inputs)
            vecs = [d.embedding for d in resp.data]
            if len(vecs) != len(inputs):
                return []
            text_vec = vecs[0]
            label_vecs = vecs[1:]

            def cosine(a, b):
                dot = sum(x * y for x, y in zip(a, b, strict=True))
                na = sqrt(sum(x * x for x in a))
                nb = sqrt(sum(x * x for x in b))
                return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

            preds = [
                CategoryPrediction(label=lab, score=cosine(text_vec, lv))
                for lab, lv in zip(labels, label_vecs, strict=False)
            ]
            preds.sort(key=lambda p: p.score, reverse=True)
            self._cache.put(cache_key, preds)
            self._last_meta = {
                "provider": "openai",
                "cache_hit": False,
                "elapsed_ms": (time.perf_counter() - start) * 1000,
                "labels": len(labels),
                "model": self._embed_model,
                "truncated": len(candidate_labels) > len(labels),
            }
            return preds
        except OpenAIError as oe:
            logger.error("Embedding error: %s", oe)
            return []
        except Exception as exc:  # pragma: no cover
            logger.exception("Embedding predict failed", exc_info=exc)
            return []

    # ------------- LLM fallback -------------
    def _predict_llm(
        self,
        *,
        text: str,
        candidate_labels: Sequence[str],
    ) -> list[CategoryPrediction] | None:
        if not self._llm_model or not self._openai or not hasattr(self._openai, "chat"):
            return None
        labels: list[str] = []
        seen: set[str] = set()
        for lbl in candidate_labels:
            if lbl and lbl not in seen:
                seen.add(lbl)
                labels.append(lbl)
        if not labels:
            return None
        messages = [
            {
                "role": "system",
                "content": "Classify banking transaction. Return JSON {label, confidence}.",
            },
            {"role": "user", "content": json.dumps({"text": text[:1200], "categories": labels})},
        ]
        start = time.perf_counter()
        try:
            chat = self._openai.chat.completions.create(  # type: ignore[attr-defined]
                model=self._llm_model,
                messages=messages,  # type: ignore[arg-type]
                temperature=0,
                response_format={"type": "json_object"},
            )
            raw = None
            try:
                raw = chat.choices[0].message.content  # type: ignore[index]
            except Exception:
                raw = None
            if not raw:
                return None
            try:
                parsed = json.loads(raw)
            except Exception:
                return None
            label = parsed.get("label")
            conf = parsed.get("confidence", 1.0)
            try:
                conf = float(conf)
            except Exception:
                conf = 1.0
            if label not in labels:
                return None
            self._last_meta = {
                "provider": "openai-llm",
                "model": self._llm_model,
                "elapsed_ms": (time.perf_counter() - start) * 1000,
                "labels": len(labels),
                "cache_hit": False,
            }
            return [CategoryPrediction(label=label, score=max(0.0, min(1.0, conf)))]
        except OpenAIError as oe:  # pragma: no cover
            logger.error("LLM error: %s", oe)
            return None
        except Exception:  # pragma: no cover
            logger.exception("LLM classification failed")
            return None

    # ------------- Hybrid convenience -------------
    def predict_hybrid(
        self,
        *,
        text: str,
        candidate_labels: Sequence[str],
        mode: str = "auto",
        embed_accept_min: float = 0.55,
    ) -> list[CategoryPrediction]:
        """Run prediction with selectable strategy.

        mode:
          'embedding' -> embeddings only
          'llm'       -> LLM only
          'auto'      -> embeddings then fallback if top score < embed_accept_min
        """
        m = (mode or "embedding").lower()
        if m == "embedding":
            return self._predict_embeddings(text=text, candidate_labels=candidate_labels)
        if m == "llm":
            return self._predict_llm(text=text, candidate_labels=candidate_labels) or []
        emb = self._predict_embeddings(text=text, candidate_labels=candidate_labels)
        if emb and emb[0].score >= embed_accept_min:
            return emb
        llm = self._predict_llm(text=text, candidate_labels=candidate_labels) or []
        return llm or emb

    def suggest_best(
        self,
        *,
        text: str,
        candidate_labels: Sequence[str],
        min_score: float = 0.4,
    ) -> CategoryPrediction | None:
        preds = self.predict(text=text, candidate_labels=candidate_labels)
        return preds[0] if preds and preds[0].score >= float(min_score) else None

    def suggest_best_hybrid(
        self,
        *,
        text: str,
        candidate_labels: Sequence[str],
        mode: str = "auto",
        embed_accept_min: float = 0.55,
        llm_conf_floor: float = 0.2,
    ) -> tuple[CategoryPrediction | None, str]:
        """Return (prediction | None, reason_code).

        reason_code values:
          'embed'                accepted embedding result
          'embed-low'            embedding score below threshold (and no LLM win)
          'llm'                  LLM produced acceptable result
          'llm-fallback-failed'  LLM path unavailable or low confidence
          'no-text'              empty/whitespace text
          'no-labels'            no candidate labels provided
        """
        if not text.strip():
            return None, "no-text"
        labels_list = [lbl for lbl in candidate_labels if lbl]
        if not labels_list:
            return None, "no-labels"
        m = (mode or "auto").lower()
        if m == "embedding":
            pred = self.suggest_best(
                text=text, candidate_labels=labels_list, min_score=embed_accept_min
            )
            return pred, ("embed" if pred else "embed-low")
        if m == "llm":
            llm = self._predict_llm(text=text, candidate_labels=labels_list) or []
            if llm and llm[0].score >= llm_conf_floor:
                return llm[0], "llm"
            return None, "llm-fallback-failed"
        emb_pred = self.suggest_best(
            text=text, candidate_labels=labels_list, min_score=embed_accept_min
        )
        if emb_pred:
            return emb_pred, "embed"
        llm = self._predict_llm(text=text, candidate_labels=labels_list) or []
        if llm and llm[0].score >= llm_conf_floor:
            return llm[0], "llm"
        return None, "embed-low"

    def last_metadata(self) -> dict | None:  # pragma: no cover
        return self._last_meta


__all__ = ["AIInferenceService", "CategoryPrediction"]
