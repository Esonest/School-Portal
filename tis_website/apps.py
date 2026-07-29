

from django.apps import AppConfig


class TisWebsiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tis_website"

    def ready(self):
        import tis_website.signals