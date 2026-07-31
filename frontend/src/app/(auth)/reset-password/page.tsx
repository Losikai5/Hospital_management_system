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

const schema = z
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

type Form = z.infer<typeof schema>;

function InvalidLink() {
  return (
    <div className="space-y-6">
      <span className="flex size-11 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
        <Cancel01Icon className="size-6" />
      </span>
      <header className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Invalid reset link</h1>
        <p className="text-sm text-muted-foreground">
          This password reset link is missing or malformed. Request a fresh one from the sign-in page.
        </p>
      </header>
      <Button className="h-11 w-full text-sm font-medium" render={<Link href="/forgot-password" />}>
        Request a new link
      </Button>
    </div>
  );
}

function ResetPasswordForm() {
  const router = useRouter();
  const params = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema) });

  if (!uid || !token) return <InvalidLink />;

  const onSubmit = async (data: Form) => {
    setFormError(null);
    setIsSubmitting(true);
    try {
      await apiRequest("/auth/password-reset/confirm/", {
        method: "POST",
        body: {
          uid,
          token,
          new_password: data.password,
          confirm_new_password: data.confirmPassword,
        },
        authenticated: false,
      });
      toast.success("Password reset — you can sign in now");
      router.replace("/login");
    } catch (err) {
      setFormError(
        err instanceof Error && err.message
          ? err.message
          : "This reset link is invalid or has expired. Request a new one."
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
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Set a new password</h1>
        <p className="text-sm text-muted-foreground">Choose a new password for your Serenity Health account.</p>
      </header>

      {formError && <AuthAlert message={formError} />}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <PasswordField
          id="password"
          label="New password"
          autoComplete="new-password"
          autoFocus
          placeholder="Create a strong password"
          error={errors.password?.message}
          {...register("password")}
        />
        <PasswordField
          id="confirmPassword"
          label="Confirm new password"
          autoComplete="new-password"
          placeholder="Re-enter your password"
          error={errors.confirmPassword?.message}
          {...register("confirmPassword")}
        />

        <Button type="submit" className="h-11 w-full text-sm font-medium" disabled={isSubmitting}>
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <span className="size-4 animate-spin rounded-full border-2 border-current/30 border-t-current" />
              Resetting…
            </span>
          ) : (
            "Reset password"
          )}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        <Link href="/login" className="font-medium text-primary underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="h-40 animate-pulse rounded-xl bg-muted" />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
