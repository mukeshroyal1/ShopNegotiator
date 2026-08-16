from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import settings


class LlmError(RuntimeError):
    pass


def chat_json(*, system: str, user: str) -> dict[str, Any]:
    key = (settings.openai_api_key or "").strip()
    if not key:
        raise LlmError(
            "OPENAI_API_KEY is not set on the agent. Add it to agent/.env."
        )

    model = (settings.openai_model or "gpt-4o-mini").strip()
    payload = {
        "model": model,
        "temperature": 0.6,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    with httpx.Client(timeout=25.0) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if response.status_code >= 400:
        raise LlmError(f"OpenAI error {response.status_code}: {response.text[:400]}")

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmError(f"Unexpected OpenAI response: {data}") from exc

    return _parse_json(content)


def _parse_json(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmError(f"Model returned non-JSON: {text[:300]}") from exc
    if not isinstance(parsed, dict):
        raise LlmError("Model JSON must be an object")
    return parsed
