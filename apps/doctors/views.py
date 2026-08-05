from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from apps.core.permissions import HasCustomPermission

from .models import DoctorProfile, DoctorSchedule, Specialization
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
            visible_queryset = queryset
        else:
            visible_queryset = queryset.filter(
                is_available=True,
                user__is_active=True,
                user__role__is_active=True,
            )

        specialization = self.request.query_params.get("specialization")
        if specialization:
            specialization = specialization.upper()
            if specialization not in Specialization.values:
                raise ValidationError(
                    {"specialization": "Invalid specialization."}
                )
            visible_queryset = visible_queryset.filter(
                specialization=specialization
            )

        is_available = self.request.query_params.get("is_available")
        if is_available is not None:
            normalized_availability = is_available.lower()
            if normalized_availability not in {"true", "false"}:
                raise ValidationError(
                    {"is_available": "Use true or false."}
                )
            visible_queryset = visible_queryset.filter(
                is_available=normalized_availability == "true"
            )

        search = self.request.query_params.get("search")
        if search:
            visible_queryset = visible_queryset.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__email__icontains=search)
            )

        ordering = self.request.query_params.get("ordering", "name")
        ordering_map = {
            "name": ("user__first_name", "user__last_name"),
            "-name": ("-user__first_name", "-user__last_name"),
            "specialization": ("specialization", "user__first_name"),
            "-specialization": ("-specialization", "user__first_name"),
            "consultation_fee": ("consultation_fee", "user__first_name"),
            "-consultation_fee": ("-consultation_fee", "user__first_name"),
            "years_of_experience": ("years_of_experience", "user__first_name"),
            "-years_of_experience": ("-years_of_experience", "user__first_name"),
        }
        if ordering not in ordering_map:
            raise ValidationError({"ordering": "Invalid ordering field."})

        return visible_queryset.order_by(*ordering_map[ordering])


@extend_schema(
    tags=["Doctors"],
    summary="List doctors",
    parameters=[
        OpenApiParameter(
            name="specialization",
            type=str,
            description="Filter by specialization code.",
        ),
        OpenApiParameter(
            name="is_available",
            type=bool,
            description="Filter by availability using true or false.",
        ),
        OpenApiParameter(
            name="search",
            type=str,
            description="Search by doctor name or email.",
        ),
        OpenApiParameter(
            name="ordering",
            type=str,
            description=(
                "Order by name, specialization, consultation_fee or "
                "years_of_experience; prefix with - for descending order."
            ),
        ),
    ],
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

    def can_manage_all_doctors(self):
        return self.request.user.has_permission("can_view_all_doctors")

    def get_doctor_profile(self):
        return get_object_or_404(
            DoctorProfile,
            user=self.request.user,
        )

    def get_queryset(self):
        queryset = DoctorSchedule.objects.select_related(
            "doctor",
            "doctor__user",
        )

        if self.can_manage_all_doctors():
            return queryset

        return queryset.filter(
            doctor=self.get_doctor_profile(),
        )

    def save_serializer(self, serializer):
        try:
            if self.can_manage_all_doctors():
                return serializer.save()

            return serializer.save(
                doctor=self.get_doctor_profile(),
            )
        except IntegrityError as error:
            raise ValidationError(
                {
                    "day_of_week": (
                        "A schedule already exists for this doctor and day."
                    )
                }
            ) from error


@extend_schema_view(
    get=extend_schema(
        tags=["Doctors"],
        summary="List accessible doctor schedules",
        responses={200: DoctorScheduleSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Doctors"],
        summary="Create a doctor schedule",
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
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        self.save_serializer(serializer)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Doctors"],
        summary="Get a doctor schedule",
        responses={200: DoctorScheduleSerializer},
    ),
    patch=extend_schema(
        tags=["Doctors"],
        summary="Update a doctor schedule",
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
        self.save_serializer(serializer)
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Doctors"],
        summary="Get my doctor profile",
        responses={200: DoctorOnboardingSerializer},
    ),
    post=extend_schema(
        tags=["Doctors"],
        summary="Complete doctor onboarding",
        request=DoctorOnboardingSerializer,
        responses={201: DoctorOnboardingSerializer},
    ),
    patch=extend_schema(
        tags=["Doctors"],
        summary="Update my doctor profile",
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
