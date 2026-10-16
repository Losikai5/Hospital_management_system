# Roles & Permissions System Documentation

## Overview

This project implements a Django REST Framework (DRF) based RBAC system with institution-scoped permissions. The authorization logic combines role-based permissions (templates/bundles) with direct per-user permissions, and includes institution ownership bypass, superuser bypass, and sync mechanisms to propagate role changes to users.

**Key components:**
- Users app (`backend/users/`) contains models, services, serializers, views for roles/permissions
- Custom decorator `permission_required` in `backend/utilities/helpers.py` for function-based view protection
- Institution-scoped permissions via `UserPermission.institution` and role-institution scoping
- Role-permission sync service (`sync_permissions_from_roles`) propagates role changes to user permissions

---

## Data model

### Core models (users/models.py)

**CustomUser** (`backend/users/models.py:86`) - Extends `AbstractBaseUser`, `PermissionsMixin`, `SoftDeletableTimeStampedModel`
- Fields: `email`, `username`, `fullname`, `phone_number`, `is_staff`, `is_email_verified`, `is_password_verified`, `gender`, `welcome_email_sent`, `user_type`, `permissions` (JSONField, default list), `session_id`, `profile_picture`
- Manager: `CustomUserManager` (`backend/users/models.py:16`)
- Special methods:
  - `get_token(selected_institution=None)` (`backend/users/models.py:138-175`) - generates JWT with institution claim and session
  - `get_institution_permissions(institution=None)` (`backend/users/models.py:177-199`) - returns set of permission codes from UserPermission for given institution
  - `has_permission(perm_name, institution=None)` (`backend/users/models.py:187-206`) - effective permission check
  - `has_perm(perm, obj=None)` (`backend/users/models.py:208-212`) - Django permission API override
  - `has_perms(perm_list, obj=None)` (`backend/users/models.py:214-215`)
  - `get_group_permissions(obj=None)` (`backend/users/models.py:217-218`)

**PermissionCategory** (`backend/users/models.py:266-281`) - Categorizes permissions
- Fields: `permission_category_name`, `permission_category_description`
- Unique constraint on active (`deleted_at__isnull=True`) `permission_category_name` (`backend/users/models.py:273-281`)

**Permission** (`backend/users/models.py:283-311`) - Defines individual permission
- Fields: `permission_code`, `permission_name`, `permission_description`, `category` (FK to PermissionCategory)
- Unique constraints: active `permission_code` and active `permission_name` (`backend/users/models.py:294-311`)
- Soft-deletable via custom delete method setting `deleted_at` (`backend/users/models.py:308-311`)

**Role** (`backend/users/models.py:313-326`) - Role definition, institution-scoped
- Fields: `name`, `description`, `institution` (FK to Institution, nullable - can be global or institution-scoped) (`backend/users/models.py:316-326`)
- Note: institution FK added in migration 0010 (`backend/users/migrations/0010_role_institution_userpermission_institution_and_more.py`)

**RolePermission** (`backend/users/models.py:328-357`) - M2M through linking roles to permissions (role's permission bundle)
- Fields: `role` (FK, related_name="permissions"), `permission` (FK, related_name="roles")
- On save/delete, triggers `_trigger_role_sync()` (`backend/users/models.py:341-357`) which calls `sync_permissions_from_roles()` for all users assigned this role (via UserRole)
- This means role permission changes propagate to users holding that role automatically (live sync on RolePermission change)

**UserPermission** (`backend/users/models.py:358-377`) - Direct per-user permissions (authoritative)
- Fields: `user` (FK), `permission` (FK), `institution` (FK, nullable) (`backend/users/models.py:360-377`)
- Institution-scoped (migration 0010 adds institution FK)
- Represents effective permissions granted directly to user (in addition to role-derived permissions which are synced into UserPermission table)

**UserRole** (`backend/users/models.py:379-396`) - M2M through linking users to roles
- Fields: `user` (FK, related_name="user_roles"), `role` (FK, related_name="user_roles"), `institution` (FK, nullable) (`backend/users/models.py:383-396`)
- Links users to roles with optional institution scope

### Relationships summary
- User ↔ Role: many-to-many via `UserRole` (user.user_roles, role.user_roles)
- Role ↔ Permission: many-to-many via `RolePermission` (role.permissions, permission.roles)
- User ↔ Permission: many-to-many via `UserPermission` (stored per-user, institution-scoped)
- User has Profile (OneToOne) and ProfileInstitution (through) linking to institutions
- Institution ownership: `Institution.institution_owner` links to user; also ProfileInstitution tracks membership

### Constraints/uniqueness
- PermissionCategory: unique active name (`backend/users/models.py:273-281`)
- Permission: unique active `permission_code` and `permission_name` (`backend/users/models.py:294-311`)
- ProfileInstitution: unique_together (profile, institution) (`backend/users/models.py:262-264`)

### Seeding/fixtures
- Fixtures directory: `backend/users/fixtures/` exists (`backend/users/fixtures/` - see contents)
- Also see system configuration docs: `backend/system/system_configuration.md`

---

## Effective permissions

### Computation
Effective permissions come from `User.get_institution_permissions(institution=None)` (`backend/users/models.py:177-199`) which returns a set of `permission__permission_code` values from `UserPermission` where `deleted_at__isnull=True` and `permission__deleted_at__isnull=True`, filtered by institution if provided.

The check `has_permission(perm_name, institution=None)` (`backend/users/models.py:187-206`):
1. If user is active AND is superuser (`self.is_active and self.is_superuser`): returns True (superuser bypass)
2. Institution ownership bypass: if institution provided and user's profile institutions include the institution AND the institution's owner is this user (`profile.institution.filter(institution_owner=self).exists()` in context) - returns True. Specifically checks if user is owner of that institution via profile relation pattern (`backend/users/models.py:201-205`). Also institution owner status is checked.
3. Otherwise returns `perm_name in perms` where perms = `get_institution_permissions(institution)`

Django's permission API methods also honor superuser bypass:
- `has_perm(perm, obj=None)` (`backend/users/models.py:208-212`): superuser bypass, otherwise checks permission for institution derived from obj (if obj is Institution)
- `has_perms(perm_list, obj=None)` (`backend/users/models.py:214-215`)
- `get_group_permissions(obj=None)` (`backend/users/models.py:217-218`) delegates to `get_institution_permissions`

**Source of truth:** Effective permission codes are stored in the `UserPermission` table (per (user, permission, institution), soft-deletable). Role grants are materialized/synced into UserPermission rows.


### Bypass rules
1. Superuser bypass: `is_active and is_superuser` → True for `has_permission`/`has_perm` (`backend/users/models.py:190, 209`)
2. Institution owner bypass: if user is the institution owner (checked via profile.institution relation to institution where `institution_owner=self`), returns True (`backend/users/models.py:201-205`)

### Role vs direct permissions & sync behavior

**Live propagation on role changes:** When `RolePermission` is saved or deleted, `_trigger_role_sync()` is called (`backend/users/models.py:341-357`). This finds all users with `UserRole` linking to that role (active, for same role context) and calls `sync_permissions_from_roles(user)` for each affected user. So if a role's permissions change, existing users holding that role get their UserPermission rows updated automatically (added/removed as needed).

**Sync logic (`sync_permissions_from_roles` in `backend/users/services.py:4-216`):**
- Takes `user` and optional `institution`. If no institution, syncs across all institutions the user belongs to (via profile.institution) (`backend/users/services.py:30-58`)
- For each institution: computes `active_role_permission_ids` = all permission_ids granted by any active role the user has in that institution (via UserRole + Role + RolePermission, all active/deleted_at null, role belongs to same institution) (`backend/users/services.py:61-90`)
- Compares to `current_user_permission_ids` = current UserPermission rows for (user, institution) (`backend/users/services.py:92-107`)
- Calculates deltas: add what’s in role grants but missing; remove what’s in current but not in any role grant (`backend/users/services.py:109-133`)
- Creates missing UserPermission rows (`bulk_create` with ignore_conflicts) and soft-deletes (calls `.delete()`) stale ones (`backend/users/services.py:135-182`)
- Returns; also has helper `apply_role_permission_delta()` for explicit propagation with specific granted/revoked IDs (`backend/users/services.py:258-328`)

**Key observations:**
- UserPermission table is the materialized store (not just computed on-the-fly from roles in most paths) - `has_permission` reads from UserPermission via `get_institution_permissions`. Role changes sync into UserPermission.
- So roles are "live templates" - edits to role permissions propagate to existing users automatically (via RolePermission save/delete triggering sync). This differs from a model where role changes don’t retroactively affect users unless explicitly reapplied.
- Direct per-user permissions: UserPermission rows can exist independently. When syncing, permissions that are granted by some role remain; permissions that exist in UserPermission but are NOT granted by any active role the user holds in that institution are removed (deleted). That means direct grants that are not backed by any role assignment in that institution will be cleaned up during sync? See line 109-182: `permission_ids_to_remove = current_user_permission_ids - active_role_permission_ids` → deletes those UserPermission rows. So direct per-user permissions not covered by role grants can be lost on sync. Also there is `is_manual` field mentioned in migrations (`0007_userpermission_is_manual.py`, then removed in 0008) - suggests there may have been concept of manual vs role-derived permissions; currently not present in final model.

**Grant/revoke helpers (`backend/users/services.py:184-256`):**
- `get_users_with_permission(permission_code, institution=None)` - finds users with UserPermission having that code
- `grant_permission_to_user(user, permission_id, institution)` - get_or_create UserPermission
- `revoke_permission_from_user(user, permission_id, institution, exclude_role_id=None)` - only deletes if no other active role still grants it (checks RolePermission via active UserRole for that user/institution/permission). If another role grants it, does not revoke.
- `apply_role_permission_delta(role, granted_ids=None, revoked_ids=None)` - explicit delta application across users holding the role

**Task-based propagation:** In serializers, when role permissions change, they enqueue `apply_role_permission_delta_task` (Celery task) on transaction commit (`backend/users/serializers.py:638-657`, also see tasks.py). Task calls `apply_role_permission_delta`.

---

## Backend enforcement

### View protection decorator
`permission_required(permission_code)` defined in `backend/utilities/helpers.py:667-695`:
```python
def permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            if not request.user.has_permission(permission_code):
                raise PermissionDenied("You dont have the permission to proceed")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
```
- Used as `@method_decorator(permission_required("..."))` on class-based views/methods (Django method_decorator). Examples in `backend/users/views.py`: e.g. `can_create_users` (127), `can_view_users` (193, 318, 363), `can_edit_users` (381), `can_delete_users` (416), role/permission management endpoints (720+).

### DRF permission classes
- Standard DRF permissions used: `permissions.IsAuthenticated` appears (e.g. `backend/users/views.py:631` class `CheckInstitutionUserAPIView` sets `permission_classes = [permissions.IsAuthenticated]`)
- Custom authentication classes exist (`backend/users/authentication.py`) including `ExternalSystemAuthentication`, `EmailBackend`, `JWTAuthentication` (custom extensions) - but no obvious custom DRF Permission class named with "required_permissions" pattern found in codebase (the grep for "required_permissions" only matched DRF source in venv). Enforcement is primarily via decorator `permission_required`.

### Notable permission-protected endpoints (users/views.py examples)

From scanning users/views.py with decorators:
- User management: create/view/edit/delete users use codes like `can_create_users`, `can_view_users`, `can_edit_users`, `can_delete_users` (lines ~127,193,318,363,381,416)
- Staff roles: `can_edit_staff_roles`, `can_view_staff_roles` (720,743,783,795,813)
- User permissions: `can_edit_user_permissions`, `can_view_user_permissions`, `can_delete_user_permissions` (831,853,868,880,896,911,930,950)
- Also many other endpoints across views use the same decorator pattern

Permission/Role CRUD APIs (also in users/views.py):
- `PermissionCategoryListAPIView` (823+), `PermissionCategoryDetailAPIView` (862+), `PermissionListAPIView` (903+), `PermissionDetailAPIView` (944+), `PermissionDestroyAPIView` (978+) etc. - these manage Permission/Category models (serializer usage shown)
- Role management views also present (e.g. around line 720+ area shows role edit/view with permission checks)

### How mapping works
Protection is per-endpoint via specific permission code strings passed to decorator. No method/action-level mapping dict like `required_permissions_by_method` seen in this codebase - it's explicit per view/method decoration.

---

## Frontend gating

The frontend is in `backend/templates/` and `frontend/` directories? Let us look:
- `backend/templates/` contains Django templates (activation emails etc.)
- `frontend/` is a separate frontend app (13 entries shown earlier)

Let us search for permission/role usage in frontend.

```bash
grep -rn "hasPermission\|hasRole\|permissions.*role\|user.*permissions" frontend | head -40
```

Also check for how auth/user shape is returned from API.

### Frontend gating

**Auth object shape (frontend types):** `IUser` (`frontend/types/auth.types.ts:65-112`) includes:
- `roles: Role[]` (array, not single string)
- `permissions: string[]` (array of permission codes)
- `is_superuser: boolean`
- Also `permission_ids`, `permission_selections` in some contexts

So user-facing shape has both `roles` array and flat `permissions` array.

**Where user/auth comes from:** Login/refresh/profile endpoints return user data (see backend users views for login - likely returns user with permissions/roles). The frontend reads from Redux store: `store.getState().auth?.user.value` (`frontend/lib/helpers.ts:494-497`).

**Permission helper:** `hasPermission(permissionCode, currentUser?)` (`frontend/lib/helpers.ts:480-511`)
- Checks `userData.is_superuser` first → returns true (honors admin/superuser bypass)
- Gets `userPermissions = userData.permissions ?? []` (flat list of codes)
- Supports single code or array (all must pass for array)
- Falls back to store state if no user passed

**Role helper:** Let us look for hasRole.

**Role handling (frontend):** UI manages roles as objects with `roles` array on user; role assignment/updates handled in forms (see user-form.tsx). No `hasRole` helper function found - permission-based gating is primary via `hasPermission`. The user shape includes `roles` array and flat `permissions` codes.

**UI gating examples:**
- `frontend/app/(main)/users/page.tsx:37-38` uses `hasPermission(PERMISSION_CODES.CAN_EDIT_USERS, user)`, `hasPermission(PERMISSION_CODES.CAN_DELETE_USERS, user)`
- `frontend/app/(main)/users/[baseUuid]/page.tsx:117-126` checks edit/view/reset permissions
- Permission codes defined/constants likely in `frontend/lib/constants` or similar (referenced as `PERMISSION_CODES`)

**Token claims:** Backend JWT sets institution claim in token (see `get_token` in CustomUser adds `current_institution` to refresh/access token) - frontend may read from token; also user object from API includes permissions/roles.

---

## Migration & compatibility

Migrations in `backend/users/migrations/` relevant to roles/permissions:
- `0001_initial.py` - initial schema for CustomUser, PermissionCategory, Permission, Role, RolePermission, UserPermission, UserRole, Profile, ProfileInstitution, OTPModel
- `0003_userpermission_base_uuid_userpermission_created_by_and_more.py` - adds audit fields (base_uuid, created_by, updated_by, deleted_by) and possibly other fields
- `0004_remove_permission_unique_active_permission_code_and_more.py` - constraint changes
- `0005_permission_unique_active_permission_code_and_more.py` - constraint adjustments
- `0007_userpermission_is_manual.py` - adds `is_manual` to UserPermission
- `0008_remove_userpermission_is_manual.py` - removes `is_manual` from UserPermission (reverted)
- `0009_profile_profileinstitution_profile_institution.py` - profile/institution through model changes
- `0010_role_institution_userpermission_institution_and_more.py` - adds `institution` FK to Role, UserPermission, UserRole; adds constraints/indexes

**Backward compatibility:** No obvious shims for older single-role APIs found in codebase scanning. Models support multiple roles (M2M via UserRole). Frontend types show `roles: Role[]` array. No "role" (singular string) legacy field apparent in current models.

---

## Tests

Tests for authorization/roles/permissions: `backend/users/tests.py` (15,476 bytes as seen earlier, `backend/users/tests.py` file exists). Also `backend/system/tests.py`. Let us look inside users tests for relevant cases.

**Tests location/coverage:** 
- `backend/users/tests.py` is essentially empty (just a placeholder TestCase class)
- `backend/system/tests.py` contains serializer tests for System/SystemFeature/SystemFeatureAction
- Other apps have tests (helpdesk/institution/settings/reminders) but no obvious authorization/roles/permissions test coverage visible in quick scan

So test coverage for the roles/permissions system appears minimal/placeholder based on file contents.

---

## Gotchas & known limitations

- **UserPermission is materialized from roles:** `sync_permissions_from_roles` rebuilds UserPermission rows for each institution based on active role grants. Direct permissions not backed by any active role in that institution are removed during sync (`permission_ids_to_remove = current_user_permission_ids - active_role_permission_ids` → deleted). The old `is_manual` field existed then was removed (migrations 0007→0008), suggesting design evolved; current behavior conflates "role-derived" vs "direct" in a way that may wipe direct grants if not assigned via roles. This is important - "per-user permissions (per-user permissions are authoritative)" as stated in the comparison context would differ if sync removes them.
- **Institution scoping is critical:** Many operations filter by institution (Role.institution, UserPermission.institution, UserRole.institution). Bypass rules also consider institution ownership. When institution is None in some contexts, behavior may span all institutions (sync does this when institution not passed).
- **Live sync on RolePermission changes:** `_trigger_role_sync()` runs on every RolePermission save/delete and iterates over all users holding that role. For large user sets this could be expensive; though there's also async task path via serializers on role updates (`apply_role_permission_delta_task`).
- **Owner bypass logic is a bit indirect:** Owner bypass checks `profile.institution.filter(institution_owner=self).exists()` in the context of the institution being checked (`backend/users/models.py:201-205`) - relies on profile-institution membership and institution owner. Correctness depends on profile setup.
- **Superuser bypass applies regardless of institution in has_permission** (`backend/users/models.py:190` returns True if superuser+active; doesn't require institution). Also `has_perm` similar.
- **Permissions stored as JSON on CustomUser?** CustomUser has `permissions = models.JSONField(default=list)` (`backend/users/models.py:119`) - this is a flat list on the user model itself; unclear if actively used vs UserPermission table. The effective source is UserPermission via `get_institution_permissions`. Could be legacy or cached representation.
- **Soft deletes everywhere:** Most models use SoftDeletableTimeStampedModel; sync checks `deleted_at__isnull=True` consistently.
- **No DRF custom permission class for required_permissions by method** - enforcement is via decorator only. The example from comparison mentioned "custom DRF permission class using `required_permissions` / `required_permissions_by_method`" - this project does NOT implement that; it uses `@permission_required` decorator.
- **Tests for RBAC are minimal/empty** (users/tests.py is stub). Hard to verify behavior without tests.

---

## Comparison to our design

Comparing to the provided design description:

| Aspect | This project (other repo) | Our design (stated) | Match? |
|---|---|---|---|
| User roles | M2M via `UserRole` (multiple roles supported). User has `roles` array in API shape and `user_roles` relation. | User has flat M2M set of `roles` and M2M set of per-user `permissions` | Mostly matches on roles M2M; also has per-user permissions table. |
| Per-user permissions | Stored as `UserPermission` rows (per user, permission, institution). Also CustomUser has JSON `permissions` field. Effective permissions come from UserPermission table. | Per-user `permissions` M2M authoritative | Matches in structure (UserPermission model). But authority is impacted by sync behavior (see below). |
| Role permission bundle | `Role` has M2M via `RolePermission` - bundle/template. | Role has M2M `permissions` bundle used as template/default | Matches. |
| Role edit retroactivity | RolePermission save/delete triggers `_trigger_role_sync()` which updates all users holding that role (adds/removes UserPermission rows). Also async task on serializer updates. So changes propagate to existing users automatically. | Role edits do NOT retroactively change users except via explicit "sync/apply role defaults to users" action | **Differs** - this project propagates automatically on role changes. |
| Admin/superuser | Bypass if `is_active and is_superuser` (uses PermissionsMixin fields). Also institution owner bypass. | No `is_superuser` field (PermissionsMixin removed); ADMIN-role bypass instead | **Differs** - uses Django's `is_superuser` (PermissionsMixin present). |
| Copy on role assignment | When syncing/applying role deltas, permissions are materialized into UserPermission. The `get_or_create_default_role_with_permissions` helper copies defaults on creation; role assignment creates UserRole - sync then propagates. Not explicitly "copy at assignment time then editable independently" - sync keeps them in sync with role grants. | Assigning role at creation copies role's active permissions into user's permissions as default (overridable) | Partial - materialized via sync; but sync removes permissions not granted by any role. |
| Effective permissions source | `UserPermission` table (materialized). `has_permission` reads from it. | User's own `permissions` + ADMIN-role bypass | Similar materialized approach. Bypass differs (superuser vs admin role). |
| Enforcement | `@permission_required(permission_code)` decorator (function-based) checking `request.user.has_permission()`. No DRF custom class with `required_permissions_by_method` found. | Custom DRF permission class using `required_permissions` / `required_permissions_by_method` | **Differs** - decorator-based, not the described DRF permission class. |
| Multiple roles | Yes - UserRole M2M, and sync considers all active roles user has in institution. | Supported (flat M2M) | Matches. |

**Notable differences from stated design:**
1. This project uses `is_superuser` (Django auth) as admin bypass; stated design removed PermissionsMixin and uses ADMIN-role bypass.
2. Role permission changes propagate automatically to existing users (live sync) - stated design says they do NOT retroactively change users except explicit action.
3. Enforcement is decorator-based (`permission_required`) not custom DRF permission class with method/action mapping.
4. Sync logic removes UserPermission rows not backed by any active role - meaning "direct per-user permissions" that aren't covered by role grants get deleted on sync events. That undermines "per-user permissions are authoritative" if sync runs.
