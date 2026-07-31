"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AuthBackdrop } from "@/components/auth/auth-backdrop";
import { Logo } from "@/components/brand/logo";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  // Signed-in users have no business on the auth screens.
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isLoading, isAuthenticated, router]);

  return (
    <div className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden bg-stone-50 px-4 py-10">
      <AuthBackdrop />

      <div className="animate-rise relative z-10 w-full max-w-md">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <Logo href="/" />
          <p className="text-sm text-muted-foreground">One calm system for the whole hospital.</p>
        </div>

        <div className="rounded-2xl border border-stone-200/80 bg-white/90 p-8 shadow-[0_24px_70px_-24px_rgba(6,78,59,0.28)] backdrop-blur-sm">
          {children}
        </div>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          {`© ${new Date().getFullYear()} Serenity Health · Secure hospital management`}
        </p>
      </div>
    </div>
  );
}
