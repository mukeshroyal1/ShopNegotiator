from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self) -> None:
        # Ensure migration checks never block runserver; schema lives in Supabase SQL.
        from django.core.management.base import BaseCommand

        def _skip_migrations(self, *args, **kwargs) -> None:
            return None

        BaseCommand.check_migrations = _skip_migrations  # type: ignore[method-assign]
