from django.apps import AppConfig


class SchoolAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'school_admin'

    def ready(self):
        import school_admin.signals
