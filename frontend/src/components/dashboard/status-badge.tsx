import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const appointmentStyles: Record<string, string> = {
  PENDING: "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-950/30 dark:text-amber-400 dark:ring-amber-400/20",
  CONFIRMED: "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-400/20",
  COMPLETED: "bg-sky-50 text-sky-700 ring-sky-600/20 dark:bg-sky-950/30 dark:text-sky-400 dark:ring-sky-400/20",
  CANCELLED: "bg-stone-100 text-stone-500 ring-stone-500/20 dark:bg-stone-800/50 dark:text-stone-400 dark:ring-stone-400/20",
  NO_SHOW: "bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-950/30 dark:text-red-400 dark:ring-red-400/20",
};

const prescriptionStyles: Record<string, string> = {
  PENDING: "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-950/30 dark:text-amber-400 dark:ring-amber-400/20",
  DISPENSED: "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-950/30 dark:text-emerald-400 dark:ring-emerald-400/20",
  CANCELLED: "bg-stone-100 text-stone-500 ring-stone-500/20 dark:bg-stone-800/50 dark:text-stone-400 dark:ring-stone-400/20",
};

export function AppointmentStatusBadge({ status }: { status: string }) {
  return (
    <Badge variant="outline" className={cn("border-0 font-medium", appointmentStyles[status] ?? "bg-stone-100 text-stone-600 ring-1 ring-stone-500/20")}>
      {status.replace("_", " ")}
    </Badge>
  );
}

export function PrescriptionStatusBadge({ status }: { status: string | null }) {
  const key = status ?? "PENDING";
  return (
    <Badge variant="outline" className={cn("border-0 font-medium", prescriptionStyles[key] ?? "bg-stone-100 text-stone-600 ring-1 ring-stone-500/20")}>
      {key.replace("_", " ")}
    </Badge>
  );
}

export function LowStockBadge() {
  return (
    <Badge variant="outline" className="border-0 bg-red-50 font-medium text-red-700 ring-1 ring-red-600/20 dark:bg-red-950/30 dark:text-red-400 dark:ring-red-400/20">
      Low stock
    </Badge>
  );
}
