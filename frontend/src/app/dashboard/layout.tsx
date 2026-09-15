"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { navForUser } from "@/lib/nav";
import { useAuth } from "@/lib/auth-context";
import { Logout04Icon, Cancel01Icon, Menu01Icon } from "hugeicons-react";

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  if (!user) return null;

  const items = navForUser(user);

  return (
    <div className="flex h-full flex-col">
      <Link href="/dashboard" className="flex h-16 items-center gap-2.5 border-b border-stone-200/70 px-5 dark:border-stone-800" onClick={onNavigate}>
        <div className="flex size-8 items-center justify-center rounded-[10px] bg-emerald-600 text-sm font-bold text-white shadow-sm dark:bg-emerald-500">
          S
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-stone-900 dark:text-stone-50">
          Serenity Health
        </span>
      </Link>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        <div className="mb-2 px-2 text-[11px] font-medium uppercase tracking-wider text-stone-400 dark:text-stone-500">
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
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                  : "text-stone-600 hover:bg-stone-100 hover:text-stone-900 dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-stone-50"
              )}
            >
              <item.icon className="size-[18px]" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-stone-200/70 p-3 dark:border-stone-800">
        <Link
          href="/dashboard/profile"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-stone-100 dark:hover:bg-stone-800"
        >
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
            {user.first_name?.[0] ?? user.email[0]?.toUpperCase() ?? "U"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-stone-900 dark:text-stone-50">
              {user.first_name || user.email}
            </div>
            <div className="truncate text-xs text-stone-500 dark:text-stone-400">{user.role}</div>
          </div>
        </Link>
        <button
          onClick={logout}
          className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-stone-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-stone-400 dark:hover:bg-red-950/30 dark:hover:text-red-400"
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
      <div className="flex min-h-[100dvh] items-center justify-center bg-stone-50 dark:bg-stone-950">
        <div className="size-8 animate-spin rounded-full border-2 border-emerald-600/30 border-t-emerald-600" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-[100dvh] bg-stone-50 dark:bg-stone-950">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-stone-200/70 bg-white lg:block dark:border-stone-800 dark:bg-stone-900">
        <SidebarContent />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-stone-900/40 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white shadow-2xl dark:bg-stone-900">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-4 rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-600 dark:hover:bg-stone-800"
              aria-label="Close menu"
            >
              <Cancel01Icon className="size-5" />
            </button>
            <SidebarContent onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-stone-200/70 bg-white/80 px-4 backdrop-blur-xl sm:px-6 dark:border-stone-800 dark:bg-stone-900/80">
          <button
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-stone-500 hover:bg-stone-100 dark:hover:bg-stone-800 lg:hidden"
            aria-label="Open menu"
          >
            <Menu01Icon className="size-5" />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <span className="hidden text-xs font-medium text-stone-400 md:block dark:text-stone-500">
              {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
            </span>
            {isLoading || !isAuthenticated ? null : null}
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
