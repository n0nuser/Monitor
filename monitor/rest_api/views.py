from web.models import Agent, Metric, Alert
from rest_framework import permissions, viewsets

from rest_api.serializers import AgentSerializer, MetricSerializer, AlertSerializer


class AgentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows agents to be viewed or edited.
    """

    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAuthenticated]


class MetricViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows metrics to be viewed or edited.
    """

    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    permission_classes = [permissions.IsAuthenticated]


class AlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows alerts to be viewed or edited.
    """

    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
