from django.urls import path
from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.TicketListView.as_view(), name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("export/", views.ticket_export_excel, name="export"),
    path("stats/", views.StatsView.as_view(), name="stats"),
    path("ticket/new/", views.TicketCreateView.as_view(), name="create"),
    path("ticket/<int:pk>/", views.TicketDetailView.as_view(), name="detail"),
    path("ticket/<int:pk>/edit/", views.TicketUpdateView.as_view(), name="edit"),
    path("ticket/<int:pk>/quick-update/", views.ticket_quick_update, name="quick_update"),
    path("ticket/<int:pk>/comment/", views.ticket_add_comment, name="add_comment"),
    path("api/client/<int:client_id>/members/", views.api_client_members, name="api_client_members"),
    path("webhook/inbound-email/", views.webhook_inbound_email, name="webhook_inbound_email"),
]
