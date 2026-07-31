"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Mail01Icon } from "hugeicons-react";
import { Button } from "@/components/ui/button";
import { TextField } from "@/components/auth/text-field";
import { AuthAlert } from "@/components/auth/auth-alert";
import { apiRequest } from "@/lib/api-client";

const schema = z.object({ email: z.string().email("Enter a valid email address") });
type Form = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: Form) => {
    setFormError(null);
    setIsSubmitting(true);
    try {
      await apiRequest("/auth/password-reset/", {
        method: "POST",
        body: { email: data.email },
        authenticated: false,
      });
      setSent(true);
    } catch (err) {
      setFormError(
        err instanceof Error && err.message ? err.message : "Something went wrong. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (sent) {
    return (
      <div className="space-y-6">
        <header className="space-y-1.5">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Check your email</h1>
          <p className="text-sm text-muted-foreground">
            If an account exists for that address, we&apos;ve sent a link to reset your password. The link expires in a few days.
          </p>
        </header>
        <AuthAlert variant="success" message="Reset link sent — check your inbox (and spam)." />
        <Button className="h-11 w-full text-sm font-medium" render={<Link href="/login" />}>
          Back to sign in
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Forgot your password?</h1>
        <p className="text-sm text-muted-foreground">
          Enter your email and we&apos;ll send you a link to set a new one.
        </p>
      </header>

      {formError && <AuthAlert message={formError} />}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <TextField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          autoFocus
          placeholder="you@example.com"
          icon={<Mail01Icon />}
          error={errors.email?.message}
          {...register("email")}
        />
        <Button type="submit" className="h-11 w-full text-sm font-medium" disabled={isSubmitting}>
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <span className="size-4 animate-spin rounded-full border-2 border-current/30 border-t-current" />
              Sending…
            </span>
          ) : (
            "Send reset link"
          )}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Remembered it?{" "}
        <Link href="/login" className="font-medium text-primary underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
