from rest_framework import serializers as drf_serializers
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from django.contrib.auth import authenticate
from .emails import send_staff_invitation_email
from .service import StaffInvitationAcceptanceError, create_staff_invitation,accept_staff_invitation
from apps.core.permissions import HasCustomPermission
from apps.core.schemas import ErrorResponse, MessageResponse
from .models import CustomUser
from .serializers import ( UserRegistrationSerializer, UserProfileSerializer, ChangePasswordSerializer, StaffInvitationSerializer,StaffInvitationAcceptSerializer,)


@extend_schema(
    tags=["Authentication & Users"],
    summary="Register a new patient account",
    description=(
        "Creates a new patient user account and a matching patient profile. "
        "The PATIENT role is assigned automatically. "
        "Passwords are validated against Django's password validators."
    ),
    request=UserRegistrationSerializer,
    responses={201: UserRegistrationSerializer},
)
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Authentication & Users"],
    summary="Log in",
    description=(
        "Authenticates a user with email and password and returns a JWT pair. "
        "The access token is short-lived; the refresh token should be stored "
        "securely and exchanged at `/token/refresh/`."
    ),
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
            }
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication & Users"],
    summary="Log out",
    description=(
        "Blacklists the provided JWT refresh token so it can no longer be used "
        "to obtain new access tokens."
    ),
    request=inline_serializer(
        "LogoutRequest",
        {"refresh": drf_serializers.CharField()},
    ),
    responses={
        205: None,
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


@extend_schema_view(
    get=extend_schema(
        tags=["Authentication & Users"],
        summary="Get current user profile",
        description="Returns the profile of the currently authenticated user.",
        responses={200: UserProfileSerializer},
    ),
    patch=extend_schema(
        tags=["Authentication & Users"],
        summary="Update current user profile",
        description=(
            "Partially updates the profile of the currently authenticated user. "
            "The email and role cannot be changed here."
        ),
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
    ),
)
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["Authentication & Users"],
    summary="Change password",
    description=(
        "Changes the password of the currently authenticated user. "
        "The old password must be provided and verified."
    ),
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
    tags=["Staff Management"],
    summary="Create a staff invitation",
    description=(
        "Invites a new staff member by email. The invitee receives an email "
        "containing a signed invitation token. Requires `can_create_users` and "
        "`can_assign_roles` permissions."
    ),
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
    description=(
        "Accepts a previously created staff invitation by setting the invitee's "
        "password using the invitation token sent by email."
    ),
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

