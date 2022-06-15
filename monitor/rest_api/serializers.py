from web.models import Agent, Metric, Alert, CustomUser, AlertEmail, AlertWebhook, AgentConfig
from rest_framework import serializers


class CustomUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"


class AgentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agent
        fields = "__all__"


class AgentConfigSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AgentConfig
        fields = "__all__"


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Metric
        fields = ["url", "agent", "created", "status", "metrics"]


class AlertSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Alert
        fields = "__all__"


class AlertEmailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AlertEmail
        fields = "__all__"


class AlertWebhookSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AlertWebhook
        fields = "__all__"
