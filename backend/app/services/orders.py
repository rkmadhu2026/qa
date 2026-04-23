import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app import models
from app.gateways.razorpay import get_razorpay
from app.schemas.order import OrderCreate, QrCreate


def _new_order_no() -> str:
    return "ORD-" + datetime.utcnow().strftime("%Y%m%d") + "-" + secrets.token_hex(3).upper()


def create_order(db: Session, *, tenant_id: UUID, user_id: UUID,
                 payload: OrderCreate) -> models.Order:
    subtotal = sum(int(i.unit_price) * int(i.quantity) for i in payload.items)
    tax = sum(int(i.tax_amount) for i in payload.items) + payload.tax_amount
    total = max(0, subtotal + tax - payload.discount_amount)

    customer_id = None
    if payload.customer and (payload.customer.name or payload.customer.phone):
        cust = models.Customer(
            tenant_id=tenant_id,
            name=payload.customer.name,
            phone=payload.customer.phone,
            email=payload.customer.email,
        )
        db.add(cust)
        db.flush()
        customer_id = cust.id

    order = models.Order(
        tenant_id=tenant_id,
        branch_id=payload.branch_id,
        terminal_id=payload.terminal_id,
        customer_id=customer_id,
        order_no=_new_order_no(),
        status="created",
        subtotal_amount=subtotal,
        tax_amount=tax,
        discount_amount=payload.discount_amount,
        total_amount=total,
        notes=payload.notes,
        created_by=user_id,
    )
    db.add(order)
    db.flush()

    for it in payload.items:
        db.add(models.OrderItem(
            order_id=order.id,
            item_name=it.item_name,
            sku=it.sku,
            quantity=it.quantity,
            unit_price=it.unit_price,
            tax_amount=it.tax_amount,
            line_total=int(it.unit_price) * int(it.quantity) + int(it.tax_amount),
        ))

    db.commit()
    db.refresh(order)
    return order


def generate_qr(db: Session, *, tenant_id: UUID, order: models.Order,
                payload: QrCreate) -> models.QrRequest:
    if order.tenant_id != tenant_id:
        raise PermissionError("Order belongs to another tenant")
    if order.status in ("paid", "cancelled", "refunded"):
        raise ValueError(f"Cannot generate QR for order in state {order.status}")

    expires_at = datetime.now(tz=timezone.utc) + timedelta(
        seconds=payload.expires_in_seconds)

    gateway = get_razorpay()
    gw = gateway.create_qr(
        amount=order.total_amount,
        currency=order.currency,
        order_ref=order.order_no,
        expires_at=expires_at,
        usage_mode=payload.usage_mode,
        metadata={"tenant_id": str(tenant_id), "order_id": str(order.id)},
    )

    qr = models.QrRequest(
        tenant_id=tenant_id,
        order_id=order.id,
        branch_id=order.branch_id,
        terminal_id=order.terminal_id,
        gateway=gateway.name,
        gateway_qr_id=gw["gateway_qr_id"],
        qr_type="dynamic",
        usage_mode=payload.usage_mode,
        status="active",
        amount=order.total_amount,
        currency=order.currency,
        qr_payload=str(gw.get("qr_payload") or ""),
        qr_image_url=gw.get("qr_image_url"),
        expires_at=gw["expires_at"],
        meta={"raw": _safe(gw.get("raw"))},
    )
    db.add(qr)
    order.status = "qr_generated"
    db.commit()
    db.refresh(qr)
    return qr


def _safe(v):
    try:
        import json
        json.dumps(v)
        return v
    except Exception:
        return str(v)
