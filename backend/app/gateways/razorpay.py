"""Razorpay gateway adapter.

Docs: https://razorpay.com/docs/payments/payment-methods/upi/qr-codes/apis/
The QR Codes API creates dynamic QR with `type="upi_qr"`, optional
`fixed_amount=true`, and `payment_amount` in paise. Webhook events
(`qr_code.credited`, `payment.captured`, etc.) are HMAC-SHA256 signed.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import razorpay

from app.core.config import settings
from app.core.security import verify_webhook_signature
from app.gateways.base import GatewayAdapter


class RazorpayAdapter(GatewayAdapter):
    name = "razorpay"

    def __init__(self) -> None:
        self._client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    # ---------- QR ----------
    def create_qr(self, *, amount: int, currency: str, order_ref: str,
                  expires_at: datetime, usage_mode: str,
                  metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        body = {
            "type": "upi_qr",
            "name": f"Order {order_ref}",
            "usage": "single_use" if usage_mode == "single_use" else "multiple_use",
            "fixed_amount": True,
            "payment_amount": amount,              # paise
            "description": f"Payment for {order_ref}",
            "close_by": int(expires_at.timestamp()),
            "notes": {"order_ref": order_ref, **(metadata or {})},
        }
        resp = self._client.qrcode.create(data=body)
        return {
            "gateway_qr_id": resp["id"],
            "qr_payload": resp.get("payment_amount") and resp.get("image_url"),
            "qr_image_url": resp.get("image_url"),
            "expires_at": datetime.fromtimestamp(resp["close_by"], tz=timezone.utc),
            "status": resp.get("status", "active"),
            "raw": resp,
        }

    def fetch_qr(self, gateway_qr_id: str) -> dict[str, Any]:
        return self._client.qrcode.fetch(gateway_qr_id)

    def close_qr(self, gateway_qr_id: str) -> dict[str, Any]:
        return self._client.qrcode.close(gateway_qr_id)

    # ---------- Payments / refunds ----------
    def fetch_payment(self, gateway_payment_id: str) -> dict[str, Any]:
        return self._client.payment.fetch(gateway_payment_id)

    def create_refund(self, *, gateway_payment_id: str, amount: int,
                      reason: str | None = None) -> dict[str, Any]:
        data = {"amount": amount}
        if reason:
            data["notes"] = {"reason": reason}
        return self._client.payment.refund(gateway_payment_id, data)

    # ---------- Webhooks ----------
    def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> bool:
        sig = headers.get("x-razorpay-signature") or headers.get("X-Razorpay-Signature")
        return verify_webhook_signature(settings.RAZORPAY_WEBHOOK_SECRET,
                                        raw_body, sig or "")

    def normalize_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        event_type = payload.get("event", "unknown")
        out: dict[str, Any] = {"event_type": event_type, "event_id": payload.get("id")}

        entity = (
            payload.get("payload", {}).get("payment", {}).get("entity")
            or payload.get("payload", {}).get("qr_code", {}).get("entity")
            or {}
        )

        if event_type.startswith("payment."):
            out["payment"] = {
                "gateway_payment_id": entity.get("id"),
                "status": _normalize_status(entity.get("status")),
                "amount": entity.get("amount"),
                "currency": entity.get("currency", "INR"),
                "method": entity.get("method"),
                "paid_at": _maybe_dt(entity.get("created_at")),
                "gateway_order_ref": (entity.get("notes") or {}).get("order_ref"),
                "qr_code_id": entity.get("qr_code_id"),
            }
        elif event_type.startswith("qr_code."):
            out["qr"] = {
                "gateway_qr_id": entity.get("id"),
                "status": entity.get("status"),
                "order_ref": (entity.get("notes") or {}).get("order_ref"),
            }
        return out


# ---------- helpers ----------
_STATUS_MAP = {
    "created": "initiated",
    "authorized": "authorized",
    "captured": "captured",
    "refunded": "refunded",
    "failed": "failed",
}


def _normalize_status(s: str | None) -> str:
    return _STATUS_MAP.get((s or "").lower(), "unknown")


def _maybe_dt(ts: int | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


# Singleton
_razorpay: RazorpayAdapter | None = None


def get_razorpay() -> RazorpayAdapter:
    global _razorpay
    if _razorpay is None:
        _razorpay = RazorpayAdapter()
    return _razorpay
