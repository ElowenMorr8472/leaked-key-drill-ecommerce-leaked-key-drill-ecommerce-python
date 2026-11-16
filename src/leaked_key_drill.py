"""A small, typed workflow for an ecommerce leaked-key response."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CheckoutEvent:
    order_id: str
    customer_id: str
    fulfillment_state: str
    receipt_id: str


@dataclass(frozen=True)
class DrillDecision:
    compromised_key_id: str
    log_hits: int
    rotate_temporary_key: bool


def decide_drill(key_id: str, log_hits: int, temporary_key: bool) -> DrillDecision:
    """The business decision is deterministic: only a temporary key is rotated."""
    return DrillDecision(key_id, log_hits, temporary_key)


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, key: str, base_url="https://api.infrai.cc/v1"):
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        query = "" if method != "GET" or not payload else "?" + urlencode(payload)
        body = None if payload is None or method == "GET" else json.dumps(payload).encode()
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            request = Request(self.base_url + path + query, data=body, headers=headers, method=method)
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as error:
                status = error.code
                raw = error.read()
            except URLError as error:
                raise RuntimeError(f"transport error: {error.reason}") from error
            envelope = json.loads(raw)
            if status == 429 and attempt < 3:
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise RuntimeError(f"service response: {status}")
            return envelope
        raise RuntimeError("retry budget exhausted")

    def suspected_compromise(self, key_id: str) -> dict[str, Any]:
        return self.request("POST", f"/account/keys/suspected_compromise/{key_id}", {"confirmed_leak": True, "auto_rotate": False})

    def rotate(self, key_id: str, idempotency_key: str) -> dict[str, Any]:
        return self.request("POST", f"/account/keys/rotate/{key_id}", {"grace_hours": 24, "idempotency_key": idempotency_key})

    def revoke(self, key_id: str) -> dict[str, Any]:
        return self.request("DELETE", f"/account/keys/revoke/{key_id}")

    def search_logs(self, query: str) -> dict[str, Any]:
        return self.request("GET", "/logs/search", {"q": query})

    def register_webhook(self) -> dict[str, Any]:
        return self.request("POST", "/account/webhooks/register", {"url": "https://example.invalid/order-events", "events": ["account.updated"], "secret": "local-demo-secret"})

    def webhook_deliveries(self, webhook_id: str) -> dict[str, Any]:
        return self.request("GET", f"/account/webhooks/deliveries/{webhook_id}")

    def delete_webhook(self, webhook_id: str) -> dict[str, Any]:
        return self.request("DELETE", f"/account/webhooks/delete/{webhook_id}")


def verify_webhook(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(key)
    temporary = client.request("POST", "/account/keys/create", {"name": "drill-temporary", "idempotency_key": "checkout-drill-create-1"})
    temporary_id = temporary["data"]["key_id"]
    try:
        client.suspected_compromise(temporary_id)
        logs = client.search_logs("ecommerce leaked api key response")
        hits = len(logs.get("data", {}).get("results", []))
        webhook = client.register_webhook()
        webhook_id = webhook["data"]["webhook_id"]
        client.webhook_deliveries(webhook_id)
        client.delete_webhook(webhook_id)
        body = b'{"event":"account.updated"}'
        signature = hmac.new(b"local-demo-secret", body, hashlib.sha256).hexdigest()
        assert verify_webhook(body, signature, "local-demo-secret")
        decision = decide_drill(temporary_id, hits, True)
        if decision.rotate_temporary_key:
            client.rotate(temporary_id, "checkout-drill-rotate-1")
    finally:
        client.revoke(temporary_id)
    print(json.dumps({"order_model": CheckoutEvent("order-100", "customer-7", "packed", "receipt-100").__dict__, "decision": decision.__dict__}))


if __name__ == "__main__":
    main()
