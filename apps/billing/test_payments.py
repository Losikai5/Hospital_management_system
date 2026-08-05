from datetime import date, time
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment, AppointmentStatus
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile
from apps.users.models import CustomUser, Permission, Role, RolePermission

from .models import InvoiceStatus
from .services import generate_invoice


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(role=role, permission=permission)
    return role


class InvoicePaymentApiTests(APITestCase):
    def setUp(self):
        billing_role = create_role(
            "RECEPTIONIST",
            [
                "can_view_invoices",
                "can_view_all_invoices",
                "can_record_invoice_payments",
            ],
        )
        patient_role = create_role(
            "PATIENT",
            ["can_view_invoices"],
        )
        doctor_role = create_role("DOCTOR", [])
        self.billing_user = CustomUser.objects.create_user(
            email="billing-payment@example.com",
            password="SafePassword!123",
            role=billing_role,
        )
        self.patient_user = CustomUser.objects.create_user(
            email="patient-payment@example.com",
            password="SafePassword!123",
            role=patient_role,
        )
        doctor_user = CustomUser.objects.create_user(
            email="doctor-payment@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        doctor = DoctorProfile.objects.create(
            user=doctor_user,
            license_number="PAYMENT-LIC-1",
            consultation_fee=Decimal("100.00"),
        )
        patient = PatientProfile.objects.create(user=self.patient_user)
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            appointment_date=date(2026, 8, 20),
            appointment_time=time(10, 0),
            status=AppointmentStatus.COMPLETED,
        )
        self.invoice = generate_invoice(appointment=appointment)
        self.url = reverse(
            "invoice-payment-list-create",
            args=[self.invoice.pk],
        )

    def record_payment(self, amount, reference):
        return self.client.post(
            self.url,
            {
                "amount": amount,
                "method": "MOBILE_MONEY",
                "reference": reference,
            },
            format="json",
        )

    def test_partial_then_full_payment_updates_derived_status(self):
        self.client.force_authenticate(self.billing_user)

        response = self.record_payment("40.00", "MOMO-001")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("40.00"))
        self.assertEqual(self.invoice.balance, Decimal("60.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PARTIAL)

        response = self.record_payment("60.00", "MOMO-002")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("100.00"))
        self.assertEqual(self.invoice.balance, Decimal("0.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PAID)

    def test_overpayment_and_payment_on_paid_invoice_are_rejected(self):
        self.client.force_authenticate(self.billing_user)

        response = self.record_payment("101.00", "MOMO-OVER")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            self.record_payment("100.00", "MOMO-FULL").status_code,
            status.HTTP_201_CREATED,
        )
        response = self.record_payment("1.00", "MOMO-LATE")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patient_can_view_history_but_cannot_record_payment(self):
        self.client.force_authenticate(self.billing_user)
        self.record_payment("25.00", "MOMO-VIEW")

        self.client.force_authenticate(self.patient_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["reference"], "MOMO-VIEW")

        response = self.record_payment("25.00", "MOMO-FORBIDDEN")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

