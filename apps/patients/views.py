from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from apps.core.permissions import HasCustomPermission

from .models import PatientProfile
from .serializers import (
    PatientCreateSerializer,
    PatientListSerializer,
    PatientProfileSerializer,
)


@extend_schema_view(
    get=extend_schema(
        tags=["Patients"],
        summary="List and search patients",
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                description="Search by patient name or email.",
            ),
        ],
        responses={200: PatientListSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Patients"],
        summary="Register a walk-in patient",
        request=PatientCreateSerializer,
        responses={201: PatientListSerializer},
    ),
)
class PatientListCreateView(APIView):
    """Staff patient registry: search patients (GET ?q=) and register a new
    walk-in patient (POST). Powers the receptionist's book-for-a-patient flow."""

    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_all_patients",),
        "POST": ("can_create_patients",),
    }


    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return PatientProfile.objects.none()

        queryset = PatientProfile.objects.select_related("user").filter(
            user__role__code="PATIENT",
        )

        q = self.request.query_params.get("q")
        if q:
            queryset = queryset.filter(
                Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__email__icontains=q)
            )

        return queryset.order_by("user__first_name", "user__last_name")


    def get(self, request):
        serializer = PatientListSerializer(
            self.get_queryset(),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = PatientCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()
        return Response(
            PatientListSerializer(patient).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Patients"],
        summary="Get a patient profile",
        responses={200: PatientProfileSerializer},
    ),
    patch=extend_schema(
        tags=["Patients"],
        summary="Update a patient profile",
        request=PatientProfileSerializer,
        responses={200: PatientProfileSerializer},
    ),
)
class PatientDetailView(APIView):
    serializer_class = PatientProfileSerializer
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_all_patients",),
        "PATCH": (
            "can_view_all_patients",
            "can_edit_patients",
        ),
    }

    def get_object(self, pk):
        return get_object_or_404(
            PatientProfile.objects.select_related(
                "user",
                "user__role",
            ),
            pk=pk,
            user__role__code="PATIENT",
        )

    def get(self, request, pk):
        serializer = self.serializer_class(
            self.get_object(pk),
            context={"request": request},
        )
        return Response(serializer.data)

    def patch(self, request, pk):
        serializer = self.serializer_class(
            self.get_object(pk),
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Patients"],
        summary="Get my patient profile",
        responses={200: PatientProfileSerializer},
    ),
    patch=extend_schema(
        tags=["Patients"],
        summary="Update my patient profile",
        request=PatientProfileSerializer,
        responses={200: PatientProfileSerializer},
    ),
)
class PatientProfileView(APIView):
    serializer_class = PatientProfileSerializer
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_patients",),
        "PATCH": ("can_edit_patients",),
    }

    def get_object(self, user):
        return get_object_or_404(
            PatientProfile.objects.select_related(
                "user",
                "user__role",
            ),
            user=user,
        )

    def get(self, request):
        serializer = self.serializer_class(
            self.get_object(request.user),
            context={"request": request},
        )
        return Response(serializer.data)

    def patch(self, request):
        serializer = self.serializer_class(
            self.get_object(request.user),
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
