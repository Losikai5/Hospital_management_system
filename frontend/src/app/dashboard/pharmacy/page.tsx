"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { PillIcon, PackageIcon, CheckmarkCircle02Icon } from "hugeicons-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingRows, EmptyState, ErrorState } from "@/components/dashboard/data-state";
import { PrescriptionStatusBadge, LowStockBadge } from "@/components/dashboard/status-badge";
import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Medicine, Prescription } from "@/lib/types";

type Tab = "prescriptions" | "medicines";

export default function PharmacyPage() {
  const { user, hasPermission } = useAuth();
  const [tab, setTab] = useState<Tab>("prescriptions");
  const [medicines, setMedicines] = useState<Medicine[] | null>(null);
  const [prescriptions, setPrescriptions] = useState<Prescription[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadAll = useCallback(async () => {
    setError(null);
    try {
      const [med, rx] = await Promise.all([
        apiRequest<Medicine[]>("/pharmacy/medicines/"),
        apiRequest<Prescription[]>("/pharmacy/prescriptions/"),
      ]);
      setMedicines(med);
      setPrescriptions(rx);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pharmacy data");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void loadAll(); }, 0);
    return () => window.clearTimeout(timer);
  }, [loadAll]);

  const dispense = async (id: number) => {
    setBusyId(id);
    try {
      await apiRequest(`/pharmacy/prescriptions/${id}/dispense/`, { method: "POST", authenticated: true });
      toast.success("Prescription dispensed");
      await loadAll();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Dispense failed");
    } finally {
      setBusyId(null);
    }
  };

  if (!user) return null;
  const canDispense = hasPermission("can_dispense_prescriptions");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pharmacy"
        description="Medicines inventory and prescription fulfillment."
      />

      <div className="flex gap-2">
        {(["prescriptions", "medicines"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm font-medium capitalize transition-colors",
              tab === t
                ? "bg-action text-white"
                : "bg-white text-stone-600 ring-1 ring-stone-200 hover:bg-stone-50 dark:bg-stone-900 dark:text-stone-400 dark:ring-stone-700 dark:hover:bg-stone-800"
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <section className="rounded-[18px] border border-hairline bg-canvas dark:border-stone-800 dark:bg-stone-900">
        {error ? (
          <ErrorState message={error} onRetry={loadAll} />
        ) : !medicines || !prescriptions ? (
          <div className="p-5"><LoadingRows rows={5} /></div>
        ) : tab === "medicines" ? (
          medicines.length === 0 ? (
            <EmptyState icon={PackageIcon} title="No medicines in inventory" description="Medicines added by pharmacy staff will appear here." />
          ) : (
            <ul className="divide-y divide-stone-100 dark:divide-stone-800">
              {medicines.map((m) => (
                <li key={m.id} className="flex items-center gap-4 px-5 py-4">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400">
                    <PackageIcon className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-stone-900 dark:text-stone-50">{m.name}</div>
                    <div className="mt-0.5 truncate text-xs text-stone-500 dark:text-stone-400">
                      {m.description || (m.unit_cost ? `$${m.unit_cost} per ${m.unit_type ?? "unit"}` : m.unit_type ?? "—")}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-stone-900 dark:text-stone-50">
                      {m.stock_quantity ?? 0} <span className="text-xs font-normal text-stone-400">{m.unit_type ?? ""}</span>
                    </div>
                    <div className="text-[11px] text-stone-400 dark:text-stone-500">
                      {m.unit_cost ? `$${m.unit_cost}/unit` : "—"}
                    </div>
                  </div>
                  {m.is_low_stock && <LowStockBadge />}
                </li>
              ))}
            </ul>
          )
        ) : prescriptions.length === 0 ? (
          <EmptyState icon={PillIcon} title="No prescriptions" description="Prescriptions written by doctors will appear here." />
        ) : (
          <ul className="divide-y divide-stone-100 dark:divide-stone-800">
            {prescriptions.map((p) => (
              <li key={p.id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2">
                    <span className="text-sm font-semibold text-stone-900 dark:text-stone-50">{p.medicine_name}</span>
                    <span className="text-xs text-stone-400">·</span>
                    <span className="text-xs text-stone-500 dark:text-stone-400">
                      {p.dosage} · {p.frequency} · {p.duration}
                    </span>
                  </div>
                  <div className="mt-0.5 truncate text-xs text-stone-500 dark:text-stone-400">
                    {p.patient_email} · Dr. {p.doctor_email}
                  </div>
                  <div className="mt-0.5 text-[11px] text-stone-400 dark:text-stone-500">
                    {formatDateTime(p.prescribed_at)} · Qty {p.quantity_prescribed} {p.medicine_unit}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <PrescriptionStatusBadge status={p.status} />
                  {canDispense && p.status === "PENDING" && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1 text-emerald-700 dark:text-emerald-400"
                      disabled={busyId === p.id}
                      onClick={() => dispense(p.id)}
                    >
                      <CheckmarkCircle02Icon className="size-3.5" />
                      Dispense
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
