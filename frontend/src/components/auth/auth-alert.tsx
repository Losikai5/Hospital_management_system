import { AlertCircleIcon, CheckmarkCircle02Icon } from "hugeicons-react";
import { cn } from "@/lib/utils";

type AuthAlertProps = {
  message: string;
  variant?: "error" | "success" | "info";
};

const STYLES = {
  error: "border-destructive/30 bg-destructive/10 text-destructive",
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  info: "border-border bg-muted text-muted-foreground",
} as const;

export function AuthAlert({ message, variant = "error" }: AuthAlertProps) {
  const Icon = variant === "success" ? CheckmarkCircle02Icon : AlertCircleIcon;
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-sm",
        STYLES[variant]
      )}
    >
      <Icon className="mt-0.5 size-[18px] shrink-0" />
      <span>{message}</span>
    </div>
  );
}
