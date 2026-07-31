import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function PageHeader({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between", className)}>
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-stone-500 dark:text-stone-400">{description}</p>
        )}
      </div>
      {action && <div className="flex shrink-0 items-center gap-2">{action}</div>}
    </div>
  );
}

export function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  loading,
}: {
  icon: typeof import("hugeicons-react").DashboardSquare02Icon;
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  loading?: boolean;
}) {
  return (
    <div className="rounded-xl border border-stone-200/70 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-stone-800 dark:bg-stone-900">
      <div className="flex items-start justify-between">
        <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400">
          <Icon className="size-5" />
        </div>
        {loading ? (
          <div className="h-4 w-12 animate-pulse rounded bg-stone-100 dark:bg-stone-800" />
        ) : (
          sub && <div className="text-xs text-stone-400 dark:text-stone-500">{sub}</div>
        )}
      </div>
      <div className="mt-4">
        {loading ? (
          <div className="h-7 w-16 animate-pulse rounded bg-stone-100 dark:bg-stone-800" />
        ) : (
          <div className="text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50">{value}</div>
        )}
        <div className="mt-0.5 text-xs text-stone-500 dark:text-stone-400">{label}</div>
      </div>
    </div>
  );
}
