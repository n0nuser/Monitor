from web.models import Agent, Metric, Alert, CustomUser, AlertEmail, AlertWebhook, AgentConfig
from rest_framework import permissions, viewsets
from rest_framework.response import Response
import rest_api.serializers as serializer


def list(self, request, *args, **kwargs):
    queryset = self.filter_queryset(self.get_queryset().filter(user=request.user))

    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = self.get_serializer(queryset, many=True)
    return Response(serializer.data)


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = CustomUser.objects.all()
    serializer_class = serializer.CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]


CustomUserViewSet.list = list


class AgentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows agents to be viewed or edited.
    """

    queryset = Agent.objects.all()
    serializer_class = serializer.AgentSerializer
    permission_classes = [permissions.IsAuthenticated]


AgentViewSet.list = list


class AgentConfigViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows agents config to be viewed or edited.
    """

    queryset = AgentConfig.objects.all()
    serializer_class = serializer.AgentConfigSerializer
    permission_classes = [permissions.IsAuthenticated]


AgentConfigViewSet.list = list


class MetricViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows metrics to be viewed or edited.
    """

    queryset = Metric.objects.all()
    serializer_class = serializer.MetricSerializer
    permission_classes = [permissions.IsAuthenticated]


MetricViewSet.list = list


class AlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows alerts to be viewed or edited.
    """

    queryset = Alert.objects.all()
    serializer_class = serializer.AlertSerializer
    permission_classes = [permissions.IsAuthenticated]


AlertViewSet.list = list


class AlertEmailViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows alert emails to be viewed or edited.
    """

    queryset = AlertEmail.objects.all()
    serializer_class = serializer.AlertEmailSerializer
    permission_classes = [permissions.IsAuthenticated]


AlertEmailViewSet.list = list


class AlertWebhookViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows alert webhooks to be viewed or edited.
    """

    queryset = AlertWebhook.objects.all()
    serializer_class = serializer.AlertWebhookSerializer
    permission_classes = [permissions.IsAuthenticated]


AlertWebhookViewSet.list = list
