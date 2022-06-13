from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import path
from django.urls import reverse_lazy

from web.tasks import startup_scheduling
from web import views

urlpatterns = [
    path("", views.AlertListView.as_view(), name="home"),
    path("accounts/login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("accounts/register/", views.register_user, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/profile/", views.Profile.as_view(), name="profile"),
    path("accounts/update_profile/<pk>", views.UpdateProfile.as_view(), name="update-profile"),
    path("password-reset/", views.ResetPasswordView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("password-reset-complete/", views.PasswordResetCompleteView.as_view(), name="password-reset-complete"),
    path(
        "change-password/",
        login_required(
            PasswordChangeView.as_view(
                template_name="accounts/change_password.html", success_url=reverse_lazy("profile")
            )
        ),
        name="change-password",
    ),
    path(
        "host/<pk>/alert/<pk1>/",
        views.AlertDetailView.as_view(),
        name="alert-detail",
    ),
    path(
        "host/<pk>/alert/<pk1>/delete/",
        views.AlertDeleteView.as_view(),
        name="alert-delete",
    ),
    path("host/", views.HostListView.as_view(), name="host-list"),
    path("host/add/", views.HostCreateView.as_view(), name="host-add"),
    path("host/<pk>/", views.HostDetailView.as_view(), name="host-detail"),
    path(
        "host/<pk>/delete/",
        views.HostDeleteView.as_view(),
        name="host-delete",
    ),
    path(
        "host/<pk>/edit/",
        views.HostUpdateView.as_view(),
        name="host-edit",
    ),
    path(
        "host/<pk>/execute/",
        views.HostExecuteFormView.as_view(),
        name="host-execute",
    ),
    path(
        "host/<pk>/config/edit/",
        views.HostConfigUpdateView.as_view(),
        name="config-edit",
    ),
    path(
        "host/<pk>/config/",
        views.config_detail,
        name="config-detail",
    ),
    path(
        "host/<pk>/metric/",
        views.MetricListView.as_view(),
        name="metric-list",
    ),
    path(
        "host/<pk>/metric/<pk1>/",
        views.MetricDetailView.as_view(),
        name="metric-detail",
    ),
    path(
        "host/<pk>/metric/<pk1>/delete/",
        views.MetricDeleteView.as_view(),
        name="metric-delete",
    ),
    path("notification/", views.NotificationListView.as_view(), name="notification-list"),
    path("email/add/", views.EmailCreateView.as_view(), name="email-add"),
    path(
        "email/<pk>/delete/",
        views.EmailDeleteView.as_view(),
        name="email-delete",
    ),
    path("webhook/add/", views.WebhookCreateView.as_view(), name="webhook-add"),
    path(
        "webhook/<pk>/delete/",
        views.WebhookDeleteView.as_view(),
        name="webhook-delete",
    ),
]

# https://www.pythonfixing.com/2022/01/fixed-execute-code-when-django-starts.html
# startup_scheduling()
