from datetime import datetime, timedelta
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncMinute
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import DeleteView, UpdateView, CreateView, FormView
from rest_framework.authtoken.models import Token
from web.tasks import send_email_task
from web.utils import format_bytes
import contextlib
import json
import re


import web.models as models
import web.forms as forms

# Create your views here.


@login_required
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        load_template = request.path.split("/")[-1]
        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:
        html_template = loader.get_template("error-404.html")
        return HttpResponse(html_template.render(context, request))

    except Exception:
        html_template = loader.get_template("error-500.html")
        return HttpResponse(html_template.render(context, request))


def register_user(request):
    success = False

    if request.method == "POST":
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            authenticate(username=username, password=raw_password)
            messages.success(request=request, message="User created.")
            success = True

            html_content = loader.render_to_string(
                "email/default.html",
                {
                    "year": datetime.now().year,
                    "company": "Monitor",
                    "address": "Salamanca, Spain",
                    "url": "https://nonuser.es",
                    "header": f"Welcome to Monitor {username}",
                    "message": "Congratulations on setting up your account!"
                    "<br>You now have access to all account features!",
                },
            )
            send_email_task(
                to=[form.cleaned_data.get("email")],
                subject="Welcome to Monitor",
                html_message=html_content,
            )
            # return redirect("/login/")
        else:
            messages.error(request=request, message="Form is not valid.")
    else:
        form = forms.SignUpForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form, "success": success},
    )


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_message = (
        "We've emailed you instructions for setting your password, "
        "if an account exists with the email you entered. You should receive them shortly."
        " If you don't receive an email, "
        "please make sure you've entered the address you registered with, and check your spam folder."
    )
    success_url = reverse_lazy("login")


class PasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_message = "Your password has been reset. You can now log in."
    success_url = reverse_lazy("login")


class PasswordResetCompleteView(SuccessMessageMixin, PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
    success_message = "Your password has been reset. You can now log in."
    success_url = reverse_lazy("login")


@method_decorator(login_required, name="dispatch")
class Profile(TemplateView):
    model = models.CustomUser
    template_name = "accounts/profile.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["token"] = Token.objects.get(user=self.request.user).key
        return context


@method_decorator(login_required, name="dispatch")
class UpdateProfile(UpdateView):
    model = models.CustomUser
    form_class = forms.CustomUserForm
    template_name = "common/edit.html"
    success_url = reverse_lazy("profile")


def handler403(request, exception, template_name="errors/403.html"):
    return render(request, template_name, status=403)


def handler404(request, exception, template_name="errors/404.html"):
    return render(request, template_name, status=404)


def handler500(request, template_name="errors/500.html"):
    return render(request, template_name, status=500)


######################################################################################################################


@method_decorator(login_required, name="dispatch")
class HostCreateView(CreateView):
    model = models.Agent
    form_class = forms.AgentForm
    success_url = reverse_lazy("host-list")
    template_name = "common/add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class HostUpdateView(UpdateView):
    model = models.Agent
    form_class = forms.AgentForm
    success_url = reverse_lazy("host-list")
    template_name = "common/edit.html"

    def get_queryset(self):
        return models.Agent.objects.filter(token=self.kwargs.get("pk", ""), user=self.request.user)


@method_decorator(login_required, name="dispatch")
class HostDeleteView(DeleteView):
    model = models.Agent
    success_url = reverse_lazy("host-list")
    template_name = "common/delete.html"

    def get_queryset(self):
        return models.Agent.objects.filter(token=self.kwargs.get("pk", ""), user=self.request.user)


@method_decorator(login_required, name="dispatch")
class HostListView(ListView):
    model = models.Agent
    paginate_by = 5
    template_name = "host/list.html"

    def get_paginate_by(self, queryset):
        return self.kwargs.get("show") or self.request.GET.get("show") or self.paginate_by

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


@method_decorator(login_required, name="dispatch")
class HostDetailView(DetailView):
    model = models.Agent
    template_name = "host/detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(models.Agent, token=self.kwargs.get("pk", ""), user=self.request.user)

    def get_context_data(self, **kwargs):  # sourcery skip: extract-method
        context = super().get_context_data(**kwargs)
        metrics = models.Metric.objects.filter(agent=self.kwargs.get("pk", ""), agent__user=self.request.user)

        if not metrics:
            context["last"] = None
            context["lastDisk"] = None
            context["chartData"] = None
            context["software"] = None
            context["hardware"] = None
            context["disk"] = None
            context["ip"] = None
            return context

        lastMetric = vars(metrics.last())
        metrics = metrics.annotate(date=TruncMinute("created"))

        try:
            lastMetric, metricsRangeDate = self._rangeDate(self.request, metrics)
            metrics = list(metricsRangeDate)
            lastMetric["metrics"]["uptime"] = lastMetric.get("metrics", {}).get("uptime", "")[:-7]
            context["last"] = lastMetric
            context["lastDisk"] = self._lastDisk(lastMetric)
            context["chartData"] = self._chartData(metrics)
        except Exception:
            context["last"] = None
            context["lastDisk"] = None
            context["chartData"] = None

        # Get the latest metric
        with contextlib.suppress(TypeError):
            self._software_data(context, lastMetric)

            self._hardware_data(context, lastMetric)

            self._disk_partitions(context, lastMetric)

            self._network_adapters(context, lastMetric)

        return context

    def _software_data(self, context, lastMetric):
        software = {
            # Software
            "Hostname": lastMetric.get("metrics", {}).get("host", ""),
            "OS": lastMetric.get("metrics", {}).get("os", ""),
            "OS Version": lastMetric.get("metrics", {}).get("os_version", ""),
        }
        context["software"] = software

    def _hardware_data(self, context, lastMetric):
        hardware = {
            # Hardware
            "Architecture": lastMetric.get("metrics", {}).get("architecture", ""),
            "CPU Physical cores": lastMetric.get("metrics", {}).get("cpu_core_physical", ""),
            "CPU Total cores": lastMetric.get("metrics", {}).get("cpu_core_total", ""),
            "CPU Maximum frequency": str(lastMetric.get("metrics", {}).get("cpu_freq", {}).get("max", "")) + " MHz",
            "CPU Minimum frequency": str(lastMetric.get("metrics", {}).get("cpu_freq", {}).get("min", "")) + " MHz",
            "RAM": format_bytes(lastMetric.get("metrics", {}).get("ram", {}).get("total", "")),
        }
        context["hardware"] = hardware

    def _disk_partitions(self, context, lastMetric):
        partitions = {
            partition: {
                "Used": format_bytes(values.get("used", "")),
                "Total": format_bytes(values.get("total", "")),
                "Mount Point": values.get("mountpoint", ""),
                "File System Type": values.get("fstype", ""),
            }
            for partition, values in lastMetric.get("metrics", {}).get("disk", "").items()
        }
        context["disk"] = partitions

    def _network_adapters(self, context, lastMetric):
        nic_adapters = {}
        for adapter, values in lastMetric.get("metrics", {}).get("ip", "").items():
            ip = ""
            mac = ""
            netmask = ""
            for address, values2 in values.items():
                if values2["family"] == 2:
                    ip = address
                    netmask = values2["netmask"]
                elif values2["family"] == 17:
                    mac = address
            nic_adapters[adapter] = {
                "IP Address": ip,
                "MAC Address": mac,
                "Network Mask": netmask,
            }
        context["ip"] = nic_adapters

    def _rangeDate(self, request, metrics):
        lastMetric = vars(metrics.last())
        startDate = request.GET.get("start")
        endDate = request.GET.get("end")
        if startDate and endDate:
            date_from = datetime.strptime(startDate, "%Y-%m-%d")
            date_to = datetime.strptime(endDate, "%Y-%m-%d")
        else:
            date_to = lastMetric.get("created", "")
            date_from = date_to - timedelta(hours=1)
        return lastMetric, metrics.filter(created__range=(date_from, date_to))

    def _lastDisk(self, lastMetric):
        free = 0.0
        used = 0.0
        total = 0.0
        diskData = lastMetric.get("metrics", {}).get("disk", "")
        for partition in diskData.keys():
            free = free + diskData.get(partition, {}).get("free", "")
            used = used + diskData.get(partition, {}).get("used", "")
            total = total + diskData.get(partition, {}).get("total", "")
        return {
            "free": free,
            "free_formatted": format_bytes(free),
            "used": used,
            "used_formatted": format_bytes(used),
            "total": total,
            "total_formatted": format_bytes(total),
        }

    def _chartData(self, metrics):
        chartData = []
        for index, i in enumerate(metrics):
            chartData.append(
                {
                    "date": vars(i).get("date", ""),
                    "cpu": vars(i).get("metrics", {}).get("cpu_percent", ""),
                    "ram": vars(i).get("metrics", {}).get("ram", {}).get("percent", ""),
                }
            )
            with contextlib.suppress(TypeError):
                battery_percent = vars(i).get("metrics", {}).get("battery", {}).get("percent", "")
                chartData[index]["battery"] = round(battery_percent, 2)
        return json.dumps(list(chartData), cls=DjangoJSONEncoder)


######################################################################################################################


@method_decorator(login_required, name="dispatch")
class HostExecuteFormView(FormView):
    form_class = forms.ExecuteForm
    template_name = "host/execute.html"

    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Metric` to the template context,
        now you can use {{ metric }} within the template
        """
        context = super().get_context_data(**kwargs)
        context["host"] = get_object_or_404(models.Agent, pk=self.kwargs.get("pk", ""), user=self.request.user)
        return context

    def form_valid(self, form, **kwargs):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        host = get_object_or_404(models.Agent, pk=self.kwargs.get("pk", ""), user=self.request.user)
        response = form.execute_command(host.ip, host.port)
        # response = json.dumps(response, cls=DjangoJSONEncoder)
        # url = f"{self.request.path}#response"
        context = super().get_context_data(**kwargs)
        context["command"] = response
        context["host"] = host
        return self.render_to_response(context)


######################################################################################################################


@method_decorator(login_required, name="dispatch")
class HostConfigUpdateView(UpdateView):
    model = models.AgentConfig
    form_class = forms.AgentConfigForm
    template_name = "common/edit.html"

    def get_object(self):
        # Needed as Agent's PK was passed instead of Config's PK
        agent = models.Agent.objects.get(token=self.kwargs.get("pk", ""), user=self.request.user)
        return models.AgentConfig.objects.get(agent=agent)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.agent = models.Agent.objects.get(token=self.kwargs.get("pk", ""), user=self.request.user)
        form.save()
        # Definition of SuccessURL from source code
        # This way it lets me pass args from the actual URL to reverse_lazy
        url = reverse_lazy("config-detail", kwargs={"pk": self.kwargs.get("pk", "")})
        return HttpResponseRedirect(url)


@login_required
def config_detail(request, pk):
    HTML_FILE = "config/detail.html"
    host = get_object_or_404(models.Agent, token=pk, user=request.user)
    config_object = get_object_or_404(models.AgentConfig, agent=host)
    config_dict = vars(config_object)
    config_dict.pop("_state")

    alerts = {"url": settings.ALERT_ENDPOINT}

    auth = {
        "agent_token": host.token,
        "name": host.name,
        "user_token": Token.objects.get(user=request.user).key,
    }

    endpoints = {
        "agent_endpoint": settings.AGENT_ENDPOINT,
        "metric_endpoint": settings.METRIC_ENDPOINT,
    }

    logging = {
        "filename": config_dict.get("logging_filename", ""),
        "level": config_dict.get("logging_level", ""),
    }

    metrics = {
        "enable_logfile": config_dict.get("metrics_enable_logfile", ""),
        "get_endpoint": config_dict.get("metrics_get_endpoint", ""),
        "log_filename": config_dict.get("metrics_log_filename", ""),
        "post_interval": config_dict.get("metrics_post_interval", ""),
    }

    thresholds = {
        "cpu_percent": config_dict.get("threshold_cpu_percent", ""),
        "ram_percent": config_dict.get("threshold_ram_percent", ""),
    }

    uvicorn = {
        "backlog": config_dict.get("uvicorn_backlog", ""),
        "debug": config_dict.get("uvicorn_debug", ""),
        "host": config_dict.get("uvicorn_host", ""),
        "log_level": config_dict.get("uvicorn_log_level", ""),
        "port": config_dict.get("uvicorn_port", ""),
        "reload": config_dict.get("uvicorn_reload", ""),
        "timeout_keep_alive": config_dict.get("uvicorn_timeout_keep_alive", ""),
        "workers": config_dict.get("uvicorn_workers", ""),
    }

    data = {
        "alerts": alerts,
        "auth": auth,
        "endpoints": endpoints,
        "logging": logging,
        "metrics": metrics,
        "thresholds": thresholds,
        "uvicorn": uvicorn,
    }
    data = json.dumps(data, indent=4, sort_keys=True)
    form = forms.AgentConfigForm(request.POST or None, instance=config_object)
    context = {"form": form, "data": data, "host": host}
    return render(request, HTML_FILE, context)


######################################################################################################################


@method_decorator(login_required, name="dispatch")
class MetricListView(ListView):
    model = models.Metric
    paginate_by = 5
    template_name = "metric/list.html"

    def setup(self, request, *args, **kwargs) -> None:
        request.GET.get("page")
        request.META["QUERY_STRING"] = re.sub("(&|\?)page=(.)*", "", request.META.get("QUERY_STRING", ""))
        return super().setup(request, *args, **kwargs)

    def get_paginate_by(self, queryset):
        return self.kwargs.get("show") or self.request.GET.get("show") or self.paginate_by

    def get_queryset(self):
        host = get_object_or_404(models.Agent, token=self.kwargs.get("pk", ""), user=self.request.user)
        metrics = models.Metric.objects.filter(agent=host, agent__user=self.request.user).order_by("-created")

        startDate = self.request.GET.get("start")
        endDate = self.request.GET.get("end")
        if startDate and endDate:
            return metrics
        if startDate:
            endDate = startDate
        elif endDate:
            startDate = endDate
        return self._getMetricsByDate(startDate, endDate, metrics)

    def _getMetricsByDate(self, startDate, endDate, metrics):
        date_from = datetime.strptime(startDate, "%Y-%m-%d")
        date_to = datetime.strptime(endDate, "%Y-%m-%d")
        if startDate == endDate:
            return metrics.filter(created__date=date_from)
        else:
            return metrics.filter(created__range=(date_from, date_to))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["host"] = get_object_or_404(models.Agent, token=self.kwargs.get("pk", ""), user=self.request.user)
        return context


@method_decorator(login_required, name="dispatch")
class MetricDetailView(DetailView):
    model = models.Metric
    template_name = "metric/detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(
            models.Metric,
            agent=self.kwargs.get("pk", ""),
            agent__user=self.request.user,
            pk=self.kwargs.get("pk1", ""),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.object.status
        context["metrics"] = self.object.metrics
        return context


@method_decorator(login_required, name="dispatch")
class MetricDeleteView(DeleteView):
    model = models.Metric
    success_url = reverse_lazy("host-detail")
    template_name = "common/delete.html"

    def get_object(self):
        return get_object_or_404(models.Metric, pk=self.kwargs.get("pk1", ""), agent__user=self.request.user)

    def form_valid(self, form):
        # Definition of form_valid from source code (BaseDeleteView)
        # This way it lets me pass args from the actual URL to reverse_lazy
        url = reverse_lazy("metric-list", kwargs={"pk": self.kwargs.get("pk", "")})
        self.object.delete()
        return HttpResponseRedirect(url)


######################################################################################################################


@method_decorator(login_required, name="dispatch")
class AlertListView(ListView):
    model = models.Alert
    paginate_by = 5
    template_name = "alert/list.html"

    def get_paginate_by(self, queryset):
        return self.kwargs.get("show") or self.request.GET.get("show") or self.paginate_by

    def get_queryset(self):
        host = get_object_or_404(models.Agent, token=self.kwargs.get("pk", ""), user=self.request.user)
        alerts = models.Alert.objects.filter(agent=host, agent__user=self.request.user).order_by("-created")

        startDate = self.request.GET.get("start")
        endDate = self.request.GET.get("end")
        if startDate and endDate:
            return alerts
        if startDate:
            endDate = startDate
        elif endDate:
            startDate = endDate
        return self._getAlertsByDate(startDate, endDate, alerts)

    def _getAlertsByDate(self, startDate, endDate, alerts):
        date_from = datetime.strptime(startDate, "%Y-%m-%d")
        date_to = datetime.strptime(endDate, "%Y-%m-%d")
        if startDate == endDate:
            return alerts.filter(created__date=date_from)
        else:
            return alerts.filter(created__range=(date_from, date_to))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        startDate = self.request.GET.get("start")
        endDate = self.request.GET.get("end")

        date_from, date_to = self._getAlertsByDateOrOneDay(startDate, endDate)

        queryset = (
            models.Alert.objects.filter(
                created__gt=date_from,
                created__lt=date_to,
                agent__user=self.request.user,
            )
            .values("created")
            .order_by("created")
            .annotate(created_count=Count("created"))
        )
        data = list(queryset.values_list("created_count", flat=True))
        labels = list(queryset.values_list("created", flat=True))

        context["data"] = json.dumps(data, cls=DjangoJSONEncoder)
        context["labels"] = json.dumps(labels, cls=DjangoJSONEncoder)
        return context

    def _getAlertsByDateOrOneDay(self, startDate, endDate):
        if startDate or endDate:
            if startDate and not endDate:
                endDate = startDate
            elif not startDate:
                startDate = endDate
            date_from = datetime.strptime(startDate, "%Y-%m-%d")
            date_to = datetime.strptime(endDate, "%Y-%m-%d")
        else:
            now = timezone.now()
            date_from = now + timedelta(hours=1)
            date_to = date_from + timedelta(days=1)

        date_from = date_from - timedelta(1)
        date_to = date_to + timedelta(1)
        return date_from, date_to


@method_decorator(login_required, name="dispatch")
class AlertDetailView(DetailView):
    model = models.Alert
    template_name = "alert/detail.html"

    def get_object(self, queryset=None):
        # Needed as we pass two PKs instead of one
        return get_object_or_404(
            models.Alert,
            agent=self.kwargs.get("pk", ""),
            agent__user=self.request.user,
            id=self.kwargs.get("pk1", ""),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processes = vars(context.get("object", "")).get("processes", "")
        context["processes"] = json.dumps(processes, indent=4, sort_keys=True)
        return context


@method_decorator(login_required, name="dispatch")
class AlertDeleteView(DeleteView):
    model = models.Alert
    success_url = reverse_lazy("home")
    template_name = "common/delete.html"

    def get_object(self):
        return get_object_or_404(models.Alert, pk=self.kwargs.get("pk1", ""), agent__user=self.request.user)


######################################################################################################################


@method_decorator(login_required, name="dispatch")
class NotificationListView(ListView):
    model = models.AlertEmail
    template_name = "notification/list.html"

    def get_queryset(self):
        return models.AlertEmail.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["webhook_list"] = models.AlertWebhook.objects.filter(user=self.request.user)
        return context


@method_decorator(login_required, name="dispatch")
class EmailCreateView(CreateView):
    model = models.AlertEmail
    form_class = forms.AlertEmailForm
    success_url = reverse_lazy("notification-list")
    template_name = "common/add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class EmailDeleteView(DeleteView):
    model = models.AlertEmail
    success_url = reverse_lazy("notification-list")
    template_name = "common/delete.html"


@method_decorator(login_required, name="dispatch")
class WebhookCreateView(CreateView):
    model = models.AlertWebhook
    form_class = forms.AlertWebhookForm
    success_url = reverse_lazy("notification-list")
    template_name = "common/add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class WebhookDeleteView(DeleteView):
    model = models.AlertWebhook
    success_url = reverse_lazy("notification-list")
    template_name = "common/delete.html"
