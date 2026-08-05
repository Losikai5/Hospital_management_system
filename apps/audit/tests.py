from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import CustomUser, Permission, Role, RolePermission

from .models import AuditLog


def create_role(code, permission_codes):
    role = Role.objects.create(code=code, name=code)
    for permission_code in permission_codes:
        permission, _ = Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code},
        )
        RolePermission.objects.create(role=role, permission=permission)
    return role


class AuditLogTests(APITestCase):
    def setUp(self):
        viewer_role = create_role(
            "AUDITOR",
            ["can_view_audit_logs"],
        )
        user_role = create_role("PATIENT", [])
        self.viewer = CustomUser.objects.create_user(
            email="auditor@example.com",
            password="SafePassword!123",
            role=viewer_role,
        )
        self.user = CustomUser.objects.create_user(
            email="patient-audit@example.com",
            password="SafePassword!123",
            role=user_role,
        )

    def test_mutating_api_request_is_logged_without_request_body(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("profile"),
            {
                "first_name": "Audited",
                "address": "Sensitive address not copied to audit metadata",
            },
            format="json",
            HTTP_X_REQUEST_ID="acceptance-request-1",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["X-Request-ID"], "acceptance-request-1")

        audit_log = AuditLog.objects.get(
            request_id="acceptance-request-1"
        )
        self.assertEqual(audit_log.actor, self.user)
        self.assertEqual(audit_log.action, "profile")
        self.assertEqual(audit_log.method, "PATCH")
        self.assertEqual(audit_log.status_code, 200)
        self.assertNotIn("address", audit_log.metadata)
        self.assertNotIn("Sensitive", str(audit_log.metadata))

    def test_auditor_can_read_logs_but_regular_user_cannot(self):
        AuditLog.objects.create(
            actor=self.user,
            actor_email=self.user.email,
            action="test-action",
            method="POST",
            path="/api/v1/test/",
            status_code=201,
            request_id="audit-test",
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("audit-log-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.viewer)
        response = self.client.get(
            reverse("audit-log-list"),
            {"actor_email": "patient-audit", "limit": 10},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_audit_logs_are_immutable(self):
        audit_log = AuditLog.objects.create(
            action="immutable",
            method="POST",
            path="/api/v1/test/",
            status_code=200,
            request_id="immutable-test",
        )
        audit_log.action = "changed"
        with self.assertRaises(DjangoValidationError):
            audit_log.save()
        with self.assertRaises(DjangoValidationError):
            audit_log.delete()

