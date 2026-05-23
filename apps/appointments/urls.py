from django.urls import path
from .views import (
    AppointmentCreateView,
    AppointmentListView,
    AppointmentDetailView,
    AppointmentCancelView,
    AppointmentCompleteView,
)

urlpatterns = [
    # A patient POSTs here to book a new appointment
    path('', AppointmentListView.as_view(), name='appointment-list'),
    
    # A patient POSTs here to book a new appointment
    path('book/', AppointmentCreateView.as_view(), name='appointment-book'),
    
    # View a single appointment by its ID
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    
    # A patient or admin POSTs here to cancel an appointment
    path('<int:pk>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),
    
    # A doctor POSTs here to mark an appointment as completed
    path('<int:pk>/complete/', AppointmentCompleteView.as_view(), name='appointment-complete'),
]