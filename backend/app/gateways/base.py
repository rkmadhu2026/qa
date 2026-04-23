from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class GatewayAdapter(ABC):
    name: str

    @abstractmethod
    def create_qr(self, *, amount: int, currency: str, order_ref: str,
                  expires_at: datetime, usage_mode: str,
                  metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Returns: {gateway_qr_id, qr_payload, qr_image_url, expires_at, status, raw}"""

    @abstractmethod
    def fetch_qr(self, gateway_qr_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def close_qr(self, gateway_qr_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def fetch_payment(self, gateway_payment_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def create_refund(self, *, gateway_payment_id: str, amount: int,
                      reason: str | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> bool: ...

    @abstractmethod
    def normalize_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a normalized event: {event_type, event_id, payment?, qr?}"""
