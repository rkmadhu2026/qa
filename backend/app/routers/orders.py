from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.core.deps import AuthContext, get_current_ctx
from app.schemas.order import OrderCreate, OrderOut, QrCreate, QrOut
from app.services import orders as order_service

router = APIRouter(prefix="/api/v1", tags=["orders"])


@router.post("/orders", response_model=OrderOut)
def create_order(body: OrderCreate, db: Session = Depends(get_db),
                 ctx: AuthContext = Depends(get_current_ctx)):
    order = order_service.create_order(
        db, tenant_id=ctx.tenant_id, user_id=ctx.user_id, payload=body
    )
    return order


@router.get("/orders", response_model=list[OrderOut])
def list_orders(status: str | None = None, limit: int = 50,
                db: Session = Depends(get_db),
                ctx: AuthContext = Depends(get_current_ctx)):
    stmt = (select(models.Order)
            .where(models.Order.tenant_id == ctx.tenant_id)
            .order_by(models.Order.created_at.desc())
            .limit(limit))
    if status:
        stmt = stmt.where(models.Order.status == status)
    return db.scalars(stmt).all()


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: UUID, db: Session = Depends(get_db),
              ctx: AuthContext = Depends(get_current_ctx)):
    order = db.get(models.Order, order_id)
    if not order or order.tenant_id != ctx.tenant_id:
        raise HTTPException(404, "Order not found")
    return order


@router.post("/orders/{order_id}/qr", response_model=QrOut)
def create_qr_for_order(order_id: UUID, body: QrCreate,
                        db: Session = Depends(get_db),
                        ctx: AuthContext = Depends(get_current_ctx)):
    order = db.get(models.Order, order_id)
    if not order or order.tenant_id != ctx.tenant_id:
        raise HTTPException(404, "Order not found")
    try:
        qr = order_service.generate_qr(db, tenant_id=ctx.tenant_id,
                                       order=order, payload=body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return QrOut(
        qr_request_id=qr.id,
        order_id=qr.order_id,
        status=qr.status,
        amount=qr.amount,
        currency=qr.currency,
        expires_at=qr.expires_at,
        qr_image_url=qr.qr_image_url,
        qr_payload=qr.qr_payload,
        gateway=qr.gateway,
    )


@router.get("/qr/{qr_id}", response_model=QrOut)
def get_qr(qr_id: UUID, db: Session = Depends(get_db),
           ctx: AuthContext = Depends(get_current_ctx)):
    qr = db.get(models.QrRequest, qr_id)
    if not qr or qr.tenant_id != ctx.tenant_id:
        raise HTTPException(404, "QR not found")
    return QrOut(
        qr_request_id=qr.id,
        order_id=qr.order_id,
        status=qr.status,
        amount=qr.amount,
        currency=qr.currency,
        expires_at=qr.expires_at,
        qr_image_url=qr.qr_image_url,
        qr_payload=qr.qr_payload,
        gateway=qr.gateway,
    )


@router.post("/qr/{qr_id}/close")
def close_qr(qr_id: UUID, db: Session = Depends(get_db),
             ctx: AuthContext = Depends(get_current_ctx)):
    from datetime import datetime, timezone
    from app.gateways.razorpay import get_razorpay
    qr = db.get(models.QrRequest, qr_id)
    if not qr or qr.tenant_id != ctx.tenant_id:
        raise HTTPException(404, "QR not found")
    if qr.gateway == "razorpay" and qr.gateway_qr_id:
        try:
            get_razorpay().close_qr(qr.gateway_qr_id)
        except Exception:
            pass
    qr.status = "closed"
    qr.closed_at = datetime.now(tz=timezone.utc)
    db.commit()
    return {"ok": True}
