from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from django.conf import settings
from jwt import PyJWKClient
from rest_framework import authentication, exceptions


@dataclass
class SupabaseUser:
    """Minimal user object backed by a verified Supabase JWT."""

    id: UUID
    email: str | None = None
    full_name: str = ""

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def pk(self) -> UUID:
        return self.id


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient | None:
    base = (settings.SUPABASE_URL or "").rstrip("/")
    if not base:
        return None
    # New Supabase projects sign user JWTs with ES256; verify via JWKS.
    return PyJWKClient(f"{base}/auth/v1/.well-known/jwks.json", cache_keys=True)


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """Authenticate API requests with `Authorization: Bearer <supabase_access_token>`."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        payload = self._decode(token)
        user_id = payload.get("sub")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token missing subject")

        try:
            uid = UUID(str(user_id))
        except ValueError as exc:
            raise exceptions.AuthenticationFailed("Invalid user id in token") from exc

        meta = payload.get("user_metadata") or {}
        user = SupabaseUser(
            id=uid,
            email=payload.get("email"),
            full_name=str(meta.get("full_name") or payload.get("full_name") or ""),
        )
        return (user, payload)

    def _decode(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise exceptions.AuthenticationFailed(f"Invalid token header: {exc}") from exc

        alg = header.get("alg", "HS256")
        audience = "authenticated"
        issuer = None
        if settings.SUPABASE_URL:
            issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"

        try:
            if alg in {"ES256", "RS256"}:
                return self._decode_asymmetric(token, alg, audience, issuer)
            if alg == "HS256":
                return self._decode_symmetric(token, audience, issuer)
            raise exceptions.AuthenticationFailed(f"Unsupported JWT alg: {alg}")
        except exceptions.AuthenticationFailed:
            raise
        except jwt.PyJWTError as exc:
            raise exceptions.AuthenticationFailed(f"Invalid token: {exc}") from exc

    def _decode_asymmetric(
        self,
        token: str,
        alg: str,
        audience: str,
        issuer: str | None,
    ) -> dict[str, Any]:
        client = _jwks_client()
        if client is None:
            raise exceptions.AuthenticationFailed(
                "Server misconfigured: SUPABASE_URL is required for ES256/RS256 tokens"
            )

        signing_key = client.get_signing_key_from_jwt(token)
        options = {"verify_aud": True}
        kwargs: dict[str, Any] = {
            "algorithms": [alg],
            "audience": audience,
            "options": options,
        }
        if issuer:
            kwargs["issuer"] = issuer
        return jwt.decode(token, signing_key.key, **kwargs)

    def _decode_symmetric(
        self,
        token: str,
        audience: str,
        issuer: str | None,
    ) -> dict[str, Any]:
        secret = settings.SUPABASE_JWT_SECRET
        if not secret:
            raise exceptions.AuthenticationFailed(
                "Server misconfigured: SUPABASE_JWT_SECRET is not set"
            )

        kwargs: dict[str, Any] = {
            "algorithms": ["HS256"],
            "audience": audience,
        }
        if issuer:
            kwargs["issuer"] = issuer
        return jwt.decode(token, secret, **kwargs)
