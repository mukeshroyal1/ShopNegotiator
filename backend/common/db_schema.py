from __future__ import annotations

from django.db import connection


def suppliers_milestone1_ready() -> bool:
    """True when Milestone 1 supplier columns exist in Postgres."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select 1
                from information_schema.columns
                where table_schema = 'public'
                  and table_name = 'suppliers'
                  and column_name = 'phone'
                limit 1
                """
            )
            return cursor.fetchone() is not None
    except Exception:  # noqa: BLE001
        return False
