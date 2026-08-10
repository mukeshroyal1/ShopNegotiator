"""Runserver that skips migration checks (schema is applied via Supabase SQL)."""

from django.core.management.commands.runserver import Command as BaseRunserverCommand


class Command(BaseRunserverCommand):
    def check_migrations(self) -> None:
        self.stdout.write("Skipping migration checks (schema owned by Supabase SQL).")
