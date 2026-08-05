from django.urls import path

from .views import AuditLogDetailView, AuditLogListView


urlpatterns = [
    path("logs/", AuditLogListView.as_view(), name="audit-log-list"),
    path("logs/<int:pk>/", AuditLogDetailView.as_view(), name="audit-log-detail"),
]

