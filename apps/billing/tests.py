from datetime import date, time
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment, AppointmentStatus
from apps.doctors.models import DoctorProfile
from apps.medical_records.models import MedicalRecord
from apps.patients.models import PatientProfile
from apps.pharmacy.models import Medicine, Prescription, PrescriptionStatus
from apps.users.models import CustomUser, Permission, Role, RolePermission

from .models import Invoice


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(role=role, permission=permission)
    return role


class BillingApiTests(APITestCase):
    def setUp(self):
        self.billing_role = create_role(
            "BILLING_STAFF",
            [
                "can_view_invoices",
                "can_view_all_invoices",
                "can_create_invoices",
            ],
        )
        self.patient_role = create_role(
            "PATIENT",
            ["can_view_invoices"],
        )
        self.doctor_role = create_role("DOCTOR", [])
        self.staff_user = CustomUser.objects.create_user(
            email="billing@example.com",
            password="SafePassword!123",
            role=self.billing_role,
        )
        self.patient_user = CustomUser.objects.create_user(
            email="patient@example.com",
            password="SafePassword!123",
            role=self.patient_role,
        )
        self.other_patient_user = CustomUser.objects.create_user(
            email="other-patient@example.com",
            password="SafePassword!123",
            role=self.patient_role,
        )
        doctor_user = CustomUser.objects.create_user(
            email="doctor@example.com",
            password="SafePassword!123",
            role=self.doctor_role,
        )
        self.doctor = DoctorProfile.objects.create(
            user=doctor_user,
            license_number="BILL-LIC-1",
            consultation_fee=Decimal("100.00"),
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.other_patient = PatientProfile.objects.create(
            user=self.other_patient_user
        )
        self.appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date(2026, 8, 10),
            appointment_time=time(8, 0),
            status=AppointmentStatus.COMPLETED,
        )
        record = MedicalRecord.objects.create(
            appointment=self.appointment,
            diagnosis="Diagnosis",
        )
        dispensed_medicine = Medicine.objects.create(
            name="Dispensed medicine",
            stock_quantity=20,
            unit_cost=Decimal("10.00"),
        )
        pending_medicine = Medicine.objects.create(
            name="Pending medicine",
            stock_quantity=20,
            unit_cost=Decimal("50.00"),
        )
        Prescription.objects.create(
            medical_record=record,
            medicine=dispensed_medicine,
            dosage="One",
            frequency="Daily",
            duration="Two days",
            quantity_prescribed=2,
            status=PrescriptionStatus.DISPENSED,
        )
        Prescription.objects.create(
            medical_record=record,
            medicine=pending_medicine,
            dosage="One",
            frequency="Daily",
            duration="One day",
            quantity_prescribed=1,
            status=PrescriptionStatus.PENDING,
        )

    def create_invoice(self):
        self.client.force_authenticate(self.staff_user)
        return self.client.post(
            reverse("invoice-list-create"),
            {"appointment": self.appointment.pk},
            format="json",
        )

    def test_invoice_is_server_calculated_from_consultation_and_dispensed_items(self):
        response = self.create_invoice()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("120.00"))
        self.assertEqual(len(response.data["items"]), 2)
        self.assertFalse(
            any(
                item["description"] == "Pending medicine"
                for item in response.data["items"]
            )
        )

    def test_duplicate_and_non_completed_invoices_are_rejected(self):
        first_response = self.create_invoice()
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        duplicate_response = self.create_invoice()
        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Invoice.objects.count(), 1)

        pending_appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date(2026, 8, 11),
            appointment_time=time(8, 0),
            status=AppointmentStatus.PENDING,
        )
        response = self.client.post(
            reverse("invoice-list-create"),
            {"appointment": pending_appointment.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patient_can_only_access_own_invoice_and_pdf(self):
        response = self.create_invoice()
        invoice_id = response.data["id"]

        other_appointment = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.other_patient,
            appointment_date=date(2026, 8, 12),
            appointment_time=time(9, 0),
            status=AppointmentStatus.COMPLETED,
        )
        other_response = self.client.post(
            reverse("invoice-list-create"),
            {"appointment": other_appointment.pk},
            format="json",
        )
        other_invoice_id = other_response.data["id"]

        self.client.force_authenticate(self.patient_user)
        list_response = self.client.get(reverse("invoice-list-create"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [invoice["id"] for invoice in list_response.data],
            [invoice_id],
        )

        detail_response = self.client.get(
            reverse("invoice-detail", args=[other_invoice_id])
        )
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

        pdf_response = self.client.get(
            reverse("invoice-pdf", args=[invoice_id])
        )
        self.assertEqual(pdf_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(
            b"".join(pdf_response.streaming_content).startswith(b"%PDF")
        )

