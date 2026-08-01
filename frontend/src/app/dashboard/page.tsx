"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import {
  Calendar01Icon,
  Doctor01Icon,
  MedicalFileIcon,
  PillIcon,
  Alert01Icon,
  ArrowRight01Icon,
} from "hugeicons-react";
import { PageHeader, StatCard } from "@/components/dashboard/page-header";
import { ProfileCompletionBanner } from "@/components/dashboard/profile-completion-banner";
import { LoadingRows, EmptyState, ErrorState } from "@/components/dashboard/data-state";
import { AppointmentStatusBadge, LowStockBadge } from "@/components/dashboard/status-badge";
import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { formatDate, formatTime } from "@/lib/format";
import type { Appointment, Doctor, Medicine, Prescription, MedicalRecord } from "@/lib/types";

function useFetch<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fn());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    load();
  }, [load]);

  return { data, error, loading, reload: load };
}

export default function DashboardPage() {
  const { user } = useAuth();
  if (!user) return null;
  const isPatient = user.role === "PATIENT";
  const isDoctor = user.role === "DOCTOR";
  const isPharmacist = user.role === "PHARMACIST";
  const isAdmin = user.role === "ADMIN";

  const appointments = useFetch<Appointment[]>(() => apiRequest("/appointments/"), []);
  const doctors = useFetch<Doctor[]>(() => apiRequest("/doctors/"), []);
  const records = useFetch<MedicalRecord[]>(() => apiRequest("/medical-records/"), []);
  const medicines = useFetch<Medicine[]>(() => apiRequest("/pharmacy/medicines/"), []);
  const prescriptions = useFetch<Prescription[]>(
    () => apiRequest(isPatient ? "/pharmacy/prescriptions/mine/" : "/pharmacy/prescriptions/"),
    [isPatient]
  );

  const upcoming = (appointments.data ?? [])
    .filter((a) => a.status === "PENDING" || a.status === "CONFIRMED")
    .sort((a, b) => `${a.appointment_date}${a.appointment_time}`.localeCompare(`${b.appointment_date}${b.appointment_time}`))
    .slice(0, 5);

  const pendingRx = (prescriptions.data ?? []).filter((p) => p.status === "PENDING");
  const lowStock = (medicines.data ?? []).filter((m) => m.is_low_stock);
  const firstName = user.first_name || user.email.split("@")[0];

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Good ${new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}, ${firstName}`}
        description="Here's what's happening across your care today."
      />

      <ProfileCompletionBanner />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Calendar01Icon}
          label="Appointments"
          value={appointments.loading ? undefined : (appointments.data?.length ?? 0)}
          loading={appointments.loading}
          sub={upcoming.length > 0 ? `${upcoming.length} upcoming` : undefined}
        />
        <StatCard
          icon={Doctor01Icon}
          label={isPatient ? "Available doctors" : "Doctors"}
          value={doctors.loading ? undefined : (doctors.data?.length ?? 0)}
          loading={doctors.loading}
        />
        <StatCard
          icon={MedicalFileIcon}
          label="Medical records"
          value={records.loading ? undefined : (records.data?.length ?? 0)}
          loading={records.loading}
        />
        <StatCard
          icon={PillIcon}
          label="Prescriptions"
          value={prescriptions.loading ? undefined : (prescriptions.data?.length ?? 0)}
          loading={prescriptions.loading}
          sub={pendingRx.length > 0 ? `${pendingRx.length} pending` : undefined}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-xl border border-stone-200/70 bg-white shadow-sm lg:col-span-2 dark:border-stone-800 dark:bg-stone-900">
          <header className="flex items-center justify-between border-b border-stone-100 px-5 py-4 dark:border-stone-800">
            <div>
              <h2 className="text-sm font-semibold text-stone-900 dark:text-stone-50">Upcoming appointments</h2>
              <p className="text-xs text-stone-500 dark:text-stone-400">Next scheduled and confirmed visits</p>
            </div>
            <Link href="/dashboard/appointments" className="flex items-center gap-1 text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400">
              View all <ArrowRight01Icon className="size-3.5" />
            </Link>
          </header>
          <div>
            {appointments.loading ? (
              <div className="p-5"><LoadingRows rows={3} /></div>
            ) : appointments.error ? (
              <ErrorState message={appointments.error} onRetry={appointments.reload} />
            ) : upcoming.length === 0 ? (
              <EmptyState
                icon={Calendar01Icon}
                title="No upcoming appointments"
                description={isPatient ? "Book a visit with one of our doctors to get started." : "No pending appointments right now."}
                action={isPatient ? (
                  <Link href="/dashboard/appointments/book"><Button size="sm">Book an appointment</Button></Link>
                ) : undefined}
              />
            ) : (
              <ul className="divide-y divide-stone-100 dark:divide-stone-800">
                {upcoming.map((a) => (
                  <li key={a.id} className="flex items-center gap-4 px-5 py-3.5">
                    <div className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
                      <span className="text-[11px] font-semibold leading-none">{formatDate(a.appointment_date).split(" ")[0]}</span>
                      <span className="text-sm font-bold leading-tight">{formatDate(a.appointment_date).split(" ")[1].replace(",", "")}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-stone-900 dark:text-stone-50">{user.role === "DOCTOR" ? a.patient_name : a.doctor_name}</div>
                      <div className="truncate text-xs text-stone-500 dark:text-stone-400">
                        {a.doctor_specialization} · {formatTime(a.appointment_time)}
                        {a.reason ? ` · ${a.reason}` : ""}
                      </div>
                    </div>
                    <AppointmentStatusBadge status={a.status} />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <div className="space-y-6">
          {isPharmacist || isAdmin ? (
            <section className="rounded-xl border border-stone-200/70 bg-white shadow-sm dark:border-stone-800 dark:bg-stone-900">
              <header className="flex items-center justify-between border-b border-stone-100 px-5 py-4 dark:border-stone-800">
                <h2 className="text-sm font-semibold text-stone-900 dark:text-stone-50">Inventory alerts</h2>
                <Link href="/dashboard/pharmacy" className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400">
                  Manage
                </Link>
              </header>
              <div>
                {medicines.loading ? (
                  <div className="p-5"><LoadingRows rows={3} /></div>
                ) : lowStock.length === 0 ? (
                  <div className="flex items-center gap-2.5 px-5 py-6 text-sm text-stone-500 dark:text-stone-400">
                    <Alert01Icon className="size-4 text-emerald-500" />
                    All medicines are well stocked.
                  </div>
                ) : (
                  <ul className="divide-y divide-stone-100 dark:divide-stone-800">
                    {lowStock.slice(0, 5).map((m) => (
                      <li key={m.id} className="flex items-center justify-between gap-3 px-5 py-3">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium text-stone-900 dark:text-stone-50">{m.name}</div>
                          <div className="text-xs text-stone-500 dark:text-stone-400">{m.stock_quantity ?? 0} in stock</div>
                        </div>
                        <LowStockBadge />
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </section>
          ) : null}

          <section className="rounded-xl border border-stone-200/70 bg-white shadow-sm dark:border-stone-800 dark:bg-stone-900">
            <header className="border-b border-stone-100 px-5 py-4 dark:border-stone-800">
              <h2 className="text-sm font-semibold text-stone-900 dark:text-stone-50">Quick actions</h2>
            </header>
            <div className="grid gap-2 p-5">
              <Link href="/dashboard/appointments/book" className="flex items-center justify-between rounded-lg border border-stone-200 px-3.5 py-2.5 text-sm font-medium text-stone-700 transition-colors hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 dark:border-stone-700 dark:text-stone-300 dark:hover:border-emerald-700 dark:hover:bg-emerald-900/20">
                Book an appointment
                <ArrowRight01Icon className="size-4" />
              </Link>
              <Link href="/dashboard/doctors" className="flex items-center justify-between rounded-lg border border-stone-200 px-3.5 py-2.5 text-sm font-medium text-stone-700 transition-colors hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 dark:border-stone-700 dark:text-stone-300 dark:hover:border-emerald-700 dark:hover:bg-emerald-900/20">
                Browse doctors
                <ArrowRight01Icon className="size-4" />
              </Link>
              <Link href="/dashboard/pharmacy" className="flex items-center justify-between rounded-lg border border-stone-200 px-3.5 py-2.5 text-sm font-medium text-stone-700 transition-colors hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 dark:border-stone-700 dark:text-stone-300 dark:hover:border-emerald-700 dark:hover:bg-emerald-900/20">
                {isPatient ? "My prescriptions" : "Pharmacy"}
                <ArrowRight01Icon className="size-4" />
              </Link>
            </div>
          </section>
        </div>
      </div>

      {!appointments.loading && !appointments.error && appointments.data && appointments.data.length > 0 && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center text-xs text-stone-400 dark:text-stone-500"
        >
          Showing live data from your hospital network.
        </motion.p>
      )}
    </div>
  );
}
