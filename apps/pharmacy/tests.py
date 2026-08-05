from datetime import date, time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment, AppointmentStatus
from apps.doctors.models import DoctorProfile
from apps.medical_records.models import MedicalRecord
from apps.patients.models import PatientProfile
from apps.users.models import (
    CustomUser,
    Permission,
    Role,
    RolePermission,
)

from .models import Medicine, Prescription, PrescriptionStatus


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(
            role=role,
            permission=permission,
        )
    return role


class PharmacyApiTests(APITestCase):
    def setUp(self):
        self.doctor_role = create_role(
            "DOCTOR",
            ["can_cancel_prescriptions"],
        )
        self.patient_role = create_role(
            "PATIENT",
            ["can_view_medicines"],
        )
        self.pharmacist_role = create_role(
            "PHARMACIST",
            [
                "can_view_medicines",
                "can_view_all_medicines",
                "can_edit_medicines",
                "can_dispense_prescriptions",
            ],
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doctor@example.com",
            password="SafePassword!123",
            role=self.doctor_role,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            license_number="PHARM-LIC-1",
        )
        self.other_doctor_user = CustomUser.objects.create_user(
            email="other-doctor@example.com",
            password="SafePassword!123",
            role=self.doctor_role,
        )
        self.other_doctor = DoctorProfile.objects.create(
            user=self.other_doctor_user,
            license_number="PHARM-LIC-2",
        )
        self.patient_user = CustomUser.objects.create_user(
            email="patient@example.com",
            password="SafePassword!123",
            role=self.patient_role,
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.pharmacist_user = CustomUser.objects.create_user(
            email="pharmacist@example.com",
            password="SafePassword!123",
            role=self.pharmacist_role,
        )
        self.prescription_manager_role = create_role(
            "PRESCRIPTION_MANAGER",
            [
                "can_cancel_prescriptions",
                "can_view_all_prescriptions",
            ],
        )
        self.prescription_manager_user = CustomUser.objects.create_user(
            email="prescription-manager@example.com",
            password="SafePassword!123",
            role=self.prescription_manager_role,
        )
        self.appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date(2026, 8, 10),
            appointment_time=time(8, 0),
            status=AppointmentStatus.COMPLETED,
        )
        self.record = MedicalRecord.objects.create(
            appointment=self.appointment,
            diagnosis="Test diagnosis",
        )
        self.medicine = Medicine.objects.create(
            name="Test Medicine",
            stock_quantity=20,
            unit_cost="10.00",
        )

    def create_prescription(self, **overrides):
        values = {
            "medical_record": self.record,
            "medicine": self.medicine,
            "dosage": "One tablet",
            "frequency": "Daily",
            "duration": "Five days",
            "quantity_prescribed": 5,
        }
        values.update(overrides)
        return Prescription.objects.create(**values)

    def test_medicine_detail_follows_list_visibility_and_supports_patch(self):
        inactive = Medicine.objects.create(
            name="Inactive Medicine",
            stock_quantity=5,
            unit_cost="5.00",
            is_active=False,
        )
        self.client.force_authenticate(self.patient_user)
        response = self.client.get(
            reverse("medicine-update", args=[inactive.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.pharmacist_user)
        response = self.client.get(
            reverse("medicine-update", args=[inactive.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(
            reverse("medicine-update", args=[inactive.pk]),
            {"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inactive.refresh_from_db()
        self.assertTrue(inactive.is_active)

    def test_prescribing_doctor_can_cancel_pending_prescription(self):
        prescription = self.create_prescription()
        self.client.force_authenticate(self.doctor_user)

        response = self.client.post(
            reverse("prescription-cancel", args=[prescription.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prescription.refresh_from_db()
        self.assertEqual(
            prescription.status,
            PrescriptionStatus.CANCELLED,
        )

    def test_other_doctor_cannot_cancel_prescription(self):
        prescription = self.create_prescription()
        self.client.force_authenticate(self.other_doctor_user)

        response = self.client.post(
            reverse("prescription-cancel", args=[prescription.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_can_cancel_any_pending_prescription(self):
        prescription = self.create_prescription()
        self.client.force_authenticate(self.prescription_manager_user)

        response = self.client.post(
            reverse("prescription-cancel", args=[prescription.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dispensed_and_cancelled_prescriptions_cannot_be_cancelled(self):
        dispensed = self.create_prescription(
            status=PrescriptionStatus.DISPENSED
        )
        cancelled = self.create_prescription(
            status=PrescriptionStatus.CANCELLED
        )
        self.client.force_authenticate(self.doctor_user)

        response = self.client.post(
            reverse("prescription-cancel", args=[dispensed.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            reverse("prescription-cancel", args=[cancelled.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dispensing_is_idempotent_and_deducts_stock_once(self):
        prescription = self.create_prescription()
        self.client.force_authenticate(self.pharmacist_user)

        response = self.client.post(
            reverse("prescription-dispense", args=[prescription.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 15)

        response = self.client.post(
            reverse("prescription-dispense", args=[prescription.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 15)