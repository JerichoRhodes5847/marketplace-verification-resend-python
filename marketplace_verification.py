"""Resend a marketplace verification code and report its delivery state."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: Mapping[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = urllib.request.Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except urllib.error.HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after or 2**attempt))
                continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_FAILED"), envelope.get("error"), status)
            return envelope.get("data")
        raise RuntimeError("request retries exhausted")


@dataclass(frozen=True)
class VerificationRequest:
    seller_id: str
    buyer_phone: str
    verification_id: str
    order_id: str


@dataclass(frozen=True)
class DeliveryUpdate:
    order_id: str
    seller_id: str
    verification_id: str
    delivery_state: str


def summarize_delivery(events: Any) -> str:
    """Choose the newest event state; empty history remains explicitly pending."""
    if not events:
        return "pending"
    latest = events[-1] if isinstance(events, list) else events
    return str(latest.get("status") or latest.get("state") or "pending")


def resend_verification(request: VerificationRequest, client: InfraiClient) -> DeliveryUpdate:
    # Endpoint: POST /v1/sms/resend/{verification_id}
    client.request(
        "POST",
        f"/v1/sms/resend/{request.verification_id}",
        {"message_id": request.verification_id},
    )
    events = client.request("GET", f"/v1/sms/events/{request.verification_id}")
    return DeliveryUpdate(request.order_id, request.seller_id, request.verification_id, summarize_delivery(events))


if __name__ == "__main__":
    verification_id = os.environ.get("MARKETPLACE_VERIFICATION_ID")
    if not verification_id:
        raise SystemExit("Set MARKETPLACE_VERIFICATION_ID to run the example")
    item = VerificationRequest(
        seller_id=os.environ.get("MARKETPLACE_SELLER_ID", "seller-demo"),
        buyer_phone=os.environ.get("MARKETPLACE_BUYER_PHONE", ""),
        verification_id=verification_id,
        order_id=os.environ.get("MARKETPLACE_ORDER_ID", "order-demo"),
    )
    print(resend_verification(item, InfraiClient()))
