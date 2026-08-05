"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useForm, useWatch, type Control } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowLeft02Icon, Calendar01Icon, Search01Icon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingRows, ErrorState } from "@/components/dashboard/data-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import type { Doctor, Patient } from "@/lib/types";

const bookSchema = z.object({
  doctor: z.coerce.number({ message: "Select a doctor" }),
  appointment_date: z.string().min(1, "Pick a date"),
  appointment_time: z.string().min(1, "Pick a time"),
  reason: z.string().max(500).optional(),
});

type BookForm = z.infer<typeof bookSchema>;

type BookFormInput = {
  doctor: unknown;
  appointment_date: string;
  appointment_time: string;
  reason?: string;
};

const emptyNewPatient = { email: "", first_name: "", last_name: "", phone: "" };

export default function BookAppointmentPage() {
  const router = useRouter();
  const { hasPermission } = useAuth();
  const bookingForOthers = hasPermission("can_view_all_patients");

  const [doctors, setDoctors] = useState<Doctor[] | null>(null);
  const [slots, setSlots] = useState<string[]>([]);
  const [doctorsError, setDoctorsError] = useState<string | null>(null);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Staff-only: who is this appointment for?
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientQuery, setPatientQuery] = useState("");
  const [patientResults, setPatientResults] = useState<Patient[]>([]);
  const [searchingPatients, setSearchingPatients] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [newPatient, setNewPatient] = useState(emptyNewPatient);
  const [registering, setRegistering] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    control,
  } = useForm<BookFormInput, never, BookForm>({
    resolver: zodResolver(bookSchema),
  });

  const watchControl = control as unknown as Control<BookFormInput>;
  const selectedDoctor = useWatch({ control: watchControl, name: "doctor" }) as number | undefined;
  const selectedDate = useWatch({ control: watchControl, name: "appointment_date" });

  const loadDoctors = useCallback(async () => {
    setDoctorsError(null);
    try {
      setDoctors(await apiRequest<Doctor[]>("/doctors/"));
    } catch (err) {
      setDoctorsError(err instanceof Error ? err.message : "Failed to load doctors");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void loadDoctors(); }, 0);
    return () => window.clearTimeout(timer);
  }, [loadDoctors]);

  useEffect(() => {
    if (!selectedDoctor || !selectedDate) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setSlotsLoading(true);
      try {
        const data = await apiRequest<{ available_slots?: string[] }>(
          `/appointments/slots/?doctor_id=${selectedDoctor}&date=${selectedDate}`
        );
        if (!cancelled) setSlots((data.available_slots ?? []).map((slot) => slot.slice(0, 5)));
      } catch {
        if (!cancelled) setSlots([]);
      } finally {
        if (!cancelled) setSlotsLoading(false);
      }
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [selectedDoctor, selectedDate]);

  // Staff patient search (debounced)
  useEffect(() => {
    if (!bookingForOthers) return;
    const query = patientQuery.trim();
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      if (!query) {
        setPatientResults([]);
        return;
      }
      setSearchingPatients(true);
      try {
        const results = await apiRequest<Patient[]>(`/patients/?q=${encodeURIComponent(query)}`);
        if (!cancelled) setPatientResults(results);
      } catch {
        if (!cancelled) setPatientResults([]);
      } finally {
        if (!cancelled) setSearchingPatients(false);
      }
    }, query ? 250 : 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [patientQuery, bookingForOthers]);

  const registerPatient = async () => {
    if (!newPatient.email || !newPatient.first_name || !newPatient.last_name) {
      toast.error("Email, first name and last name are required");
      return;
    }
    setRegistering(true);
    try {
      const created = await apiRequest<Patient>("/patients/", {
        method: "POST",
        body: newPatient,
        authenticated: true,
      });
      toast.success("Patient registered");
      setSelectedPatient(created);
      setShowRegister(false);
      setNewPatient(emptyNewPatient);
      setPatientQuery("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not register patient");
    } finally {
      setRegistering(false);
    }
  };

  const onSubmit = async (data: BookForm) => {
    if (bookingForOthers && !selectedPatient) {
      toast.error("Select a patient to book for");
      return;
    }
    setIsSubmitting(true);
    try {
      await apiRequest("/appointments/book/", {
        method: "POST",
        body: {
          doctor: data.doctor,
          ...(bookingForOthers && selectedPatient ? { patient: selectedPatient.id } : {}),
          appointment_date: data.appointment_date,
          appointment_time: data.appointment_time,
          reason: data.reason || "",
        },
        authenticated: true,
      });
      toast.success("Appointment booked");
      router.push("/dashboard/appointments");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Booking failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const today = new Date().toISOString().split("T")[0];
  const fieldClass =
    "h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50";

  return (
    <div className="space-y-6">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-sm font-medium text-stone-500 transition-colors hover:text-stone-900 dark:text-stone-400 dark:hover:text-stone-50"
      >
        <ArrowLeft02Icon className="size-4" /> Back
      </button>
      <PageHeader
        title="Book an appointment"
        description={
          bookingForOthers
            ? "Find or register the patient, then choose a doctor, date and time."
            : "Choose a doctor, date and time for your visit."
        }
      />

      <div className="max-w-xl">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900">
          {bookingForOthers && (
            <div className="space-y-2">
              <Label>Patient</Label>
              {selectedPatient ? (
                <div className="flex items-center justify-between gap-3 rounded-lg border border-emerald-300 bg-emerald-50/60 px-3 py-2.5 dark:border-emerald-800 dark:bg-emerald-900/20">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-stone-900 dark:text-stone-50">
                      {selectedPatient.first_name} {selectedPatient.last_name}
                    </div>
                    <div className="truncate text-xs text-stone-500 dark:text-stone-400">
                      {selectedPatient.email}
                      {selectedPatient.phone ? ` · ${selectedPatient.phone}` : ""}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedPatient(null)}
                    className="shrink-0 text-xs font-medium text-stone-500 underline-offset-2 hover:text-stone-900 hover:underline dark:text-stone-400 dark:hover:text-stone-50"
                  >
                    Change
                  </button>
                </div>
              ) : showRegister ? (
                <div className="space-y-3 rounded-lg border border-stone-200 p-3.5 dark:border-stone-700">
                  <div className="text-xs font-medium text-stone-500 dark:text-stone-400">Register a new patient</div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input placeholder="Email" type="email" className="h-10" value={newPatient.email} onChange={(e) => setNewPatient({ ...newPatient, email: e.target.value })} />
                    <Input placeholder="Phone (optional)" className="h-10" value={newPatient.phone} onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })} />
                    <Input placeholder="First name" className="h-10" value={newPatient.first_name} onChange={(e) => setNewPatient({ ...newPatient, first_name: e.target.value })} />
                    <Input placeholder="Last name" className="h-10" value={newPatient.last_name} onChange={(e) => setNewPatient({ ...newPatient, last_name: e.target.value })} />
                  </div>
                  <div className="flex gap-2">
                    <Button type="button" size="sm" onClick={registerPatient} disabled={registering}>
                      {registering ? "Registering…" : "Register & select"}
                    </Button>
                    <Button type="button" size="sm" variant="ghost" onClick={() => setShowRegister(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="relative">
                    <Search01Icon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-stone-400" />
                    <input
                      value={patientQuery}
                      onChange={(e) => setPatientQuery(e.target.value)}
                      placeholder="Search patient by name or email…"
                      className={cn(fieldClass, "pl-9")}
                      type="search"
                    />
                  </div>
                  {patientQuery.trim() && (
                    <div className="overflow-hidden rounded-lg border border-stone-200 dark:border-stone-700">
                      {searchingPatients ? (
                        <div className="p-3 text-sm text-stone-400">Searching…</div>
                      ) : patientResults.length > 0 ? (
                        <ul className="max-h-56 divide-y divide-stone-100 overflow-y-auto dark:divide-stone-800">
                          {patientResults.map((p) => (
                            <li key={p.id}>
                              <button
                                type="button"
                                onClick={() => {
                                  setSelectedPatient(p);
                                  setPatientQuery("");
                                  setPatientResults([]);
                                }}
                                className="flex w-full flex-col items-start px-3 py-2 text-left transition-colors hover:bg-stone-50 dark:hover:bg-stone-800"
                              >
                                <span className="text-sm font-medium text-stone-900 dark:text-stone-50">
                                  {p.first_name} {p.last_name}
                                </span>
                                <span className="text-xs text-stone-500 dark:text-stone-400">
                                  {p.email}
                                  {p.phone ? ` · ${p.phone}` : ""}
                                </span>
                              </button>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <div className="flex items-center justify-between gap-2 p-3 text-sm text-stone-500 dark:text-stone-400">
                          <span>No patient found.</span>
                          <button type="button" onClick={() => setShowRegister(true)} className="font-medium text-emerald-600 hover:underline dark:text-emerald-400">
                            Register new
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowRegister(true)}
                    className="text-xs font-medium text-emerald-600 hover:underline dark:text-emerald-400"
                  >
                    + Register a new patient
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="doctor">Doctor</Label>
            {doctorsError ? (
              <ErrorState message={doctorsError} onRetry={loadDoctors} />
            ) : !doctors ? (
              <LoadingRows rows={2} />
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {doctors.map((d) => (
                  <label
                    key={d.id}
                    className={cn(
                      "flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-colors",
                      selectedDoctor === d.id
                        ? "border-emerald-500 bg-emerald-50/60 dark:border-emerald-600 dark:bg-emerald-900/20"
                        : "border-stone-200 hover:border-stone-300 dark:border-stone-700 dark:hover:border-stone-600"
                    )}
                  >
                    <input type="radio" value={d.id} className="sr-only" {...register("doctor")} />
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                      {d.first_name[0]}{d.last_name[0]}
                    </div>
                    <div className="min-w-0">
                      <div className="truncate font-medium text-stone-900 dark:text-stone-50">
                        Dr. {d.first_name} {d.last_name}
                      </div>
                      <div className="truncate text-xs text-stone-500 dark:text-stone-400">
                        {d.specialization_display} · {d.years_of_experience} yrs
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}
            {errors.doctor && <p className="text-xs text-destructive">{errors.doctor.message}</p>}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="appointment_date">Date</Label>
              <Input id="appointment_date" type="date" min={today} className="h-10" {...register("appointment_date")} />
              {errors.appointment_date && <p className="text-xs text-destructive">{errors.appointment_date.message}</p>}
            </div>
            <div className="space-y-2">
              <Label>Time</Label>
              {slotsLoading ? (
                <div className="flex h-10 items-center text-sm text-stone-400">Loading slots…</div>
              ) : slots.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {slots.map((slot) => (
                    <label key={slot} className="cursor-pointer">
                      <input type="radio" value={slot} className="peer sr-only" {...register("appointment_time")} />
                      <span className="inline-flex rounded-md border border-stone-200 px-2.5 py-1.5 text-xs font-medium text-stone-700 transition-colors peer-checked:border-emerald-500 peer-checked:bg-emerald-600 peer-checked:text-white dark:border-stone-700 dark:text-stone-300">
                        {slot}
                      </span>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="flex h-10 items-center gap-1.5 text-sm text-stone-400">
                  <Calendar01Icon className="size-4" />
                  {selectedDoctor ? "Pick a date to see slots" : "Select a doctor first"}
                </div>
              )}
              {errors.appointment_time && <p className="text-xs text-destructive">{errors.appointment_time.message}</p>}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="reason">Reason (optional)</Label>
            <textarea
              id="reason"
              rows={3}
              placeholder="Briefly describe the reason for the visit"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
              {...register("reason")}
            />
            {errors.reason && <p className="text-xs text-destructive">{errors.reason.message}</p>}
          </div>

          <Button
            type="submit"
            size="lg"
            className="w-full"
            disabled={isSubmitting || !selectedDoctor || !selectedDate || !slots.length || (bookingForOthers && !selectedPatient)}
          >
            {isSubmitting ? "Booking..." : "Book appointment"}
          </Button>
        </form>
      </div>
    </div>
  );
}
