from django.contrib import admin

# Register your models here.
from web.models import AgentConfig, AlertEmail, AlertWebhook, CustomUser, Agent, Metric, Alert
from import_export.admin import ImportExportModelAdmin
from import_export import resources


class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = CustomUserResource


################################################################


class AgentResource(resources.ModelResource):
    class Meta:
        model = Agent
        import_id_fields = ("token", "created", "user", "name", "ip", "port", "status")


@admin.register(Agent)
class AgentAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = AgentResource
    list_filter = ("name",)


################################################################


class MetricResource(resources.ModelResource):
    class Meta:
        model = Metric


@admin.register(Metric)
class MetricAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = MetricResource
    list_filter = ("agent__name", "created")


################################################################


class AgentConfigResource(resources.ModelResource):
    class Meta:
        model = AgentConfig


@admin.register(AgentConfig)
class AgentConfigAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = AgentConfigResource
    list_filter = ("agent__name",)


################################################################


class AlertResource(resources.ModelResource):
    class Meta:
        model = Alert


@admin.register(Alert)
class AlertAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = AlertResource
    list_filter = ("agent__name", "created")


################################################################


class AlertEmailResource(resources.ModelResource):
    class Meta:
        model = AlertEmail


@admin.register(AlertEmail)
class AlertEmailAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = AlertEmailResource
    list_filter = ("user", "email")


################################################################


class AlertWebhookResource(resources.ModelResource):
    class Meta:
        model = AlertWebhook


@admin.register(AlertWebhook)
class AlertWebhookAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = AlertWebhookResource
    list_filter = ("user", "webhook")
