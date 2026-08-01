"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { UserGroupIcon, MailSend01Icon, PlusSignIcon, PencilEdit01Icon, Delete02Icon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import type { PermissionInfo, RoleDetail } from "@/lib/types";

type Tab = "invitations" | "roles";

const inviteSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  role: z.string().min(1, "Select a role"),
});

type InviteForm = z.infer<typeof inviteSchema>;

const createRoleSchema = z.object({
  code: z
    .string()
    .min(2, "Role code must be at least 2 characters")
    .max(50, "Role code cannot exceed 50 characters")
    .regex(
      /^[A-Za-z0-9_-]+$/,
      "Role code can only contain alphanumeric characters, underscores, and hyphens"
    ),
  name: z.string().min(2, "Role name must be at least 2 characters").max(100, "Role name cannot exceed 100 characters"),
  description: z.string().max(500, "Description cannot exceed 500 characters"),
  permissions: z.array(z.string()),
});

type CreateRoleForm = z.infer<typeof createRoleSchema>;

export default function StaffPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("invitations");
  
  // Data lists
  const [roles, setRoles] = useState<RoleDetail[]>([]);
  const [permissions, setPermissions] = useState<PermissionInfo[]>([]);
  
  // States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [creatingRole, setCreatingRole] = useState(false);
  const [editingRole, setEditingRole] = useState<RoleDetail | null>(null);
  const [sent, setSent] = useState<string[]>([]);

  // Forms
  const inviteForm = useForm<InviteForm>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { email: "", role: "" },
  });

  const roleForm = useForm<CreateRoleForm>({
    resolver: zodResolver(createRoleSchema),
    defaultValues: { code: "", name: "", description: "", permissions: [] },
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [fetchedRoles, fetchedPermissions] = await Promise.all([
        apiRequest<RoleDetail[]>("/staff/roles/"),
        apiRequest<PermissionInfo[]>("/staff/permissions/"),
      ]);
      setRoles(fetchedRoles);
      setPermissions(fetchedPermissions);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load roles and permissions"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "ADMIN") {
      loadData();
    }
  }, [user]);

  if (!user || user.role !== "ADMIN") return null;

  const onInviteSubmit = async (data: InviteForm) => {
    setSending(true);
    try {
      await apiRequest("/staff/invitations/", {
        method: "POST",
        body: { email: data.email, role: data.role },
        authenticated: true,
      });
      toast.success(`Invitation sent to ${data.email}`);
      setSent((prev) => [data.email, ...prev]);
      inviteForm.reset();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setSending(false);
    }
  };

  const onCreateRoleSubmit = async (data: CreateRoleForm) => {
    setCreatingRole(true);
    try {
      const payload = {
        ...data,
        code: data.code.toUpperCase(),
      };
      const newRole = await apiRequest<RoleDetail>("/staff/roles/", {
        method: "POST",
        body: payload,
        authenticated: true,
      });
      toast.success(`Role "${newRole.name}" created successfully.`);
      
      // Update local state with the new role
      setRoles((prev) =>
        [...prev, newRole].sort((a, b) => a.code.localeCompare(b.code))
      );
      
      // Reset role creation form
      roleForm.reset({ code: "", name: "", description: "", permissions: [] });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create role");
    } finally {
      setCreatingRole(false);
    }
  };

  const onRoleFormSubmit = async (data: CreateRoleForm) => {
    if (editingRole) {
      setCreatingRole(true);
      try {
        let updatedRole = editingRole;
        if (!editingRole.is_system) {
          await apiRequest(`/staff/roles/${editingRole.code}/`, {
            method: "PATCH",
            body: { name: data.name, description: data.description },
            authenticated: true,
          });
        }
        
        updatedRole = await apiRequest<RoleDetail>(`/staff/roles/${editingRole.code}/permissions/`, {
          method: "PUT",
          body: { permissions: data.permissions },
          authenticated: true,
        });
        
        toast.success(`Role "${updatedRole.name}" updated successfully.`);
        setRoles((prev) =>
          prev.map((r) => (r.code === editingRole.code ? updatedRole : r))
        );
        setEditingRole(null);
        roleForm.reset({ code: "", name: "", description: "", permissions: [] });
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Failed to update role");
      } finally {
        setCreatingRole(false);
      }
    } else {
      await onCreateRoleSubmit(data);
    }
  };

  const handleEditRole = (role: RoleDetail) => {
    setEditingRole(role);
    roleForm.reset({
      code: role.code,
      name: role.name,
      description: role.description || "",
      permissions: role.permissions || [],
    });
  };

  const handleCancelEdit = () => {
    setEditingRole(null);
    roleForm.reset({ code: "", name: "", description: "", permissions: [] });
  };

  const handleDeleteRole = async (roleCode: string) => {
    if (!confirm(`Are you sure you want to delete the role "${roleCode}"? This cannot be undone.`)) {
      return;
    }
    try {
      await apiRequest(`/staff/roles/${roleCode}/`, {
        method: "DELETE",
        authenticated: true,
      });
      toast.success(`Role "${roleCode}" deleted successfully.`);
      setRoles((prev) => prev.filter((r) => r.code !== roleCode));
      if (editingRole?.code === roleCode) {
        setEditingRole(null);
        roleForm.reset({ code: "", name: "", description: "", permissions: [] });
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete role");
    }
  };

  const handlePermissionToggle = (permCode: string) => {
    const current = roleForm.getValues("permissions") || [];
    if (current.includes(permCode)) {
      roleForm.setValue(
        "permissions",
        current.filter((c) => c !== permCode)
      );
    } else {
      roleForm.setValue("permissions", [...current, permCode]);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Staff" description="Invite team members to join Serenity Health." />
        <div className="flex h-64 items-center justify-center rounded-xl border border-stone-200/70 bg-white dark:border-stone-800 dark:bg-stone-900">
          <div className="size-8 animate-spin rounded-full border-2 border-emerald-600/30 border-t-emerald-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="Staff" description="Invite team members to join Serenity Health." />
        <div className="flex h-64 flex-col items-center justify-center gap-4 rounded-xl border border-stone-200/70 bg-white p-6 text-center dark:border-stone-800 dark:bg-stone-900">
          <p className="text-sm font-medium text-red-600 dark:text-red-400">{error}</p>
          <Button onClick={loadData} variant="outline" className="gap-2">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Staff" description="Invite team members and manage platform roles." />

      <div className="flex gap-2">
        {([
          { key: "invitations", label: "Invitations" },
          { key: "roles", label: "Roles & Permissions" },
        ] as { key: Tab; label: string }[]).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
              tab === t.key
                ? "bg-emerald-600 text-white shadow-sm"
                : "bg-white text-stone-600 ring-1 ring-stone-200 hover:bg-stone-50 dark:bg-stone-900 dark:text-stone-400 dark:ring-stone-700 dark:hover:bg-stone-800"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "invitations" ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <form
            onSubmit={inviteForm.handleSubmit(onInviteSubmit)}
            className="space-y-4 rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900"
          >
            <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
              <MailSend01Icon className="size-4 text-emerald-600 dark:text-emerald-400" /> New invitation
            </h3>
            
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                className="h-10"
                placeholder="colleague@hospital.com"
                {...inviteForm.register("email")}
              />
              {inviteForm.formState.errors.email && (
                <p className="text-xs text-destructive">
                  {inviteForm.formState.errors.email.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Select Role</Label>
              <div className="grid gap-2 sm:grid-cols-2 max-h-[300px] overflow-y-auto p-0.5">
                {roles.map((role) => (
                  <label
                    key={role.code}
                    className="cursor-pointer rounded-lg border border-stone-200 p-3 text-sm transition-colors hover:border-emerald-200 has-[:checked]:border-emerald-500 has-[:checked]:bg-emerald-50/60 dark:border-stone-700 dark:hover:border-emerald-900 dark:has-[:checked]:border-emerald-600 dark:has-[:checked]:bg-emerald-900/20"
                  >
                    <input
                      type="radio"
                      value={role.code}
                      className="sr-only"
                      {...inviteForm.register("role")}
                    />
                    <div className="font-semibold text-stone-900 dark:text-stone-50 flex items-center justify-between">
                      <span>{role.name}</span>
                      <span className="text-[10px] font-mono bg-stone-100 text-stone-700 px-1.5 py-0.2 rounded dark:bg-stone-800 dark:text-stone-300">
                        {role.code}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-stone-500 dark:text-stone-400 line-clamp-2">
                      {role.description || "No description provided."}
                    </div>
                  </label>
                ))}
              </div>
              {inviteForm.formState.errors.role && (
                <p className="text-xs text-destructive">
                  {inviteForm.formState.errors.role.message}
                </p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={sending}>
              {sending ? "Sending..." : "Send invitation"}
            </Button>
            <p className="text-xs text-stone-400 dark:text-stone-500">
              The invitee will receive an email with a secure link to activate their account.
            </p>
          </form>

          <div className="rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900 h-full">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
              <UserGroupIcon className="size-4 text-emerald-600 dark:text-emerald-400" /> Recent invitations
            </h3>
            {sent.length === 0 ? (
              <p className="mt-4 text-sm text-stone-500 dark:text-stone-400">
                Invitations sent this session will be listed here.
              </p>
            ) : (
              <ul className="mt-4 divide-y divide-stone-100 dark:divide-stone-800">
                {sent.map((email) => (
                  <li key={email} className="flex items-center gap-3 py-3">
                    <div className="flex size-8 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                      {email[0].toUpperCase()}
                    </div>
                    <span className="truncate text-sm text-stone-700 dark:text-stone-300">
                      {email}
                    </span>
                    <span className="ml-auto rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                      Invited
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Create / Edit Custom Role form */}
          <form
            onSubmit={roleForm.handleSubmit(onRoleFormSubmit)}
            className="space-y-4 rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900"
          >
            <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
              {editingRole ? (
                <>
                  <PencilEdit01Icon className="size-4 text-emerald-600 dark:text-emerald-400" /> Edit Role: {editingRole.name}
                </>
              ) : (
                <>
                  <PlusSignIcon className="size-4 text-emerald-600 dark:text-emerald-400" /> Create Custom Role
                </>
              )}
            </h3>

            <div className="space-y-2">
              <Label htmlFor="code">Role Code (e.g. CLINICAL_LEAD)</Label>
              <Input
                id="code"
                type="text"
                placeholder="CLINICAL_LEAD"
                className="h-10 uppercase read-only:bg-stone-50 dark:read-only:bg-stone-900/50 read-only:text-stone-500"
                readOnly={!!editingRole}
                {...roleForm.register("code")}
              />
              {roleForm.formState.errors.code && (
                <p className="text-xs text-destructive">
                  {roleForm.formState.errors.code.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Display Name (e.g. Clinical Lead)</Label>
              <Input
                id="name"
                type="text"
                placeholder="Clinical Lead"
                className="h-10 read-only:bg-stone-50 dark:read-only:bg-stone-900/50 read-only:text-stone-500"
                readOnly={!!editingRole?.is_system}
                {...roleForm.register("name")}
              />
              {roleForm.formState.errors.name && (
                <p className="text-xs text-destructive">
                  {roleForm.formState.errors.name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                type="text"
                placeholder="Brief summary of the role's purpose"
                className="h-10 read-only:bg-stone-50 dark:read-only:bg-stone-900/50 read-only:text-stone-500"
                readOnly={!!editingRole?.is_system}
                {...roleForm.register("description")}
              />
              {roleForm.formState.errors.description && (
                <p className="text-xs text-destructive">
                  {roleForm.formState.errors.description.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Permissions</Label>
              <div className="max-h-[300px] overflow-y-auto rounded-lg border border-stone-200 p-3 space-y-2 dark:border-stone-700 bg-stone-50/50 dark:bg-stone-900/50">
                {permissions.map((perm) => {
                  const isChecked = roleForm.watch("permissions")?.includes(perm.code);
                  return (
                    <label
                      key={perm.code}
                      className="flex items-start gap-2.5 rounded-md p-2 hover:bg-stone-100 dark:hover:bg-stone-800 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked || false}
                        onChange={() => handlePermissionToggle(perm.code)}
                        className="mt-1 accent-emerald-600 rounded border-stone-300 text-emerald-600 focus:ring-emerald-500 size-4"
                      />
                      <div className="flex flex-col">
                        <span className="text-xs font-semibold text-stone-900 dark:text-stone-50">
                          {perm.name}
                        </span>
                        <span className="text-[11px] text-stone-500 dark:text-stone-400 leading-tight mt-0.5">
                          {perm.description || perm.code}
                        </span>
                      </div>
                    </label>
                  );
                })}
                {permissions.length === 0 && (
                  <p className="text-xs text-stone-500 text-center py-4">
                    No permissions available.
                  </p>
                )}
              </div>
              {roleForm.formState.errors.permissions && (
                <p className="text-xs text-destructive">
                  {roleForm.formState.errors.permissions.message}
                </p>
              )}
            </div>

            <div className="flex gap-2">
              {editingRole && (
                <Button type="button" variant="outline" className="flex-1" onClick={handleCancelEdit}>
                  Cancel
                </Button>
              )}
              <Button type="submit" className="flex-1" disabled={creatingRole}>
                {creatingRole ? "Saving..." : editingRole ? "Save Changes" : "Create Role"}
              </Button>
            </div>
          </form>

          {/* Existing Roles list */}
          <div className="rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900 flex flex-col h-[700px]">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50 mb-4">
              <UserGroupIcon className="size-4 text-emerald-600 dark:text-emerald-400" /> Existing Roles
            </h3>
            <div className="space-y-4 overflow-y-auto pr-1 flex-1">
              {roles.map((role) => (
                <div
                  key={role.code}
                  className="rounded-lg border border-stone-200 p-4 space-y-3 bg-stone-50/30 dark:border-stone-800 dark:bg-stone-950/30 transition-all hover:shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-sm text-stone-900 dark:text-stone-50">
                          {role.name}
                        </h4>
                        <Badge
                          variant={role.is_system ? "secondary" : "default"}
                          className="text-[10px] px-1.5 py-0"
                        >
                          {role.is_system ? "System" : "Custom"}
                        </Badge>
                      </div>
                      <p className="text-xs text-stone-500 dark:text-stone-400 mt-1">
                        {role.description || "No description provided."}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold bg-stone-100 text-stone-700 px-2 py-0.5 rounded dark:bg-stone-800 dark:text-stone-300">
                        {role.code}
                      </span>
                      
                      <button
                        onClick={() => handleEditRole(role)}
                        className="rounded p-1 hover:bg-stone-200 dark:hover:bg-stone-800 text-stone-500 hover:text-stone-900 dark:hover:text-stone-100 transition-colors cursor-pointer"
                        title="Edit role"
                      >
                        <PencilEdit01Icon className="size-4" />
                      </button>

                      {!role.is_system && (
                        <button
                          onClick={() => handleDeleteRole(role.code)}
                          className="rounded p-1 hover:bg-red-50 dark:hover:bg-red-950/30 text-stone-500 hover:text-red-600 dark:hover:text-red-400 transition-colors cursor-pointer"
                          title="Delete role"
                        >
                          <Delete02Icon className="size-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] font-semibold text-stone-400 dark:text-stone-500 mb-1.5 uppercase tracking-wider">
                      Permissions ({role.permissions?.length ?? 0})
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {role.permissions && role.permissions.length > 0 ? (
                        role.permissions.map((pCode) => (
                          <span
                            key={pCode}
                            className="inline-block text-[10px] bg-stone-100 text-stone-600 rounded px-1.5 py-0.5 dark:bg-stone-800 dark:text-stone-400"
                          >
                            {pCode}
                          </span>
                        ))
                      ) : (
                        <span className="text-[10px] text-stone-400 italic">
                          No permissions assigned.
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
