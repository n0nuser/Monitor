from django.apps import AppConfig
# from web.tasks import startup_scheduling


class WebConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web"

    # def ready(self):
    #     startup_scheduling()
