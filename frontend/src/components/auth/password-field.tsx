"use client";

import * as React from "react";
import { useState } from "react";
import { LockPasswordIcon, ViewIcon, ViewOffIcon } from "hugeicons-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type PasswordFieldProps = React.ComponentProps<"input"> & {
  label: string;
  error?: string;
};

/**
 * Labelled password input with a leading lock icon and a show/hide toggle.
 * Spreads all input props (including react-hook-form's `register()` ref) onto <Input>.
 */
export function PasswordField({ label, error, id, className, ...props }: PasswordFieldProps) {
  const [show, setShow] = useState(false);

  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
          <LockPasswordIcon className="size-[18px]" />
        </span>
        <Input
          id={id}
          type={show ? "text" : "password"}
          aria-invalid={error ? true : undefined}
          className={cn("h-11 pl-10 pr-10", className)}
          {...props}
        />
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          aria-label={show ? "Hide password" : "Show password"}
          className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          tabIndex={-1}
        >
          {show ? <ViewOffIcon className="size-[18px]" /> : <ViewIcon className="size-[18px]" />}
        </button>
      </div>
      {error && (
        <p role="alert" className="text-xs font-medium text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
