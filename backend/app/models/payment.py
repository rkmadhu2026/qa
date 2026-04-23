import uuid
from datetime import datetime
from sqlalchemy import (String, BigInteger, Boolean, Text, ForeignKey,
                        DateTime, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models._mixins import UuidPk, Timestamps


class QrRequest(Base, UuidPk, Timestamps):
    __tablename__ = "qr_requests"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                 ForeignKey("tenants.id"),
                                                 nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                ForeignKey("orders.id"),
                                                nullable=False, index=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                        ForeignKey("branches.id"))
    terminal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                          ForeignKey("terminals.id"))

    gateway: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_qr_id: Mapped[str | None] = mapped_column(String(150), index=True)
    qr_type: Mapped[str] = mapped_column(String(30), default="dynamic", nullable=False)
    usage_mode: Mapped[str] = mapped_column(String(30), default="single_use",
                                            nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="created", nullable=False)

    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    qr_payload: Mapped[str | None] = mapped_column(Text)
    qr_image_url: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB)


class Payment(Base, UuidPk, Timestamps):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("gateway", "gateway_payment_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                 ForeignKey("tenants.id"),
                                                 nullable=False, index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                       ForeignKey("orders.id"),
                                                       index=True)
    qr_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                            ForeignKey("qr_requests.id"))

    gateway: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_payment_id: Mapped[str] = mapped_column(String(150), nullable=False)
    gateway_order_ref: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    method: Mapped[str | None] = mapped_column(String(50))
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)


class WebhookEvent(Base, UuidPk):
    __tablename__ = "webhook_events"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    gateway: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(180))
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  nullable=False,
                                                  server_default="now()")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    process_status: Mapped[str] = mapped_column(String(30), default="received",
                                                nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Settlement(Base, UuidPk, Timestamps):
    __tablename__ = "settlements"
    __table_args__ = (UniqueConstraint("gateway", "settlement_ref"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                 ForeignKey("tenants.id"),
                                                 nullable=False, index=True)
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)
    settlement_ref: Mapped[str] = mapped_column(String(150), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB)


class Refund(Base, UuidPk, Timestamps):
    __tablename__ = "refunds"
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                 ForeignKey("tenants.id"),
                                                 nullable=False, index=True)
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                  ForeignKey("payments.id"),
                                                  nullable=False, index=True)
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway_refund_id: Mapped[str | None] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
