"use client";

import { motion, useReducedMotion } from "motion/react";
import { CheckmarkCircle02Icon } from "hugeicons-react";
import { Logo } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

const POINTS = [
  "Role-based access for every team",
  "Encrypted, always-available records",
  "Appointments, records & pharmacy in one place",
];

/**
 * The emerald brand column of the auth split-screen.
 * Display is controlled by the caller (e.g. `hidden lg:flex`).
 */
export function BrandPanel({ className }: { className?: string }) {
  const reduce = useReducedMotion();

  return (
    <div
      className={cn(
        "relative flex-col justify-between overflow-hidden px-10 py-12 text-white",
        className
      )}
    >
      {/* Layered emerald background + medical-cross motif + soft glow */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-emerald-600 via-emerald-800 to-emerald-950" />
      <div className="pointer-events-none absolute inset-0 bg-plus-grid-invert" />
      <div className="pointer-events-none absolute -right-28 -top-28 size-96 rounded-full bg-emerald-400/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -left-24 size-80 rounded-full bg-emerald-300/10 blur-3xl" />

      <div className="relative z-10">
        <Logo variant="light" />
      </div>

      <div className="relative z-10 max-w-md">
        <h2 className="text-4xl font-semibold leading-[1.05] tracking-tight">
          Care, coordinated.
        </h2>
        <p className="mt-5 text-[15px] leading-relaxed text-emerald-50/85">
          Serenity brings appointments, records, doctors, and pharmacy into one
          calm, secure system — so your team spends less time on software and
          more on people.
        </p>
        <ul className="mt-8 space-y-3.5">
          {POINTS.map((point) => (
            <li key={point} className="flex items-center gap-3 text-sm text-emerald-50/90">
              <CheckmarkCircle02Icon className="size-5 shrink-0 text-emerald-300" />
              {point}
            </li>
          ))}
        </ul>
      </div>

      <div className="relative z-10">
        <svg
          viewBox="0 0 320 40"
          fill="none"
          className="h-9 w-full max-w-[18rem] text-emerald-300/70"
          aria-hidden
        >
          <motion.path
            d="M0 20 H58 l7 -13 l10 26 l7 -13 H150 l7 -13 l10 26 l7 -13 H320"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={reduce ? undefined : { pathLength: 0, opacity: 0 }}
            animate={reduce ? undefined : { pathLength: 1, opacity: 1 }}
            transition={{ duration: 2.2, ease: "easeInOut" }}
          />
        </svg>
        <p className="mt-3 text-xs text-emerald-200/70">
          Built around care, not paperwork.
        </p>
      </div>
    </div>
  );
}
