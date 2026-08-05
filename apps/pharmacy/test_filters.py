from datetime import date, time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment, AppointmentStatus
from apps.doctors.models import DoctorProfile
from apps.medical_records.models import MedicalRecord
from apps.patients.models import PatientProfile
from apps.users.models import CustomUser, Permission, Role, RolePermission

from .models import Medicine, Prescription, PrescriptionStatus, UnitType


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(role=role, permission=permission)
    return role


class PharmacyFilterTests(APITestCase):
    def setUp(self):
        viewer_role = create_role(
            "PHARMACY_VIEWER",
            [
                "can_view_medicines",
                "can_view_all_medicines",
                "can_view_prescriptions",
                "can_view_all_prescriptions",
            ],
        )
        doctor_role = create_role("DOCTOR", [])
        patient_role = create_role("PATIENT", [])
        self.viewer = CustomUser.objects.create_user(
            email="viewer@example.com",
            password="SafePassword!123",
            role=viewer_role,
        )
        doctor_user = CustomUser.objects.create_user(
            email="doctor@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        patient_user = CustomUser.objects.create_user(
            email="filter-patient@example.com",
            password="SafePassword!123",
            role=patient_role,
        )
        doctor = DoctorProfile.objects.create(
            user=doctor_user,
            license_number="FILTER-PHARM-LIC",
        )
        patient = PatientProfile.objects.create(user=patient_user)
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            appointment_date=date(2026, 8, 20),
            appointment_time=time(8, 0),
            status=AppointmentStatus.COMPLETED,
        )
        record = MedicalRecord.objects.create(
            appointment=appointment,
            diagnosis="Diagnosis",
        )
        self.low_medicine = Medicine.objects.create(
            name="Low Tablets",
            stock_quantity=2,
            low_stock_threshold=5,
            unit_type=UnitType.TABLET,
        )
        other_medicine = Medicine.objects.create(
            name="Full Capsules",
            stock_quantity=30,
            low_stock_threshold=5,
            unit_type=UnitType.CAPSULE,
        )
        self.pending_prescription = Prescription.objects.create(
            medical_record=record,
            medicine=self.low_medicine,
            dosage="One",
            frequency="Daily",
            duration="Two days",
            quantity_prescribed=2,
            status=PrescriptionStatus.PENDING,
        )
        Prescription.objects.create(
            medical_record=record,
            medicine=other_medicine,
            dosage="One",
            frequency="Daily",
            duration="Two days",
            quantity_prescribed=2,
            status=PrescriptionStatus.DISPENSED,
        )

    def test_medicine_computed_low_stock_filter(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(
            reverse("medicine-list"),
            {
                "low_stock": "true",
                "unit_type": "tablet",
                "search": "low",
                "ordering": "-stock_quantity",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [medicine["id"] for medicine in response.data],
            [self.low_medicine.pk],
        )

    def test_prescription_status_and_search_filters(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(
            reverse("prescription-list"),
            {
                "status": "pending",
                "search": "filter-patient",
                "ordering": "quantity_prescribed",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [prescription["id"] for prescription in response.data],
            [self.pending_prescription.pk],
        )

