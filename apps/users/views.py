from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .emails import send_staff_invitation_email, send_password_reset_email
from .service import StaffInvitationAcceptanceError, create_staff_invitation,accept_staff_invitation
from apps.core.permissions import HasCustomPermission
from .models import CustomUser
from .serializers import ( UserRegistrationSerializer, UserProfileSerializer, ChangePasswordSerializer, StaffInvitationSerializer,StaffInvitationAcceptSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,)


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    serializer_class = UserRegistrationSerializer 
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role_code,
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer 

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class PasswordResetRequestView(APIView):
    """Public: emails a reset link. Always returns 200 so it never reveals
    whether an email is registered."""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = CustomUser.objects.normalize_email(serializer.validated_data["email"])
        user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            try:
                send_password_reset_email(user=user, uid=uid, token=token)
            except Exception:
                # Never surface send failures (would leak which emails exist).
                pass

        return Response(
            {"message": "If an account exists for that email, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Public: sets a new password given a valid uid + token."""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password reset successful. You can now sign in."},
            status=status.HTTP_200_OK,
        )


class StaffInvitationView(APIView):
    permission_classes = [HasCustomPermission]
    serializer_class = StaffInvitationSerializer
    required_permissions = (
        "can_create_users",
        "can_assign_roles",
    )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation, token = create_staff_invitation(
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by=request.user,
        )

        send_staff_invitation_email(
            invitation=invitation,
            token=token,
        )

        return Response(
            {
                "message": "Staff invitation created successfully.",
                "invitation": {
                    "id": invitation.id,
                    "email": invitation.user.email,
                    "role": invitation.user.role.code,
                    "invited_by": invitation.invited_by.email,
                    "expires_at": invitation.expires_at,
                },
            },
            status=status.HTTP_201_CREATED,
        )

class StaffInvitationAcceptView(APIView):
    permission_classes = [AllowAny]
    serializer_class = StaffInvitationAcceptSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = accept_staff_invitation(
                token=serializer.validated_data["token"],
                password=serializer.validated_data["password"],
            )   
        except StaffInvitationAcceptanceError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Staff invitation accepted successfully.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role.code,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                },
            },
            status=status.HTTP_200_OK,
        )    

