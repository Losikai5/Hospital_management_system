from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import (
    CustomUser,
    Permission,
    Role,
    RolePermission,
)

from .models import PatientProfile


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


class PatientApiTests(APITestCase):
    def setUp(self):
        self.patient_role = create_role(
            "PATIENT",
            ["can_view_patients", "can_edit_patients"],
        )
        self.staff_role = create_role(
            "PATIENT_MANAGER",
            [
                "can_view_all_patients",
                "can_create_patients",
                "can_edit_patients",
            ],
        )
        self.patient_user = CustomUser.objects.create_user(
            email="patient@example.com",
            password="SafePassword!123",
            role=self.patient_role,
        )
        self.patient = PatientProfile.objects.create(
            user=self.patient_user,
        )
        self.staff_user = CustomUser.objects.create_user(
            email="staff@example.com",
            password="SafePassword!123",
            role=self.staff_role,
        )

    def test_patient_can_view_and_update_own_profile_only(self):
        self.client.force_authenticate(self.patient_user)

        response = self.client.get(reverse("patient-profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(
            reverse("patient-profile"),
            {"blood_type": "O+"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.blood_type, "O+")

        response = self.client.get(
            reverse("patient-detail", args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_list_create_and_update_patient_profiles(self):
        self.client.force_authenticate(self.staff_user)

        response = self.client.get(
            reverse("patient-list-create"),
            {"q": "patient@example.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.client.post(
            reverse("patient-list-create"),
            {
                "email": "walkin@example.com",
                "first_name": "Walk",
                "last_name": "In",
                "phone": "+256700000001",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            PatientProfile.objects.filter(
                user__email="walkin@example.com"
            ).exists()
        )

        response = self.client.patch(
            reverse("patient-detail", args=[self.patient.pk]),
            {"insurance_details": "Policy-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.insurance_details, "Policy-123")