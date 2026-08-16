from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class DjangoClient:
    def __init__(self) -> None:
        self._base = settings.django_api_url.rstrip("/")
        self._headers = {
            "Content-Type": "application/json",
            "X-Agent-Secret": settings.agent_service_secret,
        }

    def _url(self, path: str) -> str:
        return f"{self._base}{path}"

    def get_context(self, negotiation_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(
                self._url(f"/internal/negotiations/{negotiation_id}/context/"),
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()

    def add_message(self, negotiation_id: str, role: str, body: str) -> None:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                self._url(f"/internal/negotiations/{negotiation_id}/messages/"),
                headers=self._headers,
                json={"role": role, "body": body},
            )
            response.raise_for_status()

    def add_quote(
        self,
        negotiation_id: str,
        *,
        unit_price: float,
        currency: str,
        moq: int,
        lead_time_days: int = 14,
    ) -> None:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                self._url(f"/internal/negotiations/{negotiation_id}/quotes/"),
                headers=self._headers,
                json={
                    "unitPrice": unit_price,
                    "currency": currency,
                    "moq": moq,
                    "leadTimeDays": lead_time_days,
                    "isSelected": True,
                },
            )
            response.raise_for_status()

    def patch_negotiation(self, negotiation_id: str, payload: dict[str, Any]) -> None:
        with httpx.Client(timeout=20.0) as client:
            response = client.patch(
                self._url(f"/internal/negotiations/{negotiation_id}/"),
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()

    def start_twilio_call(self, negotiation_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                self._url(f"/internal/negotiations/{negotiation_id}/twilio-call/"),
                headers=self._headers,
            )
            if response.status_code >= 400:
                detail = response.text
                try:
                    body = response.json()
                    detail = str(body.get("detail") or body)
                except ValueError:
                    pass
                raise RuntimeError(detail)
            return response.json()
