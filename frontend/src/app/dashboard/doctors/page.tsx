"use client";

import { useState, useEffect, useCallback } from "react";
import { Search01Icon, Doctor01Icon, CheckmarkCircle02Icon, CancelCircleIcon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingRows, EmptyState, ErrorState } from "@/components/dashboard/data-state";
import { apiRequest } from "@/lib/api-client";
import { formatFee, initials } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Doctor } from "@/lib/types";

const SPECIALTIES = ["All", "General Practice", "Cardiology", "Dermatology", "Neurology", "Orthopedics", "Pediatrics", "Psychiatry", "Radiology", "Surgery", "Gynecology"];

export default function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [specialty, setSpecialty] = useState("All");

  const load = useCallback(async () => {
    setError(null);
    try {
      setDoctors(await apiRequest<Doctor[]>("/doctors/"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load doctors");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const filtered = (doctors ?? []).filter((d) => {
    const matchesQuery =
      !query ||
      `${d.first_name} ${d.last_name}`.toLowerCase().includes(query.toLowerCase()) ||
      d.specialization_display.toLowerCase().includes(query.toLowerCase());
    const matchesSpecialty = specialty === "All" || d.specialization_display === specialty;
    return matchesQuery && matchesSpecialty;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Doctors"
        description="Browse our network of specialists."
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1 sm:max-w-xs">
          <Search01Icon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-stone-400" />
          <input
            type="search"
            placeholder="Search doctors…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-10 w-full rounded-full border border-hairline bg-canvas pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
          />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {SPECIALTIES.map((s) => (
            <button
              key={s}
              onClick={() => setSpecialty(s)}
              className={cn(
                "rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
                specialty === s
                  ? "bg-action text-white"
                  : "bg-white text-stone-600 ring-1 ring-stone-200 hover:bg-stone-50 dark:bg-stone-900 dark:text-stone-400 dark:ring-stone-700 dark:hover:bg-stone-800"
              )}
            >
              {s === "General Practice" ? "General" : s}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <section className="rounded-[18px] border border-hairline bg-canvas dark:border-stone-800 dark:bg-stone-900">
          <ErrorState message={error} onRetry={load} />
        </section>
      ) : !doctors ? (
        <section className="rounded-[18px] border border-hairline bg-canvas p-5 dark:border-stone-800 dark:bg-stone-900">
          <LoadingRows rows={5} />
        </section>
      ) : filtered.length === 0 ? (
        <section className="rounded-[18px] border border-hairline bg-canvas dark:border-stone-800 dark:bg-stone-900">
          <EmptyState icon={Doctor01Icon} title="No doctors found" description="Try adjusting your search or filters." />
        </section>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((d) => (
            <div key={d.id} className="flex flex-col rounded-[18px] border border-hairline bg-canvas p-5 transition-colors hover:bg-pearl dark:border-stone-800 dark:bg-stone-900">
              <div className="flex items-start gap-3">
                <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                  {initials(d.first_name, d.last_name)}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="truncate text-sm font-semibold text-stone-900 dark:text-stone-50">
                    Dr. {d.first_name} {d.last_name}
                  </h3>
                  <p className="truncate text-xs text-emerald-600 dark:text-emerald-400">{d.specialization_display}</p>
                </div>
                <span
                  className={cn(
                    "flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
                    d.is_available
                      ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                      : "bg-stone-100 text-stone-500 dark:bg-stone-800 dark:text-stone-400"
                  )}
                >
                  {d.is_available ? <CheckmarkCircle02Icon className="size-3" /> : <CancelCircleIcon className="size-3" />}
                  {d.is_available ? "Available" : "Away"}
                </span>
              </div>
              <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-stone-500 dark:text-stone-400">
                {d.bio || "No biography provided yet."}
              </p>
              <div className="mt-4 flex items-center justify-between border-t border-stone-100 pt-3 dark:border-stone-800">
                <span className="text-xs text-stone-500 dark:text-stone-400">{d.years_of_experience} years experience</span>
                <span className="text-sm font-semibold text-stone-900 dark:text-stone-50">{formatFee(d.consultation_fee)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
