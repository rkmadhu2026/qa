"""Webhook ingestion + payment state transitions.

Money-safe guarantees:
  * Raw payload is persisted BEFORE processing so replays are lossless.
  * Signature verification happens in the router against the raw body.
  * Payment upsert is idempotent via (gateway, gateway_payment_id).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app import models
from app.gateways.razorpay import get_razorpay


def persist_event(db: Session, *, gateway: str, signature_valid: bool,
                  payload: dict[str, Any]) -> models.WebhookEvent:
    evt = models.WebhookEvent(
        gateway=gateway,
        event_type=payload.get("event", "unknown"),
        event_id=str(payload.get("id") or ""),
        signature_valid=signature_valid,
        process_status="received",
        payload=payload,
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return evt


def process_event(db: Session, evt: models.WebhookEvent) -> str:
    if not evt.signature_valid:
        evt.process_status = "rejected_signature"
        db.commit()
        return evt.process_status

    gateway = get_razorpay()
    normalized = gateway.normalize_webhook(evt.payload)

    try:
        if payment := normalized.get("payment"):
            _apply_payment(db, evt, payment)
        elif qr := normalized.get("qr"):
            _apply_qr_state(db, qr)
        evt.process_status = "processed"
        evt.processed_at = datetime.now(tz=timezone.utc)
    except Exception as e:  # noqa: BLE001
        evt.process_status = f"error:{type(e).__name__}"
        db.commit()
        raise
    db.commit()
    return evt.process_status


def _apply_payment(db: Session, evt: models.WebhookEvent, p: dict[str, Any]) -> None:
    if not p.get("gateway_payment_id"):
        return

    # Link to QR (and thus order) via qr_code_id or order_ref in notes.
    qr: models.QrRequest | None = None
    if qr_id := p.get("qr_code_id"):
        qr = db.scalar(select(models.QrRequest)
                       .where(models.QrRequest.gateway_qr_id == qr_id))
    order: models.Order | None = None
    if qr:
        order = db.get(models.Order, qr.order_id)
    elif order_ref := p.get("gateway_order_ref"):
        order = db.scalar(select(models.Order)
                          .where(models.Order.order_no == order_ref))

    tenant_id = (order.tenant_id if order else (qr.tenant_id if qr else None))
    evt.tenant_id = tenant_id

    # Idempotent upsert
    existing = db.scalar(
        select(models.Payment).where(
            models.Payment.gateway == "razorpay",
            models.Payment.gateway_payment_id == p["gateway_payment_id"],
        )
    )
    if existing is None:
        db.add(models.Payment(
            tenant_id=tenant_id,
            order_id=order.id if order else None,
            qr_request_id=qr.id if qr else None,
            gateway="razorpay",
            gateway_payment_id=p["gateway_payment_id"],
            gateway_order_ref=p.get("gateway_order_ref"),
            status=p.get("status", "unknown"),
            method=p.get("method"),
            amount=int(p.get("amount") or 0),
            currency=p.get("currency", "INR"),
            paid_at=p.get("paid_at"),
            raw_payload=evt.payload,
        ))
    else:
        existing.status = p.get("status", existing.status)
        existing.paid_at = p.get("paid_at") or existing.paid_at
        existing.raw_payload = evt.payload

    # Order state transitions
    if order and p.get("status") == "captured":
        order.paid_amount = order.paid_amount + int(p.get("amount") or 0)
        if order.paid_amount >= order.total_amount:
            order.status = "paid"
        else:
            order.status = "partially_paid"
        if qr:
            qr.status = "paid"
            qr.closed_at = datetime.now(tz=timezone.utc)


def _apply_qr_state(db: Session, q: dict[str, Any]) -> None:
    qr = db.scalar(select(models.QrRequest)
                   .where(models.QrRequest.gateway_qr_id == q.get("gateway_qr_id")))
    if not qr:
        return
    new_status = (q.get("status") or "").lower()
    if new_status in ("closed", "expired", "paid"):
        qr.status = new_status
        qr.closed_at = datetime.now(tz=timezone.utc)
