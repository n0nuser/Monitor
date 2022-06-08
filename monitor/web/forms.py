import requests
from django import forms
from web.models import AlertEmail, AlertWebhook, CustomUser, Agent, AgentConfig
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2")


class CustomUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = CustomUser
        fields = ("username", "email")


class ExecuteForm(forms.Form):
    command = forms.CharField(widget=forms.Textarea)
    timeout_for_request = forms.IntegerField(min_value=1)
    timeout_for_command = forms.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["command"].widget.attrs.update({"class": "form-control"})
        self.fields["timeout_for_request"].widget.attrs.update({"class": "form-control"})
        self.fields["timeout_for_command"].widget.attrs.update({"class": "form-control"})

    def execute_command(self, host, port):
        # send email using the self.cleaned_data dictionary
        command = self.cleaned_data["command"]
        timeout_for_request = self.cleaned_data["timeout_for_request"]
        timeout_for_command = self.cleaned_data["timeout_for_command"]
        json_data = {"command": command, "timeout": timeout_for_command}
        url = f"http://{host}:{port}/command/?command={command}&timeout={timeout_for_command}"
        try:
            response = requests.post(url, json=json_data, timeout=timeout_for_request)
            return response.json()
        except requests.exceptions.ReadTimeout:
            response = {
                "status": "error",
                "stderr": "Request timeout. Please try to increase 'Timeout for request'.",
            }
            return response
        except requests.exceptions.ConnectionError:
            response = {
                "status": "error",
                "stderr": f"Connection error. Could not connect to the agent: #Check if agent is running succesfully. #Check IP ({host}) and Port ({port}) configuration. #Check port forwarding in agent's router if the agent is outside your network.",
            }
            return response


class AgentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control"})
        self.fields["ip"].widget.attrs.update({"class": "form-control"})
        self.fields["port"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Agent
        fields = ("name", "ip", "port")
        labels = {
            "name": "Host Name",
            "ip": "IP Address",
            "port": "Port",
        }


class AgentConfigForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["logging_filename"].widget.attrs.update({"class": "form-control"})
        self.fields["logging_level"].widget.attrs.update({"class": "form-control"})
        self.fields["metrics_log_filename"].widget.attrs.update({"class": "form-control"})
        self.fields["metrics_post_interval"].widget.attrs.update({"class": "form-control"})
        self.fields["threshold_cpu_percent"].widget.attrs.update({"class": "form-control"})
        self.fields["threshold_ram_percent"].widget.attrs.update({"class": "form-control"})
        self.fields["uvicorn_backlog"].widget.attrs.update({"class": "form-control"})
        self.fields["uvicorn_host"].widget.attrs.update({"class": "form-control"})
        self.fields["uvicorn_log_level"].widget.attrs.update({"class": "form-control"})
        self.fields["uvicorn_port"].widget.attrs.update({"class": "form-control"})
        self.fields["uvicorn_timeout_keep_alive"].widget.attrs.update({"class": "form-control"})
        self.fields["uvicorn_workers"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = AgentConfig
        exclude = ("agent",)
        labels = {
            "logging_filename": "Filename of the log file",
            "logging_level": "Logging level",
            "metrics_enable_logfile": "Enable metrics log file",
            "metrics_get_endpoint": "Enable metrics endpoint",
            "metrics_log_filename": "Filename of the metrics log file",
            "metrics_post_interval": "Interval in seconds to send metrics",
            "threshold_cpu_percent": "Percentage of CPU usage to trigger alert",
            "threshold_ram_percent": "Percentage of RAM usage to trigger alert",
            "warning_time_interval": "Time interval in minutes for Warning status in which alerts are accumulated, or metrics aren't received",
            "bad_time_interval": "Time interval in minutes for Bad status in which alerts are accumulated, or metrics aren't received",
            "uvicorn_debug": "Enable debug mode",
            "uvicorn_reload": "Enable reloading of the uvicorn server",
            "uvicorn_backlog": "Backlog of the uvicorn server",
            "uvicorn_host": "IP address of the uvicorn server",
            "uvicorn_port": "Port of the uvicorn server",
            "uvicorn_log_level": "Logging level of the uvicorn server",
            "uvicorn_timeout_keep_alive": "Timeout of the uvicorn server",
            "uvicorn_workers": "Workers of the uvicorn server",
        }


class AlertEmailForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = AlertEmail
        fields = ("name", "email")


class AlertWebhookForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "form-control"})
        self.fields["webhook"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = AlertWebhook
        fields = ("name", "webhook")
