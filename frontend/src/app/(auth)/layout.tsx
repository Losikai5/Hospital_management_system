"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { BrandPanel } from "@/components/auth/brand-panel";
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
    <div className="grid min-h-[100dvh] lg:grid-cols-2">
      <BrandPanel className="hidden lg:flex" />

      <div className="flex flex-col px-5 py-8 sm:px-8">
        {/* Brand mark for narrow screens (the emerald panel is hidden there) */}
        <div className="flex justify-center lg:hidden">
          <Logo />
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-[25rem]">{children}</div>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          {`© ${new Date().getFullYear()} Serenity Health · Secure hospital management`}
        </p>
      </div>
    </div>
  );
}
