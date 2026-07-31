"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { SecurityValidationIcon, Cancel01Icon } from "hugeicons-react";
import { Button } from "@/components/ui/button";
import { PasswordField } from "@/components/auth/password-field";
import { AuthAlert } from "@/components/auth/auth-alert";
import { apiRequest } from "@/lib/api-client";

const acceptSchema = z
  .object({
    password: z
      .string()
      .min(8, "Use at least 8 characters")
      .regex(/[A-Za-z]/, "Include at least one letter")
      .regex(/[0-9]/, "Include at least one number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type AcceptForm = z.infer<typeof acceptSchema>;

function InvalidLink() {
  return (
    <div className="space-y-6">
      <span className="flex size-11 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
        <Cancel01Icon className="size-6" />
      </span>
      <header className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Invalid invitation</h1>
        <p className="text-sm text-muted-foreground">
          This invitation link is missing or malformed. Ask your administrator to send a new one.
        </p>
      </header>
      <Button className="h-11 w-full text-sm font-medium" render={<Link href="/login" />}>
        Go to sign in
      </Button>
    </div>
  );
}

function AcceptInvitationForm() {
  const router = useRouter();
  const token = useSearchParams().get("token");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AcceptForm>({ resolver: zodResolver(acceptSchema) });

  if (!token) return <InvalidLink />;

  const onSubmit = async (data: AcceptForm) => {
    setFormError(null);
    setIsSubmitting(true);
    try {
      await apiRequest("/staff/invitations/accept/", {
        method: "POST",
        body: { token, password: data.password, confirm_password: data.confirmPassword },
        authenticated: false,
      });
      toast.success("Account activated — you can sign in now");
      router.replace("/login");
    } catch (err) {
      setFormError(
        err instanceof Error && err.message
          ? err.message
          : "This invitation could not be accepted. It may have expired."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <span className="flex size-11 items-center justify-center rounded-xl bg-accent text-accent-foreground">
        <SecurityValidationIcon className="size-6" />
      </span>
      <header className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Set your password</h1>
        <p className="text-sm text-muted-foreground">
          You&apos;ve been invited to Serenity Health. Choose a password to activate your staff account.
        </p>
      </header>

      {formError && <AuthAlert message={formError} />}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <PasswordField
          id="password"
          label="Password"
          autoComplete="new-password"
          autoFocus
          placeholder="Create a strong password"
          error={errors.password?.message}
          {...register("password")}
        />
        <PasswordField
          id="confirmPassword"
          label="Confirm password"
          autoComplete="new-password"
          placeholder="Re-enter your password"
          error={errors.confirmPassword?.message}
          {...register("confirmPassword")}
        />

        <Button type="submit" className="h-11 w-full text-sm font-medium" disabled={isSubmitting}>
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <span className="size-4 animate-spin rounded-full border-2 border-current/30 border-t-current" />
              Activating…
            </span>
          ) : (
            "Activate account"
          )}
        </Button>
      </form>
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={<div className="h-40 animate-pulse rounded-xl bg-muted" />}>
      <AcceptInvitationForm />
    </Suspense>
  );
}
