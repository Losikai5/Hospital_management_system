import * as React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type TextFieldProps = React.ComponentProps<"input"> & {
  label: string;
  error?: string;
  /** Leading icon (rendered muted inside the field). */
  icon?: React.ReactNode;
};

/**
 * Labelled text input with optional leading icon and inline error.
 * Spreads all input props (including react-hook-form's `register()` ref) onto <Input>.
 */
export function TextField({ label, error, icon, id, className, ...props }: TextFieldProps) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground [&_svg]:size-[18px]">
            {icon}
          </span>
        )}
        <Input
          id={id}
          aria-invalid={error ? true : undefined}
          className={cn("h-11", icon && "pl-10", className)}
          {...props}
        />
      </div>
      {error && (
        <p role="alert" className="text-xs font-medium text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
