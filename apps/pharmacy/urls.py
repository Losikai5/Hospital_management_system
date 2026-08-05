from django.urls import path

from .views import (
    MedicineCreateView,
    MedicineDetailView,
    MedicineListView,
    PatientPrescriptionListView,
    PrescriptionCancelView,
    PrescriptionCreateView,
    PrescriptionDispenseView,
    PrescriptionListView,
)


urlpatterns = [
    path("medicines/", MedicineListView.as_view(), name="medicine-list"),
    path("medicines/add/", MedicineCreateView.as_view(), name="medicine-create"),
    path(
        "medicines/<int:pk>/",
        MedicineDetailView.as_view(),
        name="medicine-update",
    ),
    path(
        "prescriptions/",
        PrescriptionListView.as_view(),
        name="prescription-list",
    ),
    path(
        "prescriptions/create/",
        PrescriptionCreateView.as_view(),
        name="prescription-create",
    ),
    path(
        "prescriptions/mine/",
        PatientPrescriptionListView.as_view(),
        name="prescription-mine",
    ),
    path(
        "prescriptions/<int:pk>/dispense/",
        PrescriptionDispenseView.as_view(),
        name="prescription-dispense",
    ),
    path(
        "prescriptions/<int:pk>/cancel/",
        PrescriptionCancelView.as_view(),
        name="prescription-cancel",
    ),
]
