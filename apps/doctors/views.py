from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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


class DoctorDirectoryView(DoctorDirectoryBaseView):
    def get(self, request):
        serializer = self.serializer_class(
            self.get_queryset(),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)


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
