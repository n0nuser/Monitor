from datetime import datetime, timedelta
from django import template
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncMinute
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import DeleteView, UpdateView, CreateView, FormView
from rest_framework.authtoken.models import Token
from web.tasks import send_email_task
from web.utils import format_bytes
import contextlib
import json

# pyright: reportMissingModuleSource=false
# pyright: reportMissingImports=false

from web.models import Agent, AgentConfig, AlertEmail, AlertWebhook, Metric, Alert, CustomUser
from web.forms import AgentConfigForm, AlertEmailForm, AlertWebhookForm, ExecuteForm, LoginForm, SignUpForm, AgentForm

# Create your views here.


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


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                messages.error(request=request, message="Invalid credentials")
        else:
            messages.error(request=request, message="Error validating the form")
    return render(request, "accounts/login.html", {"form": form})


def register_user(request):
    # sourcery skip: extract-method, inline-immediately-returned-variable
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
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
                    "message": "Congratulations on setting up your account! You now have access to all account features!",
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
        form = SignUpForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form, "success": success},
    )


class Profile(TemplateView):
    model = CustomUser
    template_name = "accounts/profile.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["token"] = Token.objects.get(user=self.request.user).key
        return context


def handler403(request, exception, template_name="errors/403.html"):
    return render(request, template_name, status=403)


def handler404(request, exception, template_name="errors/404.html"):
    return render(request, template_name, status=404)


def handler500(request, template_name="errors/500.html"):
    return render(request, template_name, status=500)


######################################################################################################################


class HostCreateView(CreateView):
    model = Agent
    form_class = AgentForm
    success_url = reverse_lazy("host-list")
    template_name = "common/add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class HostUpdateView(UpdateView):
    model = Agent
    form_class = AgentForm
    success_url = reverse_lazy("host-list")
    template_name = "common/edit.html"

    def get_queryset(self):
        return Agent.objects.filter(token=self.kwargs["pk"], user=self.request.user)


class HostDeleteView(DeleteView):
    model = Agent
    success_url = reverse_lazy("host-list")
    template_name = "common/delete.html"

    def get_queryset(self):
        return Agent.objects.filter(token=self.kwargs["pk"], user=self.request.user)


class HostListView(ListView):
    model = Agent
    paginate_by = 7
    template_name = "host/list.html"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class HostDetailView(DetailView):
    model = Agent
    template_name = "host/detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Agent, token=self.kwargs["pk"], user=self.request.user)

    def get_context_data(self, **kwargs):  # sourcery skip: extract-method
        context = super().get_context_data(**kwargs)
        metrics = Metric.objects.filter(agent=self.kwargs["pk"], agent__user=self.request.user)

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
            lastMetric["metrics"]["uptime"] = lastMetric["metrics"]["uptime"][:-7]
            context["last"] = lastMetric
            context["lastDisk"] = self._lastDisk(lastMetric)
            context["chartData"] = self._chartData(metrics)
        except Exception:
            context["last"] = None
            context["lastDisk"] = None
            context["chartData"] = None

        # Get the latest metric
        with contextlib.suppress(TypeError):
            software = {
                # Software
                "Hostname": lastMetric["metrics"]["host"],
                "OS": lastMetric["metrics"]["os"],
                "OS Version": lastMetric["metrics"]["os_version"],
            }
            context["software"] = software

            hardware = {
                # Hardware
                "Architecture": lastMetric["metrics"]["architecture"],
                "CPU Physical cores": lastMetric["metrics"]["cpu_core_physical"],
                "CPU Total cores": lastMetric["metrics"]["cpu_core_total"],
                "CPU Maximum frequency": str(lastMetric["metrics"]["cpu_freq"]["max"]) + " MHz",
                "CPU Minimum frequency": str(lastMetric["metrics"]["cpu_freq"]["min"]) + " MHz",
                "RAM": format_bytes(lastMetric["metrics"]["ram"]["total"]),
            }
            context["hardware"] = hardware

            partitions = {
                partition: {
                    "Used": format_bytes(values["used"]),
                    "Total": format_bytes(values["total"]),
                    "Mount Point": values["mountpoint"],
                    "File System Type": values["fstype"],
                }
                for partition, values in lastMetric["metrics"]["disk"].items()
            }

            context["disk"] = partitions

            nic_adapters = {}
            for adapter, values in lastMetric["metrics"]["ip"].items():
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

        return context

    def _rangeDate(self, request, metrics):
        lastMetric = vars(metrics.last())
        startDate = request.GET.get("start")
        endDate = request.GET.get("end")
        if startDate and endDate:
            date_from = datetime.strptime(startDate, "%Y-%m-%d")
            date_to = datetime.strptime(endDate, "%Y-%m-%d")
        else:
            date_to = lastMetric["created"]
            date_from = date_to - timedelta(hours=1)
        return lastMetric, metrics.filter(created__range=(date_from, date_to))

    def _lastDisk(self, lastMetric):
        free = 0.0
        used = 0.0
        total = 0.0
        diskData = lastMetric["metrics"]["disk"]
        for partition in diskData.keys():
            free = free + diskData[partition]["free"]
            used = used + diskData[partition]["used"]
            total = total + diskData[partition]["total"]
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
                    "date": vars(i)["date"],
                    "cpu": vars(i)["metrics"]["cpu_percent"],
                    "ram": vars(i)["metrics"]["ram"]["percent"],
                }
            )
            with contextlib.suppress(TypeError):
                battery_percent = vars(i)["metrics"]["battery"]["percent"]
                chartData[index]["battery"] = round(battery_percent, 2)
        return json.dumps(list(chartData), cls=DjangoJSONEncoder)


######################################################################################################################


class HostExecuteFormView(FormView):
    form_class = ExecuteForm
    template_name = "host/execute.html"

    def get_context_data(self, **kwargs):
        """
        This has been overridden to add `Metric` to the template context,
        now you can use {{ metric }} within the template
        """
        context = super().get_context_data(**kwargs)
        context["host"] = get_object_or_404(Agent, pk=self.kwargs["pk"], user=self.request.user)
        return context

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        host = get_object_or_404(Agent, pk=self.kwargs["pk"], user=self.request.user)
        response = form.execute_command(host.ip, host.port)
        response = json.dumps(response, cls=DjangoJSONEncoder)
        # url = reverse_lazy("host-execute", kwargs={"pk": self.kwargs["pk"]}) + "#response"
        url = f"{self.request.path}#response"
        messages.success(request=self.request, message=response)
        return HttpResponseRedirect(url)


######################################################################################################################


class HostConfigUpdateView(UpdateView):
    model = AgentConfig
    form_class = AgentConfigForm
    template_name = "common/edit.html"

    def get_object(self):
        # Needed as Agent's PK was passed instead of Config's PK
        agent = Agent.objects.get(token=self.kwargs["pk"], user=self.request.user)
        return AgentConfig.objects.get(agent=agent)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.agent = Agent.objects.get(token=self.kwargs["pk"], user=self.request.user)
        form.save()
        # Definition of SuccessURL from source code
        # This way it lets me pass args from the actual URL to reverse_lazy
        url = reverse_lazy("config-detail", kwargs={"pk": self.kwargs["pk"]})
        return HttpResponseRedirect(url)


def config_detail(request, pk):
    HTML_FILE = "config/detail.html"
    host = get_object_or_404(Agent, token=pk, user=request.user)
    config_object = get_object_or_404(AgentConfig, agent=host)
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
        "filename": config_dict["logging_filename"],
        "level": config_dict["logging_level"],
    }

    metrics = {
        "enable_logfile": config_dict["metrics_enable_logfile"],
        "get_endpoint": config_dict["metrics_get_endpoint"],
        "log_filename": config_dict["metrics_log_filename"],
        "post_interval": config_dict["metrics_post_interval"],
    }

    thresholds = {
        "cpu_percent": config_dict["threshold_cpu_percent"],
        "ram_percent": config_dict["threshold_ram_percent"],
    }

    uvicorn = {
        "backlog": config_dict["uvicorn_backlog"],
        "debug": config_dict["uvicorn_debug"],
        "host": config_dict["uvicorn_host"],
        "log_level": config_dict["uvicorn_log_level"],
        "port": config_dict["uvicorn_port"],
        "reload": config_dict["uvicorn_reload"],
        "timeout_keep_alive": config_dict["uvicorn_timeout_keep_alive"],
        "workers": config_dict["uvicorn_workers"],
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
    form = AgentConfigForm(request.POST or None, instance=config_object)
    context = {"form": form, "data": data, "host": host}
    return render(request, HTML_FILE, context)


######################################################################################################################


class MetricListView(ListView):
    model = Metric
    paginate_by = 7
    template_name = "metric/list.html"

    def get_queryset(self):
        host = get_object_or_404(Agent, token=self.kwargs["pk"], user=self.request.user)
        startDate = self.request.GET.get("start")
        endDate = self.request.GET.get("end")
        if startDate:
            if not endDate:
                endDate = startDate
            return self._getAlertsByDate(startDate, endDate, host)
        elif endDate:
            return self._getAlertsByDate(startDate, endDate, host)
        else:
            return Metric.objects.filter(agent__user=self.request.user).order_by("-created")

    def _getAlertsByDate(self, startDate, endDate, agent):
        date_from = datetime.strptime(startDate, "%Y-%m-%d")
        date_to = datetime.strptime(endDate, "%Y-%m-%d")
        return (
            Metric.objects.all()
            .filter(created__date=date_from, agent=agent, agent__user=self.request.user)
            .order_by("-created")
            if startDate == endDate
            else Alert.objects.filter(agent__user=self.request.user)
            .filter(
                created__range=(date_from, date_to),
                agent=agent,
                agent__user=self.request.user,
            )
            .order_by("-created")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["host"] = get_object_or_404(Agent, token=self.kwargs["pk"], user=self.request.user)
        return context


class MetricDetailView(DetailView):
    model = Metric
    template_name = "metric/detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Metric,
            agent=self.kwargs["pk"],
            agent__user=self.request.user,
            pk=self.kwargs["pk1"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = json.dumps(self.object.status, indent=4, sort_keys=True)
        context["metrics"] = json.dumps(self.object.metrics, indent=4, sort_keys=True)
        return context


class MetricDeleteView(DeleteView):
    model = Metric
    success_url = reverse_lazy("host-detail")
    template_name = "common/delete.html"

    def get_object(self):
        return get_object_or_404(Metric, pk=self.kwargs["pk1"], agent__user=self.request.user)

    def form_valid(self, form):
        # Definition of form_valid from source code (BaseDeleteView)
        # This way it lets me pass args from the actual URL to reverse_lazy
        url = reverse_lazy("metric-list", kwargs={"pk": self.kwargs["pk"]})
        self.object.delete()
        return HttpResponseRedirect(url)


######################################################################################################################


class AlertListView(ListView):
    model = Alert
    paginate_by = 7
    template_name = "alert/list.html"

    def get_queryset(self):
        startDate = self.request.GET.get("start")
        endDate = self.request.GET.get("end")
        if startDate:
            if not endDate:
                endDate = startDate
            return self._getAlertsByDate(startDate, endDate)
        elif endDate:
            return self._getAlertsByDate(startDate, endDate)
        else:
            return Alert.objects.filter(agent__user=self.request.user).order_by("-created")

    def _getAlertsByDate(self, startDate, endDate):
        date_from = datetime.strptime(startDate, "%Y-%m-%d")
        date_to = datetime.strptime(endDate, "%Y-%m-%d")
        return (
            Alert.objects.all().order_by("-created").filter(created__date=date_from, agent__user=self.request.user)
            if startDate == endDate
            else Alert.objects.filter(agent__user=self.request.user)
            .order_by("-created")
            .filter(created__range=(date_from, date_to), agent__user=self.request.user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        startDate = self.request.GET.get("start")
        endDate = self.request.GET.get("end")

        date_from, date_to = self._getAlertsByDateOrOneDay(startDate, endDate)

        queryset = (
            Alert.objects.filter(
                created__gt=date_from,
                created__lt=date_to,
                agent__user=self.request.user,
            )
            .order_by("created")
            .values("created")
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
            date_from = timezone.datetime(
                now.year,
                now.month,
                now.day,
                now.hour + 1,
                now.minute,
                now.second,
                tzinfo=timezone.get_current_timezone(),
            )
            date_to = date_from + timedelta(days=1)

        date_from = date_from - timedelta(1)
        date_to = date_to + timedelta(1)
        return date_from, date_to


class AlertDetailView(DetailView):
    model = Alert
    template_name = "alert/detail.html"

    def get_object(self, queryset=None):
        # Needed as we pass two PKs instead of one
        return get_object_or_404(
            Alert,
            agent=self.kwargs["pk"],
            agent__user=self.request.user,
            id=self.kwargs["pk1"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["processes"] = json.dumps(context["object"].__dict__["processes"], indent=4, sort_keys=True)
        # context["object"]["processes"] = json.dumps(context["object"]["processes"], cls=DjangoJSONEncoder)
        return context


class AlertDeleteView(DeleteView):
    model = Alert
    success_url = reverse_lazy("home")
    template_name = "common/delete.html"

    def get_object(self):
        return get_object_or_404(Alert, pk=self.kwargs["pk1"], agent__user=self.request.user)


######################################################################################################################


class NotificationListView(ListView):
    model = AlertEmail
    template_name = "notification/list.html"

    def get_queryset(self):
        return AlertEmail.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["webhook_list"] = AlertWebhook.objects.filter(user=self.request.user)
        return context


class EmailCreateView(CreateView):
    model = AlertEmail
    form_class = AlertEmailForm
    success_url = reverse_lazy("notification-list")
    template_name = "common/add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class EmailDeleteView(DeleteView):
    model = AlertEmail
    success_url = reverse_lazy("notification-list")
    template_name = "common/delete.html"


class WebhookCreateView(CreateView):
    model = AlertWebhook
    form_class = AlertWebhookForm
    success_url = reverse_lazy("notification-list")
    template_name = "common/add.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class WebhookDeleteView(DeleteView):
    model = AlertWebhook
    success_url = reverse_lazy("notification-list")
    template_name = "common/delete.html"
