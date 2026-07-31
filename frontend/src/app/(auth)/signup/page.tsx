"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Mail01Icon } from "hugeicons-react";
import { Button } from "@/components/ui/button";
import { TextField } from "@/components/auth/text-field";
import { PasswordField } from "@/components/auth/password-field";
import { AuthAlert } from "@/components/auth/auth-alert";
import { useAuth } from "@/lib/auth-context";

const signupSchema = z
  .object({
    email: z.string().email("Enter a valid email address"),
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

type SignupForm = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const router = useRouter();
  const { register: registerUser, login } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupForm>({ resolver: zodResolver(signupSchema) });

  const onSubmit = async (data: SignupForm) => {
    setFormError(null);
    setIsSubmitting(true);
    try {
      await registerUser(data.email, data.password, data.confirmPassword);
      await login(data.email, data.password);
      toast.success("Welcome to Serenity Health");
      router.replace("/dashboard");
    } catch (err) {
      setFormError(
        err instanceof Error && err.message
          ? err.message
          : "We couldn't create your account. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <header className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Create your account
        </h1>
        <p className="text-sm text-muted-foreground">
          Set up a free patient account to book appointments and view your records.
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
        <PasswordField
          id="password"
          label="Password"
          autoComplete="new-password"
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
              Creating account…
            </span>
          ) : (
            "Create account"
          )}
        </Button>
      </form>

      <div className="rounded-lg border border-border bg-muted/50 px-3.5 py-2.5 text-xs leading-relaxed text-muted-foreground">
        Clinical staff don&apos;t sign up here — doctors, receptionists, and pharmacists
        receive an email invitation from an administrator.
      </div>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-primary underline-offset-4 hover:underline"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
