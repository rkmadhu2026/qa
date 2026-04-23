from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    item_name: str
    sku: str | None = None
    quantity: float = Field(gt=0)
    unit_price: int = Field(ge=0)  # paise
    tax_amount: int = Field(default=0, ge=0)


class CustomerIn(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None


class OrderCreate(BaseModel):
    branch_id: UUID | None = None
    terminal_id: UUID | None = None
    customer: CustomerIn | None = None
    items: list[OrderItemIn]
    discount_amount: int = 0
    tax_amount: int = 0
    notes: str | None = None


class OrderOut(BaseModel):
    id: UUID
    order_no: str
    status: str
    total_amount: int
    paid_amount: int
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class QrCreate(BaseModel):
    gateway: str = "razorpay"
    usage_mode: str = "single_use"
    expires_in_seconds: int = 300
    customer_name: str | None = None
    customer_phone: str | None = None


class QrOut(BaseModel):
    qr_request_id: UUID
    order_id: UUID
    status: str
    amount: int
    currency: str
    expires_at: datetime | None
    qr_image_url: str | None
    qr_payload: str | None
    gateway: str

    class Config:
        from_attributes = True
