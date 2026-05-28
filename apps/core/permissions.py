from rest_framework.permissions import BasePermission
from apps.users.models import UserRole


class IsDoctor(BasePermission):
    """Allows access only to users with the DOCTOR role."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.DOCTOR
        )


class IsPatient(BasePermission):
    """Allows access only to users with the PATIENT role."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PATIENT
        )


class IsAdminUser(BasePermission):
    """Allows access only to users with the ADMIN role."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ADMIN
        )


class IsReceptionist(BasePermission):
    """Allows access only to users with the RECEPTIONIST role."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.RECEPTIONIST
        )


class IsAdminOrReceptionist(BasePermission):
    """Allows access to both ADMIN and RECEPTIONIST roles."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]
        )


class IsAppointmentOwner(BasePermission):
    """
    Object-level permission for appointments.
    - Admin and Receptionist can access any appointment
    - Doctor can only access their own appointments
    - Patient can only access their own appointments
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in [UserRole.ADMIN, UserRole.RECEPTIONIST]:
            return True

        if user.role == UserRole.DOCTOR:
            return obj.doctor.user == user

        if user.role == UserRole.PATIENT:
            return obj.patient.user == user

        return False