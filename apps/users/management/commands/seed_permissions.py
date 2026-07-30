from django.core.management.base import BaseCommand, CommandError
import json
from pathlib import Path
from apps.users.models import Permission, Role

class Command(BaseCommand):
    help = 'Seeds the database with initial permissions.'

    def handle(self, *args, **options):
        fixture_path = Path(__file__).resolve().parents[2]/"fixtures"/"role.json"
        with fixture_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        roles = data.get("roles", [])
        for role_data in roles:
            role, created = Role.objects.update_or_create(
                code=role_data["code"],
                defaults={
                    "name": role_data["name"],
                    "description": role_data.get("description", ""),
                    "is_active": role_data.get("is_active", True),
                    "is_system": role_data.get("is_system", False),
                },
            )

            action = "Created" if created else "Updated"

            self.stdout.write(
                self.style.SUCCESS(f"{action} role: {role.code}")
            )
        permission_path = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "permission.json"
        )

        with permission_path.open("r", encoding="utf-8") as file:
            permission_groups = json.load(file)

        for group_name, permissions in permission_groups.items():
            for permission_data in permissions:
                permission, created = Permission.objects.update_or_create(
                    code=permission_data["code"],
                    defaults={
                        "name": permission_data["name"],
                        "description": permission_data.get("description", ""),
                        "is_active": permission_data.get("is_active", True),
                    },
                )

                action = "Created" if created else "Updated"

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{action} permission: {permission.code}"
                    )
                )
        role_permission_path = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "role_permission.json"
        )

        with role_permission_path.open("r", encoding="utf-8") as file:
            role_permission_data = json.load(file)

        for role_code, assignment_data in role_permission_data.items():
            try:
                role = Role.objects.get(code=role_code)
            except Role.DoesNotExist as error:
                raise CommandError(
                    f"Role '{role_code}' does not exist."
                ) from error

            if assignment_data.get("all_permissions", False):
                assigned_permissions = Permission.objects.filter(
                    is_active=True
                )
            else:
                permission_codes = assignment_data.get("permissions", [])
                assigned_permissions = Permission.objects.filter(
                    code__in=permission_codes,
                    is_active=True,
                )
                found_codes = set(
                    assigned_permissions.values_list("code", flat=True)
                )
                missing_codes = set(permission_codes) - found_codes

                if missing_codes:
                    missing = ", ".join(sorted(missing_codes))
                    raise CommandError(
                        f"Unknown permissions for role '{role_code}': {missing}"
                    )

            role.permissions.set(assigned_permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Assigned {assigned_permissions.count()} "
                    f"permissions to role: {role.code}"
                )
            )
