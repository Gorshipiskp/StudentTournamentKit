"""Readiness probe — requires MySQL."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.infrastructure.persistence.db import check_database

router = APIRouter(tags=["ops"])


@router.get("/ready", response_model=None)
def ready():
    if not check_database():
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}
