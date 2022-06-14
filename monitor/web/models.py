import os
import binascii
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    email = models.EmailField(("email address"), unique=True)

    def __str__(self) -> str:
        return self.username

    class Meta:
        ordering = ["username"]
        verbose_name_plural = "Users"


class Agent(models.Model):
    STATUS_CHOICES = [
        ("OK", "OK"),
        ("WR", "WARNING"),
        ("BA", "BAD"),
        ("UN", "UNREACHEABLE"),
    ]

    def tokenfunc():
        return binascii.hexlify(os.urandom(20)).decode()

    token = models.CharField(max_length=50, default=tokenfunc, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, related_name="agents", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    ip = models.GenericIPAddressField(null=True, blank=True)
    port = models.IntegerField(
        default=8080,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, default="OK", blank=True, choices=STATUS_CHOICES)
    status_reason = models.CharField(max_length=200, default="", blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["ip"]
        verbose_name_plural = "Hosts"


class Metric(models.Model):
    agent = models.ForeignKey("Agent", related_name="metrics", on_delete=models.CASCADE)
    # If created is None, set created to timezone.now()
    # Created is None when an agent send their metric
    # Is not None if it's imported via import_export package
    created = models.DateTimeField(default=timezone.now, blank=True, null=False)
    status = models.JSONField()
    metrics = models.JSONField()

    def __str__(self) -> str:
        return f"{self.agent.name} - {self.created}"

    class Meta:
        ordering = ["created"]
        verbose_name_plural = "Metrics"


class AgentConfig(models.Model):
    LEVEL_CHOICES = [
        ("debug", "Debug"),
        ("info", "Informative"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical Error"),
    ]

    UVICORN_CHOICES = [
        ("trace", "Trace"),
        ("debug", "Debug"),
        ("info", "Informative"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("critical", "Critical Error"),
    ]

    agent = models.ForeignKey("Agent", on_delete=models.CASCADE, null=False)
    # RETRIEVAL BY OTHER MODELS/DATA
    # auth_agent_token <- self.agent.token
    # auth_name <- self.agent.name
    # auth_user_token <- Token.objects.get(user=self.agent.user).key
    # endpoints_agent <- By hand :(
    # endpoints_metric  <- By hand :(
    ####################################
    logging_filename = models.CharField(max_length=100, default="monitor.log", null=False)
    logging_level = models.CharField(max_length=9, default="info", choices=LEVEL_CHOICES, null=False)
    metrics_enable_logfile = models.BooleanField(default=False, null=False)
    metrics_get_endpoint = models.BooleanField(default=False, null=False)
    metrics_log_filename = models.CharField(max_length=100, default="metrics.json", null=False)
    metrics_post_interval = models.PositiveIntegerField(default=60, validators=[MinValueValidator(1)], null=False)
    warning_time_interval = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1)], null=False)
    bad_time_interval = models.PositiveIntegerField(default=60, validators=[MinValueValidator(1)], null=False)
    threshold_cpu_percent = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=False,
    )
    threshold_ram_percent = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=False,
    )
    uvicorn_backlog = models.PositiveIntegerField(default=2048, null=False)
    uvicorn_debug = models.BooleanField(default=False, null=False)
    uvicorn_host = models.GenericIPAddressField(default="0.0.0.0", null=False)
    uvicorn_log_level = models.CharField(max_length=9, default="trace", choices=UVICORN_CHOICES, null=False)
    uvicorn_port = models.PositiveIntegerField(
        default=8080,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        null=False,
    )
    uvicorn_reload = models.BooleanField(default=True, null=False)
    uvicorn_timeout_keep_alive = models.PositiveIntegerField(default=5, null=False)
    uvicorn_workers = models.PositiveIntegerField(default=4, null=False)

    def __str__(self) -> str:
        return f"{self.agent.name} config"

    class Meta:
        ordering = ["agent"]
        verbose_name_plural = "Hosts config"


class Alert(models.Model):
    agent = models.ForeignKey("Agent", on_delete=models.CASCADE, null=False)
    created = models.DateTimeField(auto_now_add=True)
    cpu_percent = models.FloatField(
        default=None,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    ram_percent = models.FloatField(
        default=None,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    processes = models.JSONField(default=None, null=True)

    def __str__(self) -> str:
        return f"{self.agent.name} alert - {self.created}"

    class Meta:
        ordering = ["created"]
        verbose_name_plural = "Alerts"

######################################################################################################################

# Se gestiona por usuario en vez de por agente
# Si se quiere individualizar la gestión de alertas por agente, que el usuario se cree otra cuenta.


class AlertEmail(models.Model):
    user = models.ForeignKey(CustomUser, related_name="alert_email", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.email}"

    class Meta:
        ordering = ["name", "email"]


class AlertWebhook(models.Model):
    user = models.ForeignKey(CustomUser, related_name="alert_webhook", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    webhook = models.URLField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.webhook}"

    class Meta:
        ordering = ["name", "webhook"]

######################################################################################################################


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_alert_email(sender, instance=None, created=False, **kwargs):
    if created:
        AlertEmail.objects.create(user=instance, name="Default", email=instance.email)


@receiver(post_save, sender=Agent)
def update_agent_name_config(sender, instance=None, created=False, **kwargs):
    if created:
        AgentConfig.objects.create(agent=instance)
    else:
        agent_config = AgentConfig.objects.get(agent=instance)
        agent_config.auth_name = instance.name
        agent_config.save()
