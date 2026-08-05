from datetime import time, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditLog
from apps.doctors.models import DoctorProfile, DoctorSchedule
from apps.patients.models import PatientProfile
from apps.pharmacy.models import Medicine
from apps.users.models import CustomUser, Permission, Role, RolePermission


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(role=role, permission=permission)
    return role


class HospitalWorkflowAcceptanceTests(APITestCase):
    """Exercises the main clinical, pharmacy, billing, and audit workflow."""

    def setUp(self):
        patient_role = create_role(
            "PATIENT",
            ["can_view_doctors", "can_create_appointments", "can_view_invoices"],
        )
        doctor_role = create_role(
            "DOCTOR",
            [
                "can_confirm_appointments",
                "can_complete_appointments",
                "can_create_medical_records",
                "can_create_prescriptions",
            ],
        )
        pharmacist_role = create_role(
            "PHARMACIST",
            ["can_dispense_prescriptions"],
        )
        billing_role = create_role(
            "BILLING",
            [
                "can_view_invoices",
                "can_view_all_invoices",
                "can_create_invoices",
                "can_record_invoice_payments",
            ],
        )
        auditor_role = create_role(
            "AUDITOR",
            ["can_view_audit_logs"],
        )

        self.patient_user = CustomUser.objects.create_user(
            email="acceptance-patient@example.com",
            password="SafePassword!123",
            role=patient_role,
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.doctor_user = CustomUser.objects.create_user(
            email="acceptance-doctor@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            license_number="ACCEPTANCE-LICENCE",
            consultation_fee=Decimal("80.00"),
        )
        self.pharmacist_user = CustomUser.objects.create_user(
            email="acceptance-pharmacist@example.com",
            password="SafePassword!123",
            role=pharmacist_role,
        )
        self.billing_user = CustomUser.objects.create_user(
            email="acceptance-billing@example.com",
            password="SafePassword!123",
            role=billing_role,
        )
        self.auditor_user = CustomUser.objects.create_user(
            email="acceptance-auditor@example.com",
            password="SafePassword!123",
            role=auditor_role,
        )
        self.appointment_date = timezone.localdate() + timedelta(days=7)
        DoctorSchedule.objects.create(
            doctor=self.doctor,
            day_of_week=self.appointment_date.weekday(),
            start_time=time(8, 0),
            end_time=time(9, 0),
            session_duration=30,
        )
        self.medicine = Medicine.objects.create(
            name="Acceptance Medicine",
            stock_quantity=20,
            unit_cost=Decimal("5.00"),
            low_stock_threshold=2,
        )

    def test_patient_visit_to_paid_invoice_is_audited(self):
        self.client.force_authenticate(self.patient_user)
        response = self.client.post(
            reverse("appointment-book"),
            {
                "doctor": self.doctor.pk,
                "appointment_date": self.appointment_date.isoformat(),
                "appointment_time": "08:00:00",
                "reason": "Acceptance test visit",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        appointment_id = response.data["id"]

        self.client.force_authenticate(self.doctor_user)
        response = self.client.post(reverse("appointment-confirm", args=[appointment_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse("appointment-complete", args=[appointment_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse("medical-record-create"),
            {
                "appointment": appointment_id,
                "diagnosis": "Routine condition",
                "treatment_prescribed": "Medication",
                "notes": "Acceptance workflow",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record_id = response.data["id"]

        response = self.client.post(
            reverse("prescription-create"),
            {
                "medical_record": record_id,
                "medicine": self.medicine.pk,
                "dosage": "One tablet",
                "frequency": "Daily",
                "duration": "Two days",
                "quantity_prescribed": 2,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        prescription_id = response.data["id"]

        self.client.force_authenticate(self.pharmacist_user)
        response = self.client.post(
            reverse("prescription-dispense", args=[prescription_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 18)

        self.client.force_authenticate(self.billing_user)
        response = self.client.post(
            reverse("invoice-list-create"),
            {"appointment": appointment_id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invoice_id = response.data["id"]
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("90.00"))

        response = self.client.post(
            reverse("invoice-payment-list-create", args=[invoice_id]),
            {
                "amount": response.data["total_amount"],
                "method": "MOBILE_MONEY",
                "reference": "ACCEPTANCE-PAYMENT-1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.patient_user)
        response = self.client.get(reverse("invoice-detail", args=[invoice_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "PAID")
        self.assertEqual(Decimal(response.data["balance"]), Decimal("0.00"))

        self.client.force_authenticate(self.auditor_user)
        response = self.client.get(reverse("audit-log-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 7)
        self.assertFalse(any("body" in log.metadata for log in AuditLog.objects.all()))