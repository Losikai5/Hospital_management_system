from django.urls import path
from .views import (
    MedicineListView,
    MedicineCreateView,
    MedicineUpdateView,
    PrescriptionCreateView,
    PrescriptionListView,
    PatientPrescriptionListView,
    PrescriptionDispenseView,
)

urlpatterns = [
    # Medicine endpoints
    path('medicines/', MedicineListView.as_view(), name='medicine-list'),
    path('medicines/add/', MedicineCreateView.as_view(), name='medicine-create'),
    path('medicines/<int:pk>/', MedicineUpdateView.as_view(), name='medicine-update'),

    # Prescription endpoints
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/create/', PrescriptionCreateView.as_view(), name='prescription-create'),
    path('prescriptions/mine/', PatientPrescriptionListView.as_view(), name='prescription-mine'),
    path('prescriptions/<int:pk>/dispense/', PrescriptionDispenseView.as_view(), name='prescription-dispense'),
]