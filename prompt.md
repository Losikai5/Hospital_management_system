# Prompt: Document this project's Roles & Permissions system

> Copy everything in the fenced block below and paste it into an opencode session running in the other project's repository.

```text
You are working in the repository at the current working directory. I need a clear, accurate report of how THIS project implements roles and permissions. Do NOT change any code — this is a read-only investigation and documentation task. If you touch files, only create the report file described at the end.

## Scope & exclusions (important)

This is a **single-tenant** comparison. Explicitly LEAVE OUT institution scoping and multi-tenancy:
- Do not describe `Institution`/tenant models, institution/tenant foreign keys, or institution-scoped roles/permissions.
- Do not describe institution-owner bypass or any per-institution permission checks.
- If the codebase is multi-tenant, ignore those layers and report only the core user ↔ role ↔ permission model, treating roles and permissions as global.
- Add one short line under Gotchas noting that tenant scoping was intentionally omitted for this comparison.

## What I want to know

Investigate the codebase and explain, in concrete terms:

1. Data model
   - Which models/tables represent users, roles, and permissions? (names, app/paths)
   - What are the relationships (FK vs M2M, through-models, unique constraints)?
   - Can a user hold more than one role? Are permissions attached to roles, to users, or both?
   - Where are roles/permissions defined or seeded (fixtures, migrations, data seeds)?

2. Effective-permission logic (the authorization source of truth)
   - Given a user, how is their set of effective permissions computed? (Report global semantics — ignore any institution/tenant filtering.)
   - Is there any superuser/admin bypass? How is it detected (flag, role code, etc.)? (Exclude institution-owner bypass.)
   - Are roles a live grant or a copied "template/bundle" snapshot? If a role's permissions change later, do existing users' permissions change automatically, only on re-assignment, or never?
   - Where are the helper methods (e.g. has_role / has_permission / get_permission_codes) and what exactly do they check? Cite file:line.

3. Backend enforcement
   - How are endpoints protected? (DRF permission classes, decorators, middleware, custom classes)
   - How does per-method/per-action permission mapping work?
   - List the roles/permissions-related API endpoints (method + path + required permission) and the serializers used.

4. Frontend / client gating
   - How does the client know a user's roles and permissions (login response, profile fetch, token claims)?
   - How are UI elements/nav/routes gated? Is there a hasPermission/hasRole helper and does it honor the admin bypass?
   - What is the user-facing shape of the auth object (e.g. `role` string vs `roles` array)?

5. Migration & compatibility
   - How was the schema introduced (migration files, data migrations, backfills)?
   - Any backward-compatibility shims for older single-role APIs?

6. Tests
   - Which tests cover authorization, and how do they build users/roles? Where are they?

7. Gotchas & known limitations
   - Edge cases, surprising behavior, dead code, or inconsistencies you found.

## Context: how we implemented it here (so you can compare)

For comparison, our system works like this:
- A user has a flat M2M set of `roles` and a M2M set of per-user `permissions` (per-user permissions are authoritative).
- A `Role` also has a M2M `permissions` bundle used as a template/default; role edits do NOT retroactively change users, except via an explicit "sync/apply role defaults to users" action.
- Effective permissions = user's own `permissions` + an ADMIN-role bypass; there is no `is_superuser` field (PermissionsMixin was removed).
- Assigning a role at creation copies that role's active permissions into the user's `permissions` as the default (overridable).
- Enforcement is a custom DRF permission class using `required_permissions` / `required_permissions_by_method`.

Please tell me how the other project matches or differs from the above, and flag anything notable.

## Output requirements

- Write the report to `roles-permissions-review.md` at the repository root.
- Use these section headings, in order: Overview, Data model, Effective permissions, Backend enforcement, Frontend gating, Migration & compatibility, Tests, Gotchas, Comparison to our design.
- Cite specific files and line numbers as `path/to/file.ext:line` throughout. Prefer exact code references over prose.
- Keep the whole report single-tenant: no institution/tenant scoping anywhere.
- Be concise and factual. If something is ambiguous or you cannot determine it, say so explicitly under Gotchas rather than guessing.
- Do not modify application code, dependencies, or configuration.
```
