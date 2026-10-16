# Single-Tenant RBAC

> **Scope: single tenant.** This document describes a RBAC system for **one
> organization only**. There is **no** `institution`/tenant concept anywhere:
> no tenant FK, no tenant parameter, no per-tenant scoping, no tenant loop.
> `Role`, `Permission`, and every user permission are global to the whole
> installation. Any "institution"/"tenant" wording below is background only —
> it explains where the pattern came from, never something to implement.

## 1. Concept: the six pillars

| # | Pillar | Model(s) | Purpose |
|---|--------|----------|---------|
| 1 | Permission catalog | `Permission` | The static vocabulary of "what can be done" (`code`). |
| 2 | Roles | `Role` | Named bundles admins manage. System roles (`is_system`) ship with permissions. |
| 3 | Role→Permission | `RolePermission` | M2M join defining what a role grants. |
| 4 | User↔Role | `CustomUser.roles` (plain M2M) | Which roles a user holds. |
| 5 | Effective permissions (keystone) | `UserPermission` (through-model) | Flattened cache of what the user *actually* has. Read at request time. |
| 6 | Enforcement | `has_permission()` + helper | Single gate for access checks. |

**Flow:** catalog → roles bundle → role assigned to user → sync flattens into `UserPermission` → `has_permission()` reads it.

**Single-tenant rules:** `Role` and `Permission` are global; the sync function is
`sync_role_permissions(user)`; the check is `has_permission(perm)`. No `institution`
argument or scoping appears in any signature, query, or model.

## 2. Data model

```python
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Role(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)   # system roles are not editable/deletable
    permissions = models.ManyToManyField(
        Permission, through="RolePermission", related_name="roles", blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="permission_assignments",
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_assignments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"], name="unique_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.role.code}: {self.permission.code}"


class UserPermission(models.Model):
    """Effective permissions. Keystone of the system.

    source=ROLE   -> owned by the sync engine; added/removed automatically.
    source=DIRECT -> manually granted by an owner; sync NEVER touches these.
    """
    SOURCE_ROLE = "ROLE"
    SOURCE_DIRECT = "DIRECT"
    SOURCE_CHOICES = [
        (SOURCE_ROLE, "Role-derived"),
        (SOURCE_DIRECT, "Direct grant"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="user_permissions",
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="user_grants",
    )
    source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default=SOURCE_ROLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "permission"], name="unique_user_permission",
            )
        ]

    def __str__(self):
        return f"{self.user_id}: {self.permission.code} ({self.source})"
```

### CustomUser (relevant parts)

```python
class CustomUserManager(BaseUserManager):
    def _assign_roles(self, user, roles):
        if not isinstance(roles, (list, tuple, set)):
            roles = [roles]
        user.roles.set(roles)                 # triggers signal -> async sync
        sync_role_permissions(user)           # sync copy for immediate effect

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))

        roles = extra_fields.pop("roles", None)
        direct_permissions = extra_fields.pop("permissions", None)

        if not roles:
            raise ValueError(_("At least one role must be assigned to the user"))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        self._assign_roles(user, roles)

        # Owner-supplied extras are DIRECT so later role changes can't wipe them.
        if direct_permissions:
            for perm in direct_permissions:
                UserPermission.objects.update_or_create(
                    user=user, permission=perm,
                    defaults={"source": UserPermission.SOURCE_DIRECT},
                )
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)

        try:
            admin_role = Role.objects.get(code="ADMIN", is_active=True)
        except Role.DoesNotExist as error:
            raise ValueError(_("The ADMIN role must be created first.")) from error

        extra_fields["roles"] = [admin_role]
        extra_fields["permissions"] = list(Permission.objects.filter(is_active=True))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")

    roles = models.ManyToManyField(Role, related_name="users", blank=True)
    permissions = models.ManyToManyField(
        Permission, through="UserPermission", related_name="users", blank=True,
    )

    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        blank=True, null=True,
    )
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    @property
    def role_codes(self):
        return list(self.roles.filter(is_active=True).values_list("code", flat=True))

    def has_role(self, role_code):
        return self.roles.filter(code=role_code, is_active=True).exists()

    def get_permission_codes(self):
        return list(
            self.permissions.filter(is_active=True)
            .order_by("code").values_list("code", flat=True)
        )

    def has_permission(self, permission_code):
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if self.has_role("ADMIN"):
            return True
        return self.permissions.filter(code=permission_code, is_active=True).exists()

    # --- Django admin hooks (optional; delegate to has_permission if you don't use admin) ---
    def has_perm(self, perm, obj=None):
        return self.is_active and (self.is_superuser or self.has_role("ADMIN"))

    def has_module_perms(self, app_label):
        return self.is_active and (self.is_superuser or self.has_role("ADMIN"))

    def __str__(self):
        return f"{self.email} ({', '.join(self.role_codes)})"

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]
```

## 3. Source rule (role vs. direct)

- Every `UserPermission` row is tagged `ROLE` or `DIRECT`.
- **Sync only diffs `ROLE` rows.** `DIRECT` rows are invisible to it and survive role changes.
- A permission can exist only **once per user** (unique constraint). If a permission is both
  role-derived and directly granted, the row is `DIRECT` (direct wins → it persists).
- Granting directly promotes an existing `ROLE` row to `DIRECT`.
- Revoking a direct grant deletes the row, then re-derives from roles.

## 4. Sync engine — `services.py`

```python
from django.db import transaction
from .models import RolePermission, UserPermission


@transaction.atomic
def sync_role_permissions(user):
    """Recompute the ROLE-derived effective permissions for one user."""
    if not user.pk:
        return

    role_perm_ids = set(
        RolePermission.objects.filter(
            role__users=user,
            role__is_active=True,
            permission__is_active=True,
        ).values_list("permission_id", flat=True)
    )

    current_role_ids = set(
        UserPermission.objects.filter(
            user=user, source=UserPermission.SOURCE_ROLE,
        ).values_list("permission_id", flat=True)
    )

    direct_ids = set(
        UserPermission.objects.filter(
            user=user, source=UserPermission.SOURCE_DIRECT,
        ).values_list("permission_id", flat=True)
    )

    # Direct grants are never managed here, so exclude them.
    desired_role_ids = role_perm_ids - direct_ids

    to_add = desired_role_ids - current_role_ids
    to_remove = current_role_ids - desired_role_ids

    if to_remove:
        UserPermission.objects.filter(
            user=user,
            source=UserPermission.SOURCE_ROLE,
            permission_id__in=to_remove,
        ).delete()

    if to_add:
        UserPermission.objects.bulk_create(
            [
                UserPermission(
                    user=user,
                    permission_id=pid,
                    source=UserPermission.SOURCE_ROLE,
                )
                for pid in to_add
            ],
            ignore_conflicts=True,   # bulk_create bypasses signals by design
        )


@transaction.atomic
def grant_direct_permission(user, permission):
    """Owner manually adds a permission that outlives role changes."""
    UserPermission.objects.update_or_create(
        user=user, permission=permission,
        defaults={"source": UserPermission.SOURCE_DIRECT},
    )


@transaction.atomic
def revoke_direct_permission(user, permission):
    UserPermission.objects.filter(
        user=user, permission=permission, source=UserPermission.SOURCE_DIRECT,
    ).delete()
    sync_role_permissions(user)   # re-add if a role still grants it


def sync_users_for_role(role):
    for user in role.users.all():
        sync_role_permissions(user)
```

## 5. Async propagation — Celery + signals

`tasks.py`:

```python
from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_user_permissions_task(self, user_id):
    from django.contrib.auth import get_user_model
    from .services import sync_role_permissions
    try:
        user = get_user_model().objects.get(pk=user_id)
        sync_role_permissions(user)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_role_users_task(self, role_id):
    from .models import Role
    from .services import sync_role_permissions
    try:
        role = Role.objects.get(pk=role_id)
        for user in role.users.all():
            sync_role_permissions(user)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_users_task(self, user_ids):
    from django.contrib.auth import get_user_model
    from .services import sync_role_permissions
    try:
        qs = get_user_model().objects.filter(pk__in=list(user_ids))
        for user in qs:
            sync_role_permissions(user)
    except Exception as exc:
        raise self.retry(exc=exc)
```

`signals.py` (register in `AppConfig.ready()`):

```python
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import CustomUser, Role, RolePermission
from .tasks import (
    sync_user_permissions_task, sync_role_users_task, sync_users_task,
)


@receiver(m2m_changed, sender=CustomUser.roles.through)
def on_user_roles_changed(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        transaction.on_commit(
            lambda: sync_user_permissions_task.delay(instance.pk)
        )


@receiver(post_save, sender=RolePermission)
def on_role_permission_saved(sender, instance, **kwargs):
    transaction.on_commit(
        lambda: sync_role_users_task.delay(instance.role_id)
    )


@receiver(post_delete, sender=RolePermission)
def on_role_permission_deleted(sender, instance, **kwargs):
    role_id = instance.role_id          # capture before the row is gone
    transaction.on_commit(
        lambda: sync_role_users_task.delay(role_id)
    )


@receiver(pre_delete, sender=Role)
def on_role_pre_delete(sender, instance, **kwargs):
    # cascade will remove the through rows, so capture users BEFORE delete
    user_ids = list(instance.users.values_list("pk", flat=True))
    if user_ids:
        transaction.on_commit(lambda: sync_users_task.delay(user_ids))
```

> **Critical gotcha:** `bulk_create`, `queryset.update()`, and `queryset.delete()`
> **do not fire signals**. Anywhere you use them for roles/permissions, enqueue the
> task explicitly (same pattern the original used after `RolePermission.bulk_create`).

## 6. Enforcement

Decorator:

```python
from functools import wraps
from django.core.exceptions import PermissionDenied


def permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not getattr(request.user, "is_authenticated", False):
                raise PermissionDenied("Authentication required")
            if not request.user.has_permission(permission_code):
                raise PermissionDenied("You don't have permission to proceed")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
```

DRF permission class (optional):

```python
from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    def has_permission(self, request, view):
        required = getattr(view, "required_permissions", None)
        if not required:
            return True
        if isinstance(required, str):
            required = [required]
        user = request.user
        return bool(
            getattr(user, "is_authenticated", False)
            and all(user.has_permission(p) for p in required)
        )
```

Usage:

```python
@permission_required("can_view_staff_roles")
def list_roles(request): ...

class RoleListView(APIView):
    required_permissions = ["can_view_staff_roles"]
    permission_classes = [HasPermission]
```

## 7. Seeding

`create_superuser` needs an `ADMIN` role to exist. Seed permissions + system roles
via a management command run after migrate:

```python
# management/commands/seed_rbac.py
import json, os
from django.conf import settings
from django.core.management.base import BaseCommand
from rbac.models import Permission, Role, RolePermission


class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. Upsert permissions from fixture
        path = os.path.join(settings.BASE_DIR, "rbac", "fixtures", "permissions.json")
        data = json.load(open(path))          # {"Category": [{"code","name","description"}]}
        valid = set()
        for _cat, perms in data.items():
            for p in perms:
                Permission.objects.update_or_create(
                    code=p["code"],
                    defaults={"name": p["name"], "description": p.get("description", "")},
                )
                valid.add(p["code"])
        Permission.objects.exclude(code__in=valid).update(is_active=False)

        # 2. System ADMIN role -> all permissions
        admin, _ = Role.objects.update_or_create(
            code="ADMIN", defaults={"name": "Administrator", "is_system": True},
        )
        admin_ids = set(Permission.objects.filter(is_active=True).values_list("id", flat=True))
        existing = set(admin.permission_assignments.values_list("permission_id", flat=True))
        RolePermission.objects.bulk_create(
            [RolePermission(role=admin, permission_id=pid)
             for pid in admin_ids - existing],
            ignore_conflicts=True,
        )
        self.stdout.write(self.style.SUCCESS("RBAC seeded."))
```

## 8. Background only: how this differs from the multi-tenant source

> Reference for understanding the pattern's origin. **The left column does not
> describe anything you build here** — your system implements only the right column,
> with no tenant concept at all.

| Original (multi-tenant) | Single-tenant port |
|---|---|
| `Role.institution` FK | **removed** — global role |
| `UserRole(user, role, institution)` | `CustomUser.roles` plain M2M |
| `UserPermission(user, permission, institution)` | `UserPermission(user, permission, source)` |
| `sync_permissions_from_roles(user, institution)` | `sync_role_permissions(user)` |
| `apply_role_permission_delta(role, ...)` | `sync_role_users_task(role_id)` |
| `apply_role_permission_delta_task` (Celery) | `sync_user_permissions_task` / `sync_role_users_task` |
| `has_permission(perm, institution)` | `has_permission(perm)` |
| `get_institution_permissions()` | `permission_codes` / direct `self.permissions` query |
| institution-owner bypass | optional: check `is_staff` / owner flag instead |
| `deleted_at` soft delete | `is_active` boolean (filtered everywhere) |
| `RolePermission.save/delete` → sync | signals + Celery tasks (section 5) |

## 9. Gotchas / rules to keep

1. **`bulk_create`/`update`/`delete` bypass signals** — enqueue tasks manually.
2. **Sync only touches `source=ROLE` rows** — this is what lets the owner add extras that persist.
3. **Unique `(user, permission)`** — one row per permission; direct grant promotes ROLE→DIRECT.
4. **Always filter `is_active`** on `Role`, `Permission`, and `UserPermission` reads.
5. **Bypasses** in `has_permission`: superuser, then `ADMIN` role, then explicit grant.
6. **Prefer deactivating roles** (`is_active=False`) over hard delete. If you hard-delete,
   the `pre_delete` signal (section 5) must capture users before cascade.
7. **Performance:** prefetch `roles`/`permissions` on hot paths; `has_permission` hits this
   cache table (~1 indexed query) and never traverses role→permission at request time.
8. **Determinism:** call `sync_role_permissions(user)` synchronously right after role
   assignment (as in `create_user`); let Celery handle subsequent changes.

## 10. Design rationale (why this pattern exists)

Three constraints force this design. Understanding them keeps you from "simplifying"
it into something that silently breaks.

### 10.1 Why materialize `UserPermission` (instead of checking roles live)

Roles are **authored rarely** but **enforced on every request**. Deriving effective
permissions live means joining `UserRole → Role → RolePermission → Permission` and
re-running the category/`select_all` resolution on every check. So:

- **Cheap enforcement:** `has_permission` becomes one indexed lookup on a flat table
  instead of a multi-join derivation per call.
- **Complex authoring, simple runtime:** the messy part (select-all, per-category
  exclusions, dedupe) is computed once at sync time and stored flattened.
- **Queryable + auditable:** a table can be filtered in SQL
  (`get_users_with_permission`), carries `created_by/updated_by`, and supports
  soft-delete — a computed value or JSON blob cannot.
- **Single merge point:** role-derived permissions and any other grants converge into
  one authoritative set.

### 10.2 Why **diff/reconcile** instead of wipe-and-rebuild

`add = desired - current`, `remove = current - desired`, leave the intersection alone.

- **Async + retries demand idempotency.** Propagation runs in Celery with retries and
  can fire more than once (signal + explicit call) or run late. A diff **re-reads the
  true desired state** and converges no matter how often it runs. An imperative
  "add these IDs" would double-apply; a change-set captured at edit time could be
  stale by run time.
- **Full replace destroys data.** Delete-all-then-recreate would wipe direct grants,
  churn PKs and `created_at/created_by` (breaking audit + FK references), and be
  expensive when a role has hundreds of permissions but only one changed.
- **Minimal writes:** only the delta is touched, so unaffected rows and their audit
  fields stay intact. (This is why the original has a separate
  `apply_role_permission_delta` path.)
- **Soft-delete safety:** because `.delete()` soft-deletes, diffing against the live
  set (filtering `deleted_at__isnull=True`) avoids colliding with tombstoned rows.

### 10.3 Single unscoped compute

In a single-tenant system every role and user belongs to the one installation, so
there is exactly **one** "desired" set per user. `sync_role_permissions(user)` is a
single unscoped pass — no tenant filtering, no per-institution loop.

### 10.4 Direct grants must survive role changes

A naive sync only knows **role-derived** permissions, so `current - desired` would
also delete any **manually granted** permission. This port prevents that with
`source=ROLE/DIRECT`: sync diffs only `source=ROLE` rows, so owner-granted
(`DIRECT`) permissions survive role changes.

**One line:** *materialize because enforcement must be cheap; reconcile (diff) because
propagation is asynchronous, retryable, and must preserve history and manual grants.*

---

## 11. Future reference: evolving this into multi-tenant (NOT built now)

> Everything above is the single-tenant system you ship today. This section is a
> **forward-looking note only** for if/when you ever need multiple organizations.
> None of it is implemented, and adding it later should be a deliberate decision,
> not a default.

### 11.1 What actually changes

Multi-tenancy means the **same models gain a tenant dimension**. The pattern does not
change — only its scope:

| Concern | Single tenant (now) | Multi-tenant (future) |
|---|---|---|
| Tenant model | none | `Institution` / `Tenant` |
| `Role` | global | scoped: `Role.institution` FK |
| User↔Role | `CustomUser.roles` M2M | through-model `UserRole(user, role, institution)` |
| Effective perms | `UserPermission(user, permission, source)` | `+ institution` FK |
| Sync | `sync_role_permissions(user)` | `sync_role_permissions(user, institution)` — loop per tenant |
| Check | `has_permission(perm)` | `has_permission(perm, institution)` |
| Unique constraints | `(user, permission)` | `(user, permission, institution)` |

### 11.2 The one structural gotcha

A plain `CustomUser.roles` M2M **cannot** carry a tenant column. Multi-tenant forces
you to convert it into a **through-model** (`UserRole` with `institution`), exactly
as the original source did. `UserPermission` likewise needs the added `institution`
FK and its unique constraint widened to include it. Plan the migration before there
is production data, or write a data migration that backfills a default tenant.

### 11.3 Why the original added a per-tenant loop (and why you won't yet)

The source looped over "all institutions the user belongs to" because the *desired*
set differs per tenant and role assignments are per tenant. The reconciliation
identity is identical — `desired - current` / `current - desired` — it's just run
once per tenant instead of once per user.

### 11.4 Tenant resolution

Multi-tenant also needs a way to know **which tenant a request is acting on** — the
source used a JWT claim (`current_institution` in `get_token`) plus a
`get_current_institution_from_request` helper. That request-scoping concern is
entirely absent single-tenant and is the biggest non-model addition you'd take on.

### 11.5 If you ever migrate, keep

- The **materialize + reconcile** core (Section 10) — it scales to tenants unchanged.
- The **`source=ROLE/DIRECT`** idea — direct grants remain tenant-scoped and safe.
- **Signals + Celery propagation** — just include the tenant in the task payload.

And add for the multi-tenant case: tenant isolation tests, and a guard so a role from
tenant A can never grant permissions in tenant B (filter every sync query by
institution, as the original did).

---

## 12. How sync removes old permissions and adds the ones you tick

"Remove what the role came with, add what I ticked" is a **diff**, not a
wipe-and-re-add. It happens at **two levels**.

### Level 1 — the role's own permission set (the ticks in the UI)

Handled in `RoleSerializer` create/update, **not** `sync_role_permissions`.

**a. Resolve the ticks into a target set** (`resolve_role_permission_selection`):
- `select_all_permissions=true` → target = all permissions minus
  `global_excluded_permission_ids`.
- per-category `permission_selections` → for each selection, either the listed
  `permission_ids` or the whole category minus `excluded_permission_ids`.

**b. Compute old vs new:**
```python
# mode "global":     old = all RolePermission for this role
# mode "categories": old = RolePermission for this role,
#                          limited to the categories you touched
to_add    = new_permission_ids - old_permission_ids
to_remove = old_permission_ids - new_permission_ids
```
Key detail: in **categories mode** the old set is restricted to
`selected_category_ids`, so permissions in categories you did **not** touch are
left alone — you only remove "what the role came with" **inside the categories you
edited**.

**c. Apply to `RolePermission`:** delete `to_remove`, `bulk_create` `to_add`.

### Level 2 — propagate the delta to each user's `UserPermission`

After the role's rows change, enqueue a delta task for the role. For every user
holding it:
- **added** → `grant_permission_to_user` → `UserPermission.get_or_create`.
- **removed** → `revoke_permission_from_user`, with the crucial guard:
```python
still_granted = RolePermission.objects.filter(
    role__user_roles__user=user,
    permission_id=permission_id,
    deleted_at__isnull=True,
).exclude(role_id=exclude_role_id)   # ignore the role being edited

if still_granted.exists():
    return                            # another role still grants it -> keep
# else delete the UserPermission row(s)
```
So a permission is pulled from a user **only if no other role of theirs still
grants it**.

### Direct ticks on the user are never touched

If "ticked" means permissions tapped **directly on the user** (not on a role),
those are `source=DIRECT`. Sync subtracts `direct_ids` from the desired role set,
so role edits can never remove your manual grants.

### Your single-tenant port collapses the two levels

No tenant and per-user resync means a role edit just fires the `RolePermission`
signal → `sync_role_users_task(role_id)` → `sync_role_permissions(user)` for each
affected user. That recomputes the **whole** desired set and diffs it. The
"still granted elsewhere?" rule falls out for free: `role_perm_ids` is the union
across **all** the user's roles, so a permission another role grants stays in
`desired` and never lands in `to_remove`.

**One line:** *Level 1 diffs the role's ticks into `RolePermission`; Level 2
propagates that delta to `UserPermission` with an "is it still granted elsewhere?"
guard; the single-tenant port reproduces both with one full resync per user.*
