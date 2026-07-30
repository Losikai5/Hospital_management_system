from rest_framework.permissions import BasePermission


class HasCustomPermission(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        permissions_by_method = getattr(
            view,
            "required_permissions_by_method",
            None,
        )

        if permissions_by_method is not None:
            permission_codes = permissions_by_method.get(request.method)
        else:
            permission_codes = getattr(view, "required_permissions", None)

            if permission_codes is None:
                permission_code = getattr(
                    view,
                    "required_permission",
                    None,
                )
                permission_codes = (
                    (permission_code,)
                    if permission_code
                    else ()
                )
        if isinstance(permission_codes, str):
            permission_codes = (permission_codes,)

        if not permission_codes:
            return False

        return all(
            user.has_permission(permission_code)
            for permission_code in permission_codes
        )


class IsAppointmentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.has_permission("can_view_all_appointments"):
            return True

        if obj.doctor.user_id == user.id:
            return True

        if obj.patient.user_id == user.id:
            return True

        return False
