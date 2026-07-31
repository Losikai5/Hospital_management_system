"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { UserGroupIcon, MailSend01Icon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

const inviteSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  role: z.enum(["DOCTOR", "RECEPTIONIST", "PHARMACIST", "ADMIN"]),
});

type InviteForm = z.infer<typeof inviteSchema>;

const ROLE_INFO: Record<string, { label: string; description: string }> = {
  DOCTOR: { label: "Doctor", description: "Manage appointments and write medical records." },
  RECEPTIONIST: { label: "Receptionist", description: "Confirm and manage appointment bookings." },
  PHARMACIST: { label: "Pharmacist", description: "Manage inventory and dispense prescriptions." },
  ADMIN: { label: "Administrator", description: "Full access, including staff invitations." },
};

export default function StaffPage() {
  const { user } = useAuth();
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InviteForm>({ resolver: zodResolver(inviteSchema) });

  if (!user || user.role !== "ADMIN") return null;

  const onSubmit = async (data: InviteForm) => {
    setSending(true);
    try {
      await apiRequest("/staff/invitations/", {
        method: "POST",
        body: { email: data.email, role: data.role },
        authenticated: true,
      });
      toast.success(`Invitation sent to ${data.email}`);
      setSent((prev) => [data.email, ...prev]);
      reset();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to send invitation");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Staff"
        description="Invite team members to join Serenity Health."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
            <MailSend01Icon className="size-4 text-emerald-600 dark:text-emerald-400" /> New invitation
          </h3>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" className="h-10" placeholder="colleague@hospital.com" {...register("email")} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label>Role</Label>
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(ROLE_INFO).map(([role, info]) => (
                <label key={role} className="cursor-pointer rounded-lg border border-stone-200 p-3 text-sm transition-colors has-[:checked]:border-emerald-500 has-[:checked]:bg-emerald-50/60 dark:border-stone-700 dark:has-[:checked]:border-emerald-600 dark:has-[:checked]:bg-emerald-900/20">
                  <input type="radio" value={role} className="sr-only" {...register("role")} />
                  <div className="font-medium text-stone-900 dark:text-stone-50">{info.label}</div>
                  <div className="mt-0.5 text-xs text-stone-500 dark:text-stone-400">{info.description}</div>
                </label>
              ))}
            </div>
            {errors.role && <p className="text-xs text-destructive">{errors.role.message}</p>}
          </div>
          <Button type="submit" className="w-full" disabled={sending}>
            {sending ? "Sending..." : "Send invitation"}
          </Button>
          <p className="text-xs text-stone-400 dark:text-stone-500">
            The invitee will receive an email with a secure link to activate their account.
          </p>
        </form>

        <div className="rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900">
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
                  <span className="truncate text-sm text-stone-700 dark:text-stone-300">{email}</span>
                  <span className="ml-auto rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                    Invited
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
