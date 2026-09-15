from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import CustomUser, Permission, Role, RolePermission

from .models import DoctorProfile, Specialization


class DoctorOrderingTests(APITestCase):
    def setUp(self):
        permission = Permission.objects.create(
            code="can_view_doctors",
            name="Can view doctors",
        )
        role = Role.objects.create(code="VIEWER", name="Viewer")
        RolePermission.objects.create(role=role, permission=permission)
        self.viewer = CustomUser.objects.create_user(
            email="viewer@example.com",
            password="SafePassword!123",
            role=role,
        )
        doctor_role = Role.objects.create(code="DOCTOR", name="Doctor")
        expensive_user = CustomUser.objects.create_user(
            email="expensive@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        affordable_user = CustomUser.objects.create_user(
            email="affordable@example.com",
            password="SafePassword!123",
            role=doctor_role,
        )
        self.expensive = DoctorProfile.objects.create(
            user=expensive_user,
            license_number="ORDER-LIC-1",
            specialization=Specialization.CARDIOLOGY,
            consultation_fee="200.00",
        )
        self.affordable = DoctorProfile.objects.create(
            user=affordable_user,
            license_number="ORDER-LIC-2",
            specialization=Specialization.PEDIATRICS,
            consultation_fee="50.00",
        )

    def test_doctors_support_safe_ordering(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(
            reverse("doctor-list"),
            {"ordering": "consultation_fee"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [doctor["id"] for doctor in response.data],
            [self.affordable.pk, self.expensive.pk],
        )

        response = self.client.get(
            reverse("doctor-list"),
            {"ordering": "user__password"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

