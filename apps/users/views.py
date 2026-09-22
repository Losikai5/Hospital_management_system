from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.module_loading import import_string
from .emails import send_staff_invitation_email, send_password_reset_email
from .service import StaffInvitationAcceptanceError, create_staff_invitation,accept_staff_invitation
from apps.core.permissions import HasCustomPermission
from apps.core.schemas import ErrorResponse, MessageResponse
from .models import CustomUser, Permission, Role
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PermissionSerializer,
    RoleCreateSerializer,
    RoleDetailSerializer,
    RolePermissionUpdateSerializer,
    StaffInvitationAcceptSerializer,
    StaffInvitationSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)

ConfiguredTokenRefreshSerializer = import_string(
    api_settings.TOKEN_REFRESH_SERIALIZER
)


@extend_schema(
    tags=["Authentication & Users"],
    summary="Register a new patient account",
    request=UserRegistrationSerializer,
    responses={201: UserRegistrationSerializer},
)
class RegisterView(APIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            self.serializer_class(user).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Authentication & Users"],
    summary="Log in",
    request=inline_serializer(
        "LoginRequest",
        {
            "email": drf_serializers.EmailField(),
            "password": drf_serializers.CharField(write_only=True),
        },
    ),
    responses={
        200: inline_serializer(
            "LoginResponse",
            {
                "tokens": inline_serializer(
                    "TokenPair",
                    {
                        "refresh": drf_serializers.CharField(),
                        "access": drf_serializers.CharField(),
                    },
                ),
                "user": inline_serializer(
                    "LoginUser",
                    {
                        "id": drf_serializers.IntegerField(),
                        "email": drf_serializers.EmailField(),
                        "role": drf_serializers.CharField(),
                        "permissions": drf_serializers.ListField(
                            child=drf_serializers.CharField(),
                        ),
                    },
                ),
            },
        ),
        400: ErrorResponse,
        401: ErrorResponse,
        403: ErrorResponse,
    },
)
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
                'permissions': list(
                    user.role.permissions.filter(is_active=True)
                    .order_by('code')
                    .values_list('code', flat=True)
                ),
            }
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication & Users"],
    summary="Log out",
    request=inline_serializer(
        "LogoutRequest",
        {"refresh": drf_serializers.CharField()},
    ),
    responses={
        205: MessageResponse,
        400: ErrorResponse,
    },
)
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


@extend_schema(
    tags=["Authentication & Users"],
    summary="Refresh access token",
    request=ConfiguredTokenRefreshSerializer,
    responses={200: ConfiguredTokenRefreshSerializer, 401: ErrorResponse},
)
class TokenRefreshAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ConfiguredTokenRefreshSerializer
    www_authenticate_realm = "api"

    def get_authenticate_header(self, request):
        return f'{AUTH_HEADER_TYPES[0]} realm="{self.www_authenticate_realm}"'

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as error:
            raise InvalidToken(error.args[0]) from error
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

@extend_schema_view(
    get=extend_schema(
        tags=["Authentication & Users"],
        summary="Get current user profile",
        responses={200: UserProfileSerializer},
    ),
    patch=extend_schema(
        tags=["Authentication & Users"],
        summary="Update current user profile",
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
    ),
)
class ProfileView(APIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(self.serializer_class(request.user).data)

    def patch(self, request):
        serializer = self.serializer_class(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(
    tags=["Authentication & Users"],
    summary="Change password",
    request=ChangePasswordSerializer,
    responses={
        200: MessageResponse,
        400: ErrorResponse,
    },
)
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

@extend_schema(
    tags=["Authentication & Users"],
    summary="Request a password reset",
    request=PasswordResetRequestSerializer,
    responses={200: MessageResponse, 400: ErrorResponse},
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


@extend_schema(
    tags=["Authentication & Users"],
    summary="Confirm a password reset",
    request=PasswordResetConfirmSerializer,
    responses={200: MessageResponse, 400: ErrorResponse},
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


@extend_schema(
    tags=["Staff Management"],
    summary="Create a staff invitation",
    request=StaffInvitationSerializer,
    responses={
        201: inline_serializer(
            "StaffInvitationCreated",
            {
                "message": drf_serializers.CharField(),
                "invitation": inline_serializer(
                    "StaffInvitationData",
                    {
                        "id": drf_serializers.IntegerField(),
                        "email": drf_serializers.EmailField(),
                        "role": drf_serializers.CharField(),
                        "invited_by": drf_serializers.EmailField(),
                        "expires_at": drf_serializers.DateTimeField(),
                    },
                ),
            },
        ),
        400: ErrorResponse,
    },
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

@extend_schema(
    tags=["Staff Management"],
    summary="Accept a staff invitation",
    request=StaffInvitationAcceptSerializer,
    responses={
        200: inline_serializer(
            "StaffInvitationAccepted",
            {
                "message": drf_serializers.CharField(),
                "user": inline_serializer(
                    "InvitedUser",
                    {
                        "id": drf_serializers.IntegerField(),
                        "email": drf_serializers.EmailField(),
                        "role": drf_serializers.CharField(),
                        "is_active": drf_serializers.BooleanField(),
                        "is_verified": drf_serializers.BooleanField(),
                    },
                ),
            },
        ),
        400: ErrorResponse,
    },
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


@extend_schema_view(
    get=extend_schema(
        tags=["Role Management"],
        summary="List roles",
        responses={200: RoleDetailSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Role Management"],
        summary="Create a custom role",
        request=RoleCreateSerializer,
        responses={201: RoleDetailSerializer},
    ),
)
class RoleListCreateView(APIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_roles",),
        "POST": ("can_create_roles", "can_assign_permissions"),
    }

    def get(self, request):
        roles = Role.objects.prefetch_related("permissions").order_by("code")
        return Response(RoleDetailSerializer(roles, many=True).data)

    def post(self, request):
        serializer = RoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return Response(RoleDetailSerializer(role).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(tags=["Role Management"], summary="Get a role", responses={200: RoleDetailSerializer}),
    patch=extend_schema(tags=["Role Management"], summary="Update a role", request=RoleDetailSerializer, responses={200: RoleDetailSerializer}),
    put=extend_schema(tags=["Role Management"], summary="Replace a role", request=RoleDetailSerializer, responses={200: RoleDetailSerializer}),
    delete=extend_schema(tags=["Role Management"], summary="Delete a custom role", responses={204: None, 400: ErrorResponse}),
)
class RoleDetailView(APIView):
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_roles",),
        "PATCH": ("can_edit_roles",),
        "PUT": ("can_edit_roles",),
        "DELETE": ("can_edit_roles",),
    }

    @staticmethod
    def get_role(code):
        return get_object_or_404(Role.objects.prefetch_related("permissions"), code=code.upper())

    def get(self, request, code):
        return Response(RoleDetailSerializer(self.get_role(code)).data)

    def patch(self, request, code):
        role = self.get_role(code)
        serializer = RoleDetailSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, code):
        role = self.get_role(code)
        serializer = RoleDetailSerializer(role, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, code):
        role = self.get_role(code)
        if role.is_system:
            return Response({"detail": "System roles cannot be deleted."}, status=status.HTTP_400_BAD_REQUEST)
        if role.users.exists():
            return Response({"detail": "Cannot delete a role that is currently assigned to users."}, status=status.HTTP_400_BAD_REQUEST)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Role Management"],
    summary="Assign permissions to a role",
    request=RolePermissionUpdateSerializer,
    responses={200: RoleDetailSerializer, 400: ErrorResponse},
)
class RolePermissionUpdateView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_assign_permissions"
    serializer_class = RolePermissionUpdateSerializer

    def put(self, request, code):
        role = get_object_or_404(Role, code=code.upper())
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        permissions = Permission.objects.filter(
            code__in=serializer.validated_data["permissions"],
            is_active=True,
        )
        role.permissions.set(permissions)
        return Response(RoleDetailSerializer(role).data)


@extend_schema(
    tags=["Role Management"],
    summary="List permissions",
    responses={200: PermissionSerializer(many=True)},
)
class PermissionListView(APIView):
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_permissions"

    def get(self, request):
        permissions = Permission.objects.filter(is_active=True).order_by("code")
        return Response(PermissionSerializer(permissions, many=True).data)
