from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Role


class TokenRefreshAPIViewTests(APITestCase):
    def setUp(self):
        role = Role.objects.create(code="TOKEN_TEST", name="Token test")
        self.user = CustomUser.objects.create_user(
            email="token-refresh@example.com",
            password="SafePassword!123",
            role=role,
        )

    def test_rotates_a_valid_refresh_token(self):
        refresh = str(RefreshToken.for_user(self.user))
        response = self.client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        reused_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(
            reused_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )