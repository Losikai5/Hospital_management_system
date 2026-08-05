"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Search01Icon,
  CheckmarkCircle02Icon,
  Calendar01Icon,
  AlertCircleIcon,
} from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingRows, EmptyState, ErrorState } from "@/components/dashboard/data-state";
import { AppointmentStatusBadge } from "@/components/dashboard/status-badge";
import { apiRequest } from "@/lib/api-client";
import { formatDate, formatTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Appointment } from "@/lib/types";

/** Local calendar date (YYYY-MM-DD) — the receptionist's "today". */
function localTodayISO() {
  const n = new Date();
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}-${String(
    n.getDate()
  ).padStart(2, "0")}`;
}

const ACTIVE = new Set(["PENDING", "CONFIRMED"]);

function byTime(a: Appointment, b: Appointment) {
  return (a.appointment_date + a.appointment_time).localeCompare(
    b.appointment_date + b.appointment_time
  );
}

function ApptRow({ a, highlight }: { a: Appointment; highlight?: boolean }) {
  return (
    <li
      className={cn(
        "flex flex-col gap-1.5 px-5 py-3.5 sm:flex-row sm:items-center sm:gap-3",
        highlight && "bg-emerald-50/50 dark:bg-emerald-900/10"
      )}
    >
      <div className="w-20 shrink-0 text-sm font-semibold tabular-nums text-stone-900 dark:text-stone-50">
        {formatTime(a.appointment_time)}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-stone-900 dark:text-stone-50">
          {a.patient_name}
        </div>
        <div className="truncate text-xs text-stone-500 dark:text-stone-400">
          {a.patient_email} · Dr. {a.doctor_name} · {a.doctor_specialization}
        </div>
      </div>
      <div className="flex items-center gap-2.5 text-xs text-stone-400">
        <span className="hidden sm:inline">{formatDate(a.appointment_date)}</span>
        <AppointmentStatusBadge status={a.status} />
      </div>
    </li>
  );
}

function Verdict({
  tone,
  icon: Icon,
  title,
  detail,
}: {
  tone: "success" | "warning" | "danger";
  icon: typeof CheckmarkCircle02Icon;
  title: string;
  detail: string;
}) {
  const box = {
    success:
      "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200",
    warning:
      "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200",
    danger:
      "border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-200",
  }[tone];
  const iconTone = {
    success: "text-emerald-600 dark:text-emerald-400",
    warning: "text-amber-600 dark:text-amber-400",
    danger: "text-red-500 dark:text-red-400",
  }[tone];
  return (
    <div className={cn("flex items-start gap-3 rounded-xl border p-4", box)}>
      <Icon className={cn("mt-0.5 size-5 shrink-0", iconTone)} />
      <div className="min-w-0">
        <div className="text-sm font-semibold">{title}</div>
        <div className="mt-0.5 text-sm opacity-90">{detail}</div>
      </div>
    </div>
  );
}

export default function FrontDeskPage() {
  const [appts, setAppts] = useState<Appointment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setAppts(await apiRequest<Appointment[]>("/appointments/"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load the schedule");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const today = localTodayISO();
  const all = useMemo(() => appts ?? [], [appts]);

  const todaySchedule = useMemo(
    () => all.filter((a) => a.appointment_date === today && ACTIVE.has(a.status)).sort(byTime),
    [all, today]
  );

  const q = query.trim().toLowerCase();
  const matches = useMemo(
    () =>
      q
        ? all
            .filter(
              (a) =>
                a.patient_name.toLowerCase().includes(q) ||
                a.patient_email.toLowerCase().includes(q)
            )
            .sort(byTime)
        : [],
    [all, q]
  );
  const todayMatch = matches.filter((a) => a.appointment_date === today && ACTIVE.has(a.status));
  const upcomingMatch = matches.filter((a) => a.appointment_date > today && ACTIVE.has(a.status));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Front Desk"
        description="Check a walk-in patient against the schedule — search by patient name or email."
      />

      <div className="relative max-w-xl">
        <Search01Icon className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-stone-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by patient name or email…"
          type="search"
          autoFocus
          className="h-11 w-full rounded-xl border border-stone-200 bg-white pl-10 pr-4 text-sm shadow-sm outline-none transition-colors placeholder:text-stone-400 focus-visible:border-emerald-500 focus-visible:ring-[3px] focus-visible:ring-emerald-500/20 dark:border-stone-700 dark:bg-stone-900 dark:placeholder:text-stone-500"
        />
      </div>

      {loading ? (
        <div className="rounded-xl border border-stone-200/70 bg-white p-5 shadow-sm dark:border-stone-800 dark:bg-stone-900">
          <LoadingRows rows={4} />
        </div>
      ) : error ? (
        <div className="rounded-xl border border-stone-200/70 bg-white shadow-sm dark:border-stone-800 dark:bg-stone-900">
          <ErrorState message={error} onRetry={load} />
        </div>
      ) : q ? (
        <div className="space-y-4">
          {todayMatch.length > 0 ? (
            <Verdict
              tone="success"
              icon={CheckmarkCircle02Icon}
              title={`${todayMatch[0].patient_name} has an appointment today`}
              detail={`${formatTime(todayMatch[0].appointment_time)} with Dr. ${todayMatch[0].doctor_name} · ${todayMatch[0].status}`}
            />
          ) : matches.length > 0 ? (
            <Verdict
              tone="warning"
              icon={Calendar01Icon}
              title="No appointment today"
              detail={
                upcomingMatch.length > 0
                  ? `Next booking: ${formatDate(upcomingMatch[0].appointment_date)} at ${formatTime(upcomingMatch[0].appointment_time)}`
                  : "This patient has no upcoming bookings."
              }
            />
          ) : (
            <Verdict
              tone="danger"
              icon={AlertCircleIcon}
              title="No appointment found"
              detail={`Nothing on the schedule matches “${query.trim()}”. This patient isn't booked.`}
            />
          )}

          {matches.length > 0 && (
            <section className="rounded-xl border border-stone-200/70 bg-white shadow-sm dark:border-stone-800 dark:bg-stone-900">
              <div className="border-b border-stone-100 px-5 py-3 text-[11px] font-medium uppercase tracking-wider text-stone-400 dark:border-stone-800 dark:text-stone-500">
                All bookings for this patient
              </div>
              <ul className="divide-y divide-stone-100 dark:divide-stone-800">
                {matches.map((a) => (
                  <ApptRow
                    key={a.id}
                    a={a}
                    highlight={a.appointment_date === today && ACTIVE.has(a.status)}
                  />
                ))}
              </ul>
            </section>
          )}
        </div>
      ) : (
        <section className="rounded-xl border border-stone-200/70 bg-white shadow-sm dark:border-stone-800 dark:bg-stone-900">
          <div className="flex items-center justify-between border-b border-stone-100 px-5 py-3 dark:border-stone-800">
            <span className="text-sm font-semibold text-stone-900 dark:text-stone-50">
              Today&apos;s schedule
            </span>
            <span className="text-xs text-stone-400">
              {todaySchedule.length} booked · {formatDate(today)}
            </span>
          </div>
          {todaySchedule.length === 0 ? (
            <EmptyState
              icon={Calendar01Icon}
              title="No appointments today"
              description="Patients booked for today will appear here. Search above to check a specific patient."
            />
          ) : (
            <ul className="divide-y divide-stone-100 dark:divide-stone-800">
              {todaySchedule.map((a) => (
                <ApptRow key={a.id} a={a} />
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
