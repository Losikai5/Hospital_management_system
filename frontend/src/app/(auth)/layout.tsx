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
    <div className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden bg-parchment px-4 py-10">
      <AuthBackdrop />

      <div className="animate-rise relative z-10 w-full max-w-md">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <Logo href="/" />
          <p className="text-sm text-ink-48">One calm system for the whole hospital.</p>
        </div>

        <div className="rounded-[18px] border border-hairline bg-white/90 p-8 backdrop-blur-sm dark:border-stone-800 dark:bg-stone-900/90">
          {children}
        </div>

        <p className="mt-6 text-center text-xs text-ink-48">
          {`© ${new Date().getFullYear()} Serenity Health · Secure hospital management`}
        </p>
      </div>
    </div>
  );
}
