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
        <h1 className="text-3xl font-semibold tracking-tight text-ink dark:text-white">{title}</h1>
        {description && (
          <p className="mt-1.5 text-[15px] text-ink-48 dark:text-stone-400">{description}</p>
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
    <div className="rounded-[18px] border border-hairline bg-canvas p-6 transition-colors hover:bg-pearl dark:border-stone-800 dark:bg-stone-900 dark:hover:bg-stone-800/70">
      <div className="flex items-start justify-between">
        <div className="flex size-10 items-center justify-center rounded-[11px] bg-emerald-50 text-action dark:bg-emerald-900/30 dark:text-emerald-300">
          <Icon className="size-5" />
        </div>
        {loading ? (
          <div className="h-4 w-12 animate-pulse rounded-full bg-stone-100 dark:bg-stone-800" />
        ) : (
          sub && <div className="text-xs text-ink-48 dark:text-stone-400">{sub}</div>
        )}
      </div>
      <div className="mt-4">
        {loading ? (
          <div className="h-7 w-16 animate-pulse rounded-full bg-stone-100 dark:bg-stone-800" />
        ) : (
          <div className="text-[1.75rem] font-semibold tracking-tight tabular-nums text-ink dark:text-white">{value}</div>
        )}
        <div className="mt-0.5 text-[13px] text-ink-48 dark:text-stone-400">{label}</div>
      </div>
    </div>
  );
}
