"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Calendar01Icon, PlusSignIcon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingRows, EmptyState, ErrorState } from "@/components/dashboard/data-state";
import { AppointmentStatusBadge } from "@/components/dashboard/status-badge";
import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { formatDate, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Appointment } from "@/lib/types";

const FILTERS = ["ALL", "PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"] as const;

export default function AppointmentsPage() {
  const { user, hasPermission } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("ALL");
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setAppointments(await apiRequest<Appointment[]>("/appointments/"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load appointments");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const runAction = async (id: number, path: string, successMsg: string) => {
    setBusyId(id);
    try {
      await apiRequest(path, { method: "POST", authenticated: true });
      toast.success(successMsg);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  };

  if (!user) return null;

  const canConfirm = hasPermission("can_confirm_appointments");
  const canComplete = hasPermission("can_complete_appointments");
  const canCancel = hasPermission("can_cancel_appointments");
  const canBook = hasPermission("can_create_appointments");
  const isDoctor = user.role === "DOCTOR";
  const heading = isDoctor
    ? { title: "My calendar", description: "Confirm or decline the appointments patients have booked with you." }
    : { title: "Appointments", description: "Manage scheduled visits across the hospital." };

  const filtered = (appointments ?? []).filter((a) => filter === "ALL" || a.status === filter);

  return (
    <div className="space-y-6">
      <PageHeader
        title={heading.title}
        description={heading.description}
        action={
          canBook ? (
            <Link href="/dashboard/appointments/book">
              <Button className="gap-1.5"><PlusSignIcon className="size-4" /> Book appointment</Button>
            </Link>
          ) : undefined
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors",
              filter === f
                ? "bg-emerald-600 text-white shadow-sm"
                : "bg-white text-stone-600 ring-1 ring-stone-200 hover:bg-stone-50 dark:bg-stone-900 dark:text-stone-400 dark:ring-stone-700 dark:hover:bg-stone-800"
            )}
          >
            {f === "ALL" ? "All" : f[0] + f.slice(1).toLowerCase().replace("_", " ")}
          </button>
        ))}
      </div>

      <section className="rounded-xl border border-stone-200/70 bg-white shadow-sm dark:border-stone-800 dark:bg-stone-900">
        {loading ? (
          <div className="p-5"><LoadingRows rows={5} /></div>
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Calendar01Icon}
            title={filter === "ALL" ? "No appointments yet" : `No ${filter.toLowerCase().replace("_", " ")} appointments`}
            description="When appointments are booked they'll appear here."
          />
        ) : (
          <ul className="divide-y divide-stone-100 dark:divide-stone-800">
            {filtered.map((a) => (
              <li key={a.id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center">
                <div className="flex h-12 w-14 shrink-0 flex-col items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-900/30">
                  <span className="text-[11px] font-semibold uppercase text-emerald-600 dark:text-emerald-400">
                    {formatDate(a.appointment_date).split(" ")[0]}
                  </span>
                  <span className="text-base font-bold leading-tight text-emerald-700 dark:text-emerald-300">
                    {formatDate(a.appointment_date).split(" ")[1].replace(",", "")}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                    <span className="text-sm font-semibold text-stone-900 dark:text-stone-50">{isDoctor ? a.patient_name : a.doctor_name}</span>
                    <span className="text-xs text-stone-400">·</span>
                    <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">{a.doctor_specialization}</span>
                  </div>
                  <div className="mt-0.5 text-xs text-stone-500 dark:text-stone-400">
                    {formatTime(a.appointment_time)} · {isDoctor ? a.patient_email : a.patient_name}
                    {a.reason ? ` · "${a.reason}"` : ""}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <AppointmentStatusBadge status={a.status} />
                  {a.status === "PENDING" && canConfirm && (
                    <Button size="sm" variant="outline" className="text-emerald-700 dark:text-emerald-400" disabled={busyId === a.id} onClick={() => runAction(a.id, `/appointments/${a.id}/confirm/`, "Appointment confirmed")}>
                      Confirm
                    </Button>
                  )}
                  {a.status === "CONFIRMED" && canComplete && (
                    <Button size="sm" variant="outline" className="text-sky-700 dark:text-sky-400" disabled={busyId === a.id} onClick={() => runAction(a.id, `/appointments/${a.id}/complete/`, "Appointment marked complete")}>
                      Complete
                    </Button>
                  )}
                  {(a.status === "PENDING" || a.status === "CONFIRMED") && canCancel && (
                    <Button size="sm" variant="ghost" className="text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30" disabled={busyId === a.id} onClick={() => runAction(a.id, `/appointments/${a.id}/cancel/`, isDoctor && a.status === "PENDING" ? "Appointment declined" : "Appointment cancelled")}>
                      {isDoctor && a.status === "PENDING" ? "Decline" : "Cancel"}
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
