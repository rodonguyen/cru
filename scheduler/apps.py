from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    """Configuration for the scheduler app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "scheduler"
    verbose_name = "Task Scheduler"

    def ready(self) -> None:
        """App initialization - called when Django starts."""
        # Import any signal handlers here if needed in the future
        pass
