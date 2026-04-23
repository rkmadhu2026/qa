from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.core.deps import AuthContext, get_current_ctx

router = APIRouter(prefix="/api/v1", tags=["payments"])


@router.get("/payments")
def list_payments(status: str | None = None,
                  from_: datetime | None = None,
                  to: datetime | None = None,
                  limit: int = 100,
                  db: Session = Depends(get_db),
                  ctx: AuthContext = Depends(get_current_ctx)):
    stmt = (select(models.Payment)
            .where(models.Payment.tenant_id == ctx.tenant_id)
            .order_by(models.Payment.created_at.desc())
            .limit(limit))
    if status:
        stmt = stmt.where(models.Payment.status == status)
    if from_:
        stmt = stmt.where(models.Payment.created_at >= from_)
    if to:
        stmt = stmt.where(models.Payment.created_at <= to)
    rows = db.scalars(stmt).all()
    return [
        {
            "id": str(p.id),
            "gateway_payment_id": p.gateway_payment_id,
            "order_id": str(p.order_id) if p.order_id else None,
            "status": p.status,
            "amount": p.amount,
            "currency": p.currency,
            "method": p.method,
            "paid_at": p.paid_at,
            "created_at": p.created_at,
        }
        for p in rows
    ]


@router.post("/payments/{payment_id}/refund")
def refund_payment(payment_id: UUID, amount: int | None = None,
                   reason: str | None = None,
                   db: Session = Depends(get_db),
                   ctx: AuthContext = Depends(get_current_ctx)):
    from app.gateways.razorpay import get_razorpay
    p = db.get(models.Payment, payment_id)
    if not p or p.tenant_id != ctx.tenant_id:
        raise HTTPException(404, "Payment not found")
    refund_amount = amount or p.amount
    try:
        res = get_razorpay().create_refund(
            gateway_payment_id=p.gateway_payment_id,
            amount=refund_amount, reason=reason)
    except Exception as e:
        raise HTTPException(502, f"Gateway error: {e}")

    db.add(models.Refund(
        tenant_id=ctx.tenant_id,
        payment_id=p.id,
        gateway=p.gateway,
        gateway_refund_id=res.get("id"),
        status=res.get("status", "created"),
        amount=refund_amount,
        reason=reason,
        raw_payload=res,
    ))
    db.commit()
    return {"ok": True, "gateway_refund_id": res.get("id")}


@router.get("/dashboard/kpis")
def dashboard_kpis(db: Session = Depends(get_db),
                   ctx: AuthContext = Depends(get_current_ctx)):
    """Light KPI roll-up for merchant dashboard."""
    from sqlalchemy import func as F
    from datetime import timezone, timedelta

    now = datetime.now(tz=timezone.utc)
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_today = db.scalar(
        select(F.coalesce(F.sum(models.Payment.amount), 0))
        .where(models.Payment.tenant_id == ctx.tenant_id,
               models.Payment.status == "captured",
               models.Payment.paid_at >= start_today)
    ) or 0

    pending_qr = db.scalar(
        select(F.count(models.QrRequest.id))
        .where(models.QrRequest.tenant_id == ctx.tenant_id,
               models.QrRequest.status.in_(["active", "created", "scanned"]))
    ) or 0

    success = db.scalar(
        select(F.count(models.Payment.id))
        .where(models.Payment.tenant_id == ctx.tenant_id,
               models.Payment.status == "captured",
               models.Payment.paid_at >= start_today)
    ) or 0
    failed = db.scalar(
        select(F.count(models.Payment.id))
        .where(models.Payment.tenant_id == ctx.tenant_id,
               models.Payment.status == "failed",
               models.Payment.created_at >= start_today)
    ) or 0
    rate = round(100 * success / (success + failed), 2) if (success + failed) else 0.0

    return {
        "today_revenue_paise": int(total_today),
        "success_rate_pct": rate,
        "pending_qr": int(pending_qr),
        "failed_payments_today": int(failed),
    }
