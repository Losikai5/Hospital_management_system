"use client";

import { useState, useEffect, useCallback } from "react";
import { MedicalFileIcon, ArrowDown01Icon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingRows, EmptyState, ErrorState } from "@/components/dashboard/data-state";
import { apiRequest } from "@/lib/api-client";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { MedicalRecord } from "@/lib/types";

export default function RecordsPage() {
  const [records, setRecords] = useState<MedicalRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setRecords(await apiRequest<MedicalRecord[]>("/medical-records/"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load records");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <div className="space-y-6">
      <PageHeader title="Medical records" description="Diagnoses, treatments and clinical notes." />

      <section className="rounded-[18px] border border-hairline bg-canvas dark:border-stone-800 dark:bg-stone-900">
        {!records ? (
          <div className="p-5"><LoadingRows rows={5} /></div>
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : records.length === 0 ? (
          <EmptyState
            icon={MedicalFileIcon}
            title="No medical records"
            description="Clinical notes from your visits will appear here."
          />
        ) : (
          <ul className="divide-y divide-stone-100 dark:divide-stone-800">
            {records.map((r) => (
              <li key={r.id}>
                <button
                  onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                  className="flex w-full items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-stone-50/70 dark:hover:bg-stone-800/40"
                >
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400">
                    <MedicalFileIcon className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-stone-900 dark:text-stone-50">{r.diagnosis}</div>
                    <div className="mt-0.5 truncate text-xs text-stone-500 dark:text-stone-400">
                      {r.doctor_email} · {r.patient_email}
                    </div>
                  </div>
                  <span className="hidden text-xs text-stone-400 sm:block dark:text-stone-500">{formatDate(r.appointment_date)}</span>
                  <ArrowDown01Icon className={cn("size-4 text-stone-400 transition-transform", expanded === r.id && "rotate-180")} />
                </button>
                {expanded === r.id && (
                  <div className="border-t border-stone-100 bg-stone-50/50 px-5 py-4 dark:border-stone-800 dark:bg-stone-800/30">
                    <dl className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <dt className="text-xs font-medium uppercase tracking-wider text-stone-400 dark:text-stone-500">Diagnosis</dt>
                        <dd className="mt-1 text-sm text-stone-800 dark:text-stone-200">{r.diagnosis}</dd>
                      </div>
                      <div>
                        <dt className="text-xs font-medium uppercase tracking-wider text-stone-400 dark:text-stone-500">Treatment prescribed</dt>
                        <dd className="mt-1 text-sm text-stone-800 dark:text-stone-200">{r.treatment_prescribed || "—"}</dd>
                      </div>
                      <div className="sm:col-span-2">
                        <dt className="text-xs font-medium uppercase tracking-wider text-stone-400 dark:text-stone-500">Notes</dt>
                        <dd className="mt-1 text-sm leading-relaxed text-stone-800 dark:text-stone-200">{r.notes || "—"}</dd>
                      </div>
                    </dl>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
