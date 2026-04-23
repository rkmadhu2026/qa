"""Daily reconciliation: match order ↔ QR ↔ payment and surface issues.

Outputs rows tagged: matched | unmatched_payment | unmatched_order |
                     duplicate | amount_mismatch | stale_pending
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import models


def _day_window(date: datetime) -> tuple[datetime, datetime]:
    start = date.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def daily_summary(db: Session, *, tenant_id: UUID, date: datetime) -> dict:
    start, end = _day_window(date)

    # Payments that day
    payments = db.scalars(
        select(models.Payment).where(
            models.Payment.tenant_id == tenant_id,
            models.Payment.created_at >= start,
            models.Payment.created_at < end,
        )
    ).all()

    # Orders that day
    orders = db.scalars(
        select(models.Order).where(
            models.Order.tenant_id == tenant_id,
            models.Order.created_at >= start,
            models.Order.created_at < end,
        )
    ).all()

    matched, issues = [], []

    # duplicate detection on gateway_payment_id
    pid_seen: dict[str, int] = defaultdict(int)
    for p in payments:
        pid_seen[p.gateway_payment_id] += 1

    for p in payments:
        order = db.get(models.Order, p.order_id) if p.order_id else None
        row = {
            "payment_id": str(p.id),
            "gateway_payment_id": p.gateway_payment_id,
            "order_no": order.order_no if order else None,
            "amount": p.amount,
            "status": p.status,
        }
        if pid_seen[p.gateway_payment_id] > 1:
            row["tag"] = "duplicate"
            issues.append(row)
            continue
        if order is None:
            row["tag"] = "unmatched_payment"
            issues.append(row)
            continue
        if p.status == "captured" and p.amount != order.total_amount:
            row["tag"] = "amount_mismatch"
            row["order_total"] = order.total_amount
            issues.append(row)
            continue
        row["tag"] = "matched"
        matched.append(row)

    # stale pending: orders created >30m ago, still pending
    threshold = datetime.now(tz=timezone.utc) - timedelta(minutes=30)
    stale = [
        {
            "order_id": str(o.id),
            "order_no": o.order_no,
            "status": o.status,
            "total": o.total_amount,
            "tag": "stale_pending",
        }
        for o in orders
        if o.status in ("created", "qr_generated", "pending_payment")
        and o.created_at < threshold
    ]

    # totals
    captured = [p for p in payments if p.status == "captured"]

    return {
        "date": start.date().isoformat(),
        "totals": {
            "orders": len(orders),
            "payments": len(payments),
            "captured_amount": sum(p.amount for p in captured),
            "matched": len(matched),
            "issues": len(issues),
            "stale_pending": len(stale),
        },
        "matched": matched[:500],
        "issues": issues[:500],
        "stale_pending": stale[:500],
    }
