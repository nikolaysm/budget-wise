"""
API router for application metadata endpoints.

Provides a simple `/version` endpoint to retrieve the current API version.
"""
from fastapi import APIRouter

from app.version import get_version

router = APIRouter()


@router.get("/version", tags=["meta"])
def version() -> dict[str, str]:
    return {"version": get_version()}
