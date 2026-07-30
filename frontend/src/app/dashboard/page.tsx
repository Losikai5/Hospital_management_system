"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "motion/react";
import {
  Appointment01Icon,
  MedicalFileIcon,
  Doctor01Icon,
  PillIcon,
  Logout04Icon,
  Settings01Icon,
  Calendar01Icon,
} from "hugeicons-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading, isAuthenticated, logout } = useAuth();

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

  if (!user) return null;

  return (
    <div className="flex min-h-[100dvh] flex-col bg-stone-50 dark:bg-stone-950">
      <header className="sticky top-0 z-50 border-b border-stone-200/80 bg-white/70 backdrop-blur-xl dark:border-stone-800/50 dark:bg-stone-950/70">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-[10px] bg-emerald-600 text-sm font-bold text-white shadow-sm dark:bg-emerald-500">
              S
            </div>
            <span className="text-[15px] font-semibold tracking-tight text-stone-900 dark:text-stone-50">
              Serenity Health
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-stone-500 sm:block dark:text-stone-400">
              {user.email}
            </span>
            <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
              {user.role}
            </span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-sm font-medium text-stone-600 shadow-sm transition-colors hover:bg-stone-50 hover:text-stone-900 active:bg-stone-100 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-300 dark:hover:bg-stone-700 dark:hover:text-stone-100"
            >
              <Logout04Icon className="size-4" />
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-10 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        >
          <h1 className="text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50">
            Welcome back{user.first_name ? `, ${user.first_name}` : ""}
          </h1>
          <p className="mt-1 text-sm text-stone-500 dark:text-stone-400">
            Here is an overview of your account.
          </p>
        </motion.div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { icon: Appointment01Icon, label: "Upcoming appointments", value: "—" },
            { icon: MedicalFileIcon, label: "Medical records", value: "—" },
            { icon: Doctor01Icon, label: "My doctors", value: "—" },
            { icon: PillIcon, label: "Active prescriptions", value: "—" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 + i * 0.05, ease: [0.16, 1, 0.3, 1] }}
              className="rounded-xl border border-stone-200/70 bg-white p-5 shadow-sm dark:border-stone-800 dark:bg-stone-900"
            >
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400">
                  <stat.icon className="size-5" />
                </div>
                <div>
                  <div className="text-lg font-semibold text-stone-900 dark:text-stone-50">
                    {stat.value}
                  </div>
                  <div className="text-xs text-stone-500 dark:text-stone-400">{stat.label}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mt-8"
        >
          <div className="rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900">
            <h2 className="text-base font-semibold text-stone-900 dark:text-stone-50">
              Profile details
            </h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[
                { label: "Email", value: user.email },
                { label: "Role", value: user.role },
                { label: "First name", value: user.first_name || "—" },
                { label: "Last name", value: user.last_name || "—" },
                { label: "Phone", value: user.phone || "—" },
                { label: "Verified", value: user.is_verified ? "Yes" : "No" },
              ].map((field) => (
                <div key={field.label}>
                  <div className="text-xs text-stone-500 dark:text-stone-400">
                    {field.label}
                  </div>
                  <div className="mt-0.5 text-sm font-medium text-stone-900 dark:text-stone-50">
                    {field.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="mt-6"
        >
          <div className="rounded-xl border border-stone-200/70 bg-white p-6 shadow-sm dark:border-stone-800 dark:bg-stone-900">
            <h2 className="text-base font-semibold text-stone-900 dark:text-stone-50">
              Quick actions
            </h2>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button variant="outline" size="sm" className="gap-1.5">
                <Calendar01Icon className="size-4" />
                Book appointment
              </Button>
              <Button variant="outline" size="sm" className="gap-1.5">
                <MedicalFileIcon className="size-4" />
                View records
              </Button>
              <Button variant="outline" size="sm" className="gap-1.5">
                <Settings01Icon className="size-4" />
                Edit profile
              </Button>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
