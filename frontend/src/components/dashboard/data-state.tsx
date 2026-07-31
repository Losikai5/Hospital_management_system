import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircleIcon, InboxIcon } from "hugeicons-react";

export function LoadingRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full rounded-lg" />
      ))}
    </div>
  );
}

export function EmptyState({
  icon: Icon = InboxIcon,
  title,
  description,
  action,
}: {
  icon?: typeof InboxIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-stone-100 text-stone-400 dark:bg-stone-800 dark:text-stone-500">
        <Icon className="size-6" />
      </div>
      <h3 className="text-sm font-semibold text-stone-900 dark:text-stone-50">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-stone-500 dark:text-stone-400">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-red-50 text-red-500 dark:bg-red-950/30 dark:text-red-400">
        <AlertCircleIcon className="size-6" />
      </div>
      <h3 className="text-sm font-semibold text-stone-900 dark:text-stone-50">Couldn&apos;t load data</h3>
      <p className="mt-1 max-w-sm text-sm text-stone-500 dark:text-stone-400">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 rounded-lg border border-stone-200 px-3.5 py-1.5 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-50 dark:border-stone-700 dark:text-stone-300 dark:hover:bg-stone-800"
        >
          Try again
        </button>
      )}
    </div>
  );
}
