import uuid
from datetime import datetime
from sqlalchemy import String, BigInteger, Numeric, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import UuidPk, Timestamps


class Customer(Base, UuidPk, Timestamps):
    __tablename__ = "customers"
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                 ForeignKey("tenants.id"),
                                                 nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(180))
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB)


class Order(Base, UuidPk, Timestamps):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("tenant_id", "order_no"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                 ForeignKey("tenants.id"),
                                                 nullable=False, index=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                       ForeignKey("branches.id"))
    terminal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                          ForeignKey("terminals.id"))
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                          ForeignKey("customers.id"))
    order_no: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="created", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    subtotal_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tax_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    discount_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True),
                                                         ForeignKey("users.id"))

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order",
                                                    cascade="all, delete-orphan")


class OrderItem(Base, UuidPk):
    __tablename__ = "order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                ForeignKey("orders.id",
                                                           ondelete="CASCADE"),
                                                nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(80))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tax_amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    line_total: Mapped[int] = mapped_column(BigInteger, nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
