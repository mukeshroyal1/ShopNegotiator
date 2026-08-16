from __future__ import annotations

import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAgentService(BasePermission):
    """Allow requests that present the shared AGENT_SERVICE_SECRET."""

    message = "Invalid or missing agent secret."

    def has_permission(self, request, view) -> bool:
        expected = (getattr(settings, "AGENT_SERVICE_SECRET", None) or "").strip()
        if not expected:
            return False
        provided = request.META.get("HTTP_X_AGENT_SECRET", "")
        if not provided:
            return False
        return hmac.compare_digest(provided, expected)
