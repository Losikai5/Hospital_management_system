"use client";

import { useState, useEffect, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { UserCircleIcon, SecurityLockIcon, HeartCheckIcon, Doctor01Icon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { PatientProfile } from "@/lib/types";

const profileSchema = z.object({
  first_name: z.string().max(150).optional(),
  last_name: z.string().max(150).optional(),
  phone: z.string().max(15).optional().or(z.literal("")),
  date_of_birth: z.string().optional().or(z.literal("")),
  gender: z.enum(["Male", "Female", "Other", ""]).optional(),
  address: z.string().optional(),
});

type ProfileForm = z.infer<typeof profileSchema>;

const patientSchema = z.object({
  blood_type: z.string().optional(),
  emergency_contact_name: z.string().optional(),
  emergency_contact_phone: z.string().optional(),
  medical_history_summary: z.string().optional(),
  insurance_details: z.string().optional(),
});

type PatientForm = z.infer<typeof patientSchema>;

const SPECIALIZATIONS: [string, string][] = [
  ["GENERAL", "General Practice"],
  ["CARDIOLOGY", "Cardiology"],
  ["DERMATOLOGY", "Dermatology"],
  ["NEUROLOGY", "Neurology"],
  ["ORTHOPEDICS", "Orthopedics"],
  ["PEDIATRICS", "Pediatrics"],
  ["PSYCHIATRY", "Psychiatry"],
  ["RADIOLOGY", "Radiology"],
  ["SURGERY", "Surgery"],
  ["GYNECOLOGY", "Gynecology"],
];

const doctorSchema = z.object({
  specialization: z.string().min(1, "Select a specialization"),
  license_number: z.string().min(1, "License number is required"),
  years_of_experience: z.string().optional(),
  consultation_fee: z.string().optional(),
  bio: z.string().optional(),
  is_available: z.boolean().optional(),
});

type DoctorForm = z.infer<typeof doctorSchema>;

type DoctorProfileResponse = {
  specialization: string;
  license_number: string;
  years_of_experience: number;
  bio: string | null;
  consultation_fee: string;
  is_available: boolean;
};

const passwordSchema = z
  .object({
    old_password: z.string().min(1, "Current password is required"),
    new_password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Za-z]/, "Must contain at least one letter")
      .regex(/[0-9]/, "Must contain at least one number"),
    confirm_new_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_new_password, {
    message: "Passwords do not match",
    path: ["confirm_new_password"],
  });

type PasswordForm = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { user, updateProfile, refreshUser } = useAuth();
  const [, setPatient] = useState<PatientProfile | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPatient, setSavingPatient] = useState(false);
  const [hasDoctorProfile, setHasDoctorProfile] = useState(false);
  const [savingDoctor, setSavingDoctor] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  const profileForm = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
      phone: user?.phone ?? "",
      date_of_birth: user?.date_of_birth ?? "",
      gender: (user?.gender as ProfileForm["gender"]) ?? "",
      address: user?.address ?? "",
    },
  });

  const patientForm = useForm<PatientForm>({ resolver: zodResolver(patientSchema) });
  const doctorForm = useForm<DoctorForm>({
    resolver: zodResolver(doctorSchema),
    defaultValues: { is_available: true },
  });
  const passwordForm = useForm<PasswordForm>({ resolver: zodResolver(passwordSchema) });

  const loadPatient = useCallback(async () => {
    if (user?.role !== "PATIENT") return;
    try {
      const data = await apiRequest<PatientProfile>("/patients/profile/", { authenticated: true });
      setPatient(data);
      patientForm.reset({
        blood_type: data.blood_type ?? "",
        emergency_contact_name: data.emergency_contact_name ?? "",
        emergency_contact_phone: data.emergency_contact_phone ?? "",
        medical_history_summary: data.medical_history_summary ?? "",
        insurance_details: data.insurance_details ?? "",
      });
    } catch {
      // patient profile endpoint may not be available for all accounts
    }
  }, [user?.role, patientForm]);

  const loadDoctor = useCallback(async () => {
    if (user?.role !== "DOCTOR") return;
    try {
      const data = await apiRequest<DoctorProfileResponse>("/doctors/profile/", { authenticated: true });
      setHasDoctorProfile(true);
      doctorForm.reset({
        specialization: data.specialization ?? "GENERAL",
        license_number: data.license_number ?? "",
        years_of_experience: String(data.years_of_experience ?? 0),
        consultation_fee: data.consultation_fee ?? "0",
        bio: data.bio ?? "",
        is_available: data.is_available ?? true,
      });
    } catch {
      // 404 = no DoctorProfile yet → create mode
      setHasDoctorProfile(false);
    }
  }, [user?.role, doctorForm]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadPatient();
      void loadDoctor();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadPatient, loadDoctor]);

  const onSaveProfile = async (data: ProfileForm) => {
    setSavingProfile(true);
    try {
      const clean = Object.fromEntries(Object.entries(data).filter(([, v]) => v !== ""));
      await updateProfile(clean as Parameters<typeof updateProfile>[0]);
      await refreshUser();
      toast.success("Profile updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSavingProfile(false);
    }
  };

  const onSavePatient = async (data: PatientForm) => {
    setSavingPatient(true);
    try {
      const clean = Object.fromEntries(Object.entries(data).filter(([, v]) => v !== ""));
      await apiRequest("/patients/profile/", { method: "PATCH", body: clean, authenticated: true });
      toast.success("Patient profile updated");
      await loadPatient();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSavingPatient(false);
    }
  };

  const onSaveDoctor = async (data: DoctorForm) => {
    setSavingDoctor(true);
    try {
      await apiRequest("/doctors/profile/", {
        method: hasDoctorProfile ? "PATCH" : "POST",
        body: {
          first_name: user?.first_name,
          last_name: user?.last_name,
          specialization: data.specialization,
          license_number: data.license_number,
          years_of_experience: Number(data.years_of_experience) || 0,
          consultation_fee: Number(data.consultation_fee) || 0,
          bio: data.bio || "",
          is_available: data.is_available ?? true,
        },
        authenticated: true,
      });
      toast.success(hasDoctorProfile ? "Professional profile updated" : "Professional profile created");
      await loadDoctor();
      await refreshUser();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSavingDoctor(false);
    }
  };

  const onChangePassword = async (data: PasswordForm) => {
    setChangingPassword(true);
    try {
      await apiRequest("/auth/change-password/", {
        method: "POST",
        body: data,
        authenticated: true,
      });
      toast.success("Password changed");
      passwordForm.reset();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Password change failed");
    } finally {
      setChangingPassword(false);
    }
  };

  if (!user) return null;

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Manage your personal details and security." />

      <div className="flex items-center gap-4 rounded-[18px] border border-hairline bg-canvas p-6 dark:border-stone-800 dark:bg-stone-900">
        <div className="flex size-16 items-center justify-center rounded-2xl bg-emerald-100 text-2xl font-bold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
          {user.first_name?.[0] ?? user.email[0]?.toUpperCase() ?? "U"}
        </div>
        <div>
          <h2 className="text-lg font-semibold text-stone-900 dark:text-stone-50">
            {user.first_name ? `${user.first_name} ${user.last_name}`.trim() : user.email}
          </h2>
          <p className="text-sm text-stone-500 dark:text-stone-400">{user.email}</p>
          <span className="mt-1.5 inline-block rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
            {user.role}
          </span>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={profileForm.handleSubmit(onSaveProfile)} className="space-y-4 rounded-[18px] border border-hairline bg-canvas p-6 dark:border-stone-800 dark:bg-stone-900">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
            <UserCircleIcon className="size-4 text-emerald-600 dark:text-emerald-400" /> Personal information
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="first_name">First name</Label>
              <Input id="first_name" className="h-10" {...profileForm.register("first_name")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_name">Last name</Label>
              <Input id="last_name" className="h-10" {...profileForm.register("last_name")} />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" className="h-10" placeholder="+1 (555) 000-0000" {...profileForm.register("phone")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="gender">Gender</Label>
              <select id="gender" className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50" {...profileForm.register("gender")}>
                <option value="">Prefer not to say</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="date_of_birth">Date of birth</Label>
            <Input id="date_of_birth" type="date" className="h-10" {...profileForm.register("date_of_birth")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">Address</Label>
            <textarea id="address" rows={2} className="w-full rounded-[11px] border border-hairline bg-canvas px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50" {...profileForm.register("address")} />
          </div>
          <Button type="submit" className="w-full" disabled={savingProfile}>
            {savingProfile ? "Saving..." : "Save changes"}
          </Button>
        </form>

        {user.role === "PATIENT" && (
          <form onSubmit={patientForm.handleSubmit(onSavePatient)} className="space-y-4 rounded-[18px] border border-hairline bg-canvas p-6 dark:border-stone-800 dark:bg-stone-900">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
              <HeartCheckIcon className="size-4 text-emerald-600 dark:text-emerald-400" /> Health information
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="blood_type">Blood type</Label>
                <select id="blood_type" className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50" {...patientForm.register("blood_type")}>
                  <option value="">Unknown</option>
                  {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="emergency_contact_phone">Emergency phone</Label>
                <Input id="emergency_contact_phone" className="h-10" placeholder="+1 (555) 000-0000" {...patientForm.register("emergency_contact_phone")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="emergency_contact_name">Emergency contact</Label>
              <Input id="emergency_contact_name" className="h-10" placeholder="Contact name" {...patientForm.register("emergency_contact_name")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="medical_history_summary">Medical history</Label>
              <textarea id="medical_history_summary" rows={3} className="w-full rounded-[11px] border border-hairline bg-canvas px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50" placeholder="Allergies, chronic conditions, past surgeries…" {...patientForm.register("medical_history_summary")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="insurance_details">Insurance details</Label>
              <textarea id="insurance_details" rows={2} className="w-full rounded-[11px] border border-hairline bg-canvas px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50" {...patientForm.register("insurance_details")} />
            </div>
            <Button type="submit" className="w-full" variant="outline" disabled={savingPatient}>
              {savingPatient ? "Saving..." : "Save health info"}
            </Button>
          </form>
        )}

        {user.role === "DOCTOR" && (
          <form onSubmit={doctorForm.handleSubmit(onSaveDoctor)} className="space-y-4 rounded-[18px] border border-hairline bg-canvas p-6 dark:border-stone-800 dark:bg-stone-900">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
              <Doctor01Icon className="size-4 text-emerald-600 dark:text-emerald-400" /> Professional information
            </h3>
            {!hasDoctorProfile && (!user.first_name || !user.last_name) && (
              <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-950/30 dark:text-amber-400">
                Add your name in Personal information first — it&apos;s required to create your doctor profile.
              </p>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="specialization">Specialization</Label>
                <select id="specialization" className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50" {...doctorForm.register("specialization")}>
                  {SPECIALIZATIONS.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
                {doctorForm.formState.errors.specialization && (
                  <p className="text-xs text-destructive">{doctorForm.formState.errors.specialization.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="license_number">License number</Label>
                <Input id="license_number" className="h-10" placeholder="e.g. MD-123456" {...doctorForm.register("license_number")} />
                {doctorForm.formState.errors.license_number && (
                  <p className="text-xs text-destructive">{doctorForm.formState.errors.license_number.message}</p>
                )}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="years_of_experience">Years of experience</Label>
                <Input id="years_of_experience" type="number" min={0} className="h-10" {...doctorForm.register("years_of_experience")} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="consultation_fee">Consultation fee</Label>
                <Input id="consultation_fee" type="number" min={0} step="0.01" className="h-10" placeholder="0.00" {...doctorForm.register("consultation_fee")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="bio">Bio</Label>
              <textarea id="bio" rows={3} className="w-full rounded-[11px] border border-hairline bg-canvas px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50" placeholder="Short professional bio shown to patients" {...doctorForm.register("bio")} />
            </div>
            <label className="flex items-center gap-2.5 text-sm text-stone-700 dark:text-stone-300">
              <input type="checkbox" className="size-4 rounded border-stone-300 text-emerald-600 focus:ring-emerald-500 dark:border-stone-600" {...doctorForm.register("is_available")} />
              Accepting appointments
            </label>
            <Button type="submit" className="w-full" variant="outline" disabled={savingDoctor}>
              {savingDoctor ? "Saving..." : hasDoctorProfile ? "Save professional info" : "Create doctor profile"}
            </Button>
          </form>
        )}

        <form onSubmit={passwordForm.handleSubmit(onChangePassword)} className="space-y-4 rounded-[18px] border border-hairline bg-canvas p-6 dark:border-stone-800 dark:bg-stone-900">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-stone-900 dark:text-stone-50">
            <SecurityLockIcon className="size-4 text-emerald-600 dark:text-emerald-400" /> Change password
          </h3>
          <div className="space-y-2">
            <Label htmlFor="old_password">Current password</Label>
            <Input id="old_password" type="password" className="h-10" {...passwordForm.register("old_password")} />
            {passwordForm.formState.errors.old_password && (
              <p className="text-xs text-destructive">{passwordForm.formState.errors.old_password.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="new_password">New password</Label>
            <Input id="new_password" type="password" className="h-10" {...passwordForm.register("new_password")} />
            {passwordForm.formState.errors.new_password && (
              <p className="text-xs text-destructive">{passwordForm.formState.errors.new_password.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm_new_password">Confirm new password</Label>
            <Input id="confirm_new_password" type="password" className="h-10" {...passwordForm.register("confirm_new_password")} />
            {passwordForm.formState.errors.confirm_new_password && (
              <p className="text-xs text-destructive">{passwordForm.formState.errors.confirm_new_password.message}</p>
            )}
          </div>
          <Button type="submit" className="w-full" variant="outline" disabled={changingPassword}>
            {changingPassword ? "Updating..." : "Update password"}
          </Button>
        </form>
      </div>
    </div>
  );
}
