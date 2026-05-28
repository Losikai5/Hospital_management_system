from django.urls import path
from .views import (
    AppointmentCreateView,
    AppointmentListView,
    AppointmentDetailView,
    AppointmentCancelView,
    AppointmentCompleteView,
    AvailableSlotsView,
)

urlpatterns = [
    path('', AppointmentListView.as_view(), name='appointment-list'),
    path('book/', AppointmentCreateView.as_view(), name='appointment-book'),
    path('slots/', AvailableSlotsView.as_view(), name='available-slots'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('<int:pk>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    path('<int:pk>/complete/', AppointmentCompleteView.as_view(), name='appointment-complete'),
]