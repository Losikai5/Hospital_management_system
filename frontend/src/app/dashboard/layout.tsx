"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { navForUser } from "@/lib/nav";
import { useAuth } from "@/lib/auth-context";
import { AiChatWidget } from "@/components/ai/ai-chat-widget";
import { Logout04Icon, Cancel01Icon, Menu01Icon } from "hugeicons-react";

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  if (!user) return null;

  const items = navForUser(user);

  return (
    <div className="flex h-full flex-col">
      <Link
        href="/dashboard"
        className="flex h-16 items-center gap-2.5 border-b border-white/10 px-5"
        onClick={onNavigate}
      >
        <div className="flex size-8 items-center justify-center rounded-[10px] bg-action text-sm font-bold text-white">
          S
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-white">
          Serenity Health
        </span>
      </Link>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        <div className="mb-2 px-2 text-[11px] font-medium uppercase tracking-wider text-white/40">
          Menu
        </div>
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-full px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-action text-white"
                  : "text-white/70 hover:bg-white/10 hover:text-white"
              )}
            >
              <item.icon className="size-[18px]" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-3">
        <Link
          href="/dashboard/profile"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-full px-3 py-2 transition-colors hover:bg-white/10"
        >
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-action text-xs font-semibold text-white">
            {user.first_name?.[0] ?? user.email[0]?.toUpperCase() ?? "U"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-white">
              {user.first_name || user.email}
            </div>
            <div className="truncate text-xs text-white/50">{user.role}</div>
          </div>
        </Link>
        <button
          onClick={logout}
          className="mt-1 flex w-full items-center gap-3 rounded-full px-3 py-2 text-sm font-medium text-white/50 transition-colors hover:bg-red-500/15 hover:text-red-300"
        >
          <Logout04Icon className="size-[18px]" />
          Sign out
        </button>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-parchment dark:bg-stone-950">
        <div className="size-8 animate-spin rounded-full border-2 border-action/30 border-t-action" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-[100dvh] bg-canvas dark:bg-stone-950">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 bg-ink lg:block dark:bg-ink">
        <SidebarContent />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-ink">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-4 z-10 rounded-full p-1.5 text-white/60 hover:bg-white/10 hover:text-white"
              aria-label="Close menu"
            >
              <Cancel01Icon className="size-5" />
            </button>
            <SidebarContent onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="frosted sticky top-0 z-30 flex h-14 items-center justify-between border-b border-hairline/60 px-4 sm:px-6">
          <button
            onClick={() => setMobileOpen(true)}
            className="rounded-full p-2 text-ink-48 hover:bg-stone-100 dark:hover:bg-stone-800 lg:hidden"
            aria-label="Open menu"
          >
            <Menu01Icon className="size-5" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <span className="hidden text-xs font-normal text-ink-48 md:block">
              {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
            </span>
            {isLoading || !isAuthenticated ? null : null}
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      </div>
      <AiChatWidget />
    </div>
  );
}