from django.apps import AppConfig


class ChoreographyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "choreography"

    def ready(self):
        from choreography import signals
