from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_ctx
from app.services.reconciliation import daily_summary

router = APIRouter(prefix="/api/v1/reconciliation", tags=["reconciliation"])


@router.get("/daily")
def recon_daily(date: str | None = Query(None, description="YYYY-MM-DD, UTC"),
                db: Session = Depends(get_db),
                ctx: AuthContext = Depends(get_current_ctx)):
    dt = datetime.fromisoformat(date) if date else datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return daily_summary(db, tenant_id=ctx.tenant_id, date=dt)
