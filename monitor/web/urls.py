from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import login_required
from web import views

# pyright: reportMissingModuleSource=false
# pyright: reportMissingImports=false

urlpatterns = [
    path("", login_required(views.AlertListView.as_view()), name="alert-list"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/register/", views.register_user, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/profile/", login_required(views.Profile.as_view()), name="profile"),
    path(
        "host/<pk>/alert/<pk1>/",
        login_required(views.AlertDetailView.as_view()),
        name="alert-detail",
    ),
    path(
        "host/<pk>/alert/<pk1>/delete/",
        login_required(views.AlertDeleteView.as_view()),
        name="alert-delete",
    ),
    path("host/", login_required(views.HostListView.as_view()), name="host-list"),
    path("host/add/", login_required(views.HostCreateView.as_view()), name="host-add"),
    path(
        "host/<pk>/", login_required(views.HostDetailView.as_view()), name="host-detail"
    ),
    path(
        "host/<pk>/delete/",
        login_required(views.HostDeleteView.as_view()),
        name="host-delete",
    ),
    path(
        "host/<pk>/edit/",
        login_required(views.HostUpdateView.as_view()),
        name="host-edit",
    ),
    path(
        "host/<pk>/execute/",
        login_required(views.HostExecuteFormView.as_view()),
        name="host-execute",
    ),
    path(
        "host/<pk>/config/edit/",
        login_required(views.HostConfigUpdateView.as_view()),
        name="config-edit",
    ),
    path(
        "host/<pk>/config/",
        login_required(views.config_detail),
        name="config-detail",
    ),
    path(
        "host/<pk>/info/",
        login_required(views.HostInfoDetailView.as_view()),
        name="host-info",
    ),
    path(
        "host/<pk>/metric/",
        login_required(views.MetricListView.as_view()),
        name="metric-list",
    ),
    path(
        "host/<pk>/metric/<pk1>/",
        login_required(views.MetricDetailView.as_view()),
        name="metric-detail",
    ),
    path(
        "host/<pk>/metric/<pk1>/delete/",
        login_required(views.MetricDeleteView.as_view()),
        name="metric-delete",
    ),
]
