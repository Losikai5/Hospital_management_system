from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.core.permissions import HasCustomPermission

from .models import DoctorProfile, DoctorSchedule
from .serializers import (
    DoctorDirectorySerializer,
    DoctorOnboardingSerializer,
    DoctorScheduleSerializer,
)


class DoctorDirectoryBaseView(APIView):
    serializer_class = DoctorDirectorySerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_view_doctors"

    def get_queryset(self):
        queryset = DoctorProfile.objects.select_related(
            "user",
            "user__role",
        )

        if self.request.user.has_permission("can_view_all_doctors"):
            return queryset

        return queryset.filter(
            is_available=True,
            user__is_active=True,
            user__role__is_active=True,
        )


@extend_schema(
    tags=["Doctors"],
    summary="List doctors",
    description=(
        "Returns the doctor directory. Users without the `can_view_all_doctors` "
        "permission only see active and available doctors."
    ),
    responses={200: DoctorDirectorySerializer(many=True)},
)
class DoctorDirectoryView(DoctorDirectoryBaseView):
    def get(self, request):
        serializer = self.serializer_class(
            self.get_queryset(),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


@extend_schema(
    tags=["Doctors"],
    summary="Get a single doctor",
    description=(
        "Returns a single doctor profile by ID. Users without the "
        "`can_view_all_doctors` permission can only retrieve active and "
        "available doctors."
    ),
    responses={200: DoctorDirectorySerializer},
)
class DoctorDirectoryDetailView(DoctorDirectoryBaseView):
    def get(self, request, pk):
        doctor = get_object_or_404(
            self.get_queryset(),
            pk=pk,
        )
        serializer = self.serializer_class(
            doctor,
            context={"request": request},
        )
        return Response(serializer.data)


class DoctorScheduleBaseView(APIView):
    serializer_class = DoctorScheduleSerializer
    permission_classes = [HasCustomPermission]
    required_permission = "can_manage_doctor_schedules"

    def get_doctor_profile(self):
        return get_object_or_404(
            DoctorProfile,
            user=self.request.user,
        )

    def get_queryset(self):
        return DoctorSchedule.objects.filter(
            doctor=self.get_doctor_profile(),
        ).select_related(
            "doctor",
            "doctor__user",
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Doctors"],
        summary="List my doctor schedules",
        description=(
            "Returns the weekly schedules of the currently authenticated doctor."
        ),
        responses={200: DoctorScheduleSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Doctors"],
        summary="Create a doctor schedule",
        description=(
            "Creates a weekly schedule entry (day, working hours and session "
            "length) for the currently authenticated doctor. Only one schedule "
            "per day is allowed."
        ),
        request=DoctorScheduleSerializer,
        responses={201: DoctorScheduleSerializer},
    ),
)
class DoctorScheduleListCreateView(DoctorScheduleBaseView):
    def get(self, request):
        serializer = self.serializer_class(
            self.get_queryset(),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        doctor = self.get_doctor_profile()
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(doctor=doctor)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Doctors"],
        summary="Get a doctor schedule",
        description="Returns a single schedule entry owned by the authenticated doctor.",
        responses={200: DoctorScheduleSerializer},
    ),
    patch=extend_schema(
        tags=["Doctors"],
        summary="Update a doctor schedule",
        description=(
            "Partially updates a schedule entry owned by the authenticated doctor."
        ),
        request=DoctorScheduleSerializer,
        responses={200: DoctorScheduleSerializer},
    ),
)
class DoctorScheduleDetailView(DoctorScheduleBaseView):
    def get_object(self, pk):
        return get_object_or_404(
            self.get_queryset(),
            pk=pk,
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
        tags=["Doctors"],
        summary="Get my doctor profile",
        description=(
            "Returns the doctor profile (and linked user details) of the "
            "currently authenticated doctor."
        ),
        responses={200: DoctorOnboardingSerializer},
    ),
    post=extend_schema(
        tags=["Doctors"],
        summary="Complete doctor onboarding",
        description=(
            "Creates a doctor profile for the currently authenticated user, "
            "filling in the linked user fields (name, phone, etc.) in the same "
            "request. Can only be run once per user."
        ),
        request=DoctorOnboardingSerializer,
        responses={201: DoctorOnboardingSerializer},
    ),
    patch=extend_schema(
        tags=["Doctors"],
        summary="Update my doctor profile",
        description=(
            "Partially updates the doctor profile and linked user fields of the "
            "currently authenticated doctor."
        ),
        request=DoctorOnboardingSerializer,
        responses={200: DoctorOnboardingSerializer},
    ),
)
class DoctorOnboardingView(APIView):
    serializer_class = DoctorOnboardingSerializer
    permission_classes = [HasCustomPermission]
    required_permissions_by_method = {
        "GET": ("can_view_doctors",),
        "POST": ("can_create_doctors",),
        "PATCH": ("can_edit_doctors",),
    }

    def get_object(self, user):
        return get_object_or_404(
            DoctorProfile.objects.select_related(
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

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

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
