"use client";

import { motion, useReducedMotion } from "motion/react";
import { CheckmarkCircle02Icon, Activity01Icon, Medicine02Icon } from "hugeicons-react";

/**
 * Ambient animated backdrop for the auth screens. Deliberately quiet: a layered
 * emerald/teal glow, the "+" motif, slowly drifting orbs and a few faint, gently
 * bobbing chips — atmosphere, not the focus. Fully static under reduced-motion.
 */
export function AuthBackdrop() {
  const reduce = useReducedMotion();

  const drift = (duration: number, x: number, y: number) =>
    reduce
      ? {}
      : {
          animate: { x: [0, x, 0], y: [0, -y, 0], scale: [1, 1.04, 1] },
          transition: { duration, repeat: Infinity, ease: "easeInOut" as const },
        };

  const bob = (duration: number, delay = 0) =>
    reduce
      ? {}
      : {
          animate: { y: [0, -8, 0] },
          transition: { duration, repeat: Infinity, ease: "easeInOut" as const, delay },
        };

  const chip =
    "rounded-xl bg-white/55 shadow-sm ring-1 ring-stone-900/[0.04] backdrop-blur-md";

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {/* Layered glow base — the richer, calmer background */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(55rem 55rem at 10% -8%, rgba(16,185,129,0.13), transparent 60%), radial-gradient(48rem 48rem at 106% 110%, rgba(13,148,136,0.11), transparent 55%)",
        }}
      />
      <div className="absolute inset-0 bg-plus-grid opacity-40" />
      {/* Soft vignette so the centre (the card) reads as the focus */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(85rem 58rem at 50% 42%, transparent 56%, rgba(28,25,23,0.05))",
        }}
      />

      {/* Drifting orbs — slow and low-contrast */}
      <motion.div
        className="absolute -left-24 top-0 size-80 rounded-full bg-emerald-400/15 blur-3xl"
        {...drift(30, 16, 12)}
      />
      <motion.div
        className="absolute -right-28 bottom-0 size-[26rem] rounded-full bg-teal-400/[0.12] blur-3xl"
        {...drift(38, 18, 14)}
      />
      <motion.div
        className="absolute -bottom-24 left-1/3 size-72 rounded-full bg-emerald-300/10 blur-3xl"
        {...drift(34, 12, 10)}
      />

      {/* Faint floating chips — ambient, tucked to the edges (desktop only) */}
      <motion.div className={`absolute left-[8%] top-[22%] hidden w-52 p-3 lg:block ${chip}`} {...bob(8)}>
        <div className="flex items-center gap-2.5">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-emerald-100/70 text-emerald-600">
            <CheckmarkCircle02Icon className="size-4" />
          </span>
          <div>
            <div className="text-xs font-medium text-stone-600">Appointment confirmed</div>
            <div className="text-[11px] text-stone-400">Tue, 12 Aug · 10:30 AM</div>
          </div>
        </div>
      </motion.div>

      <motion.div className={`absolute right-[9%] top-[30%] hidden w-36 p-3 lg:block ${chip}`} {...bob(9, 0.7)}>
        <div className="flex items-center gap-2">
          <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-emerald-100/70 text-emerald-600">
            <Activity01Icon className="size-4" />
          </span>
          <span className="text-xs text-stone-400">Heart rate</span>
        </div>
        <div className="mt-1 flex items-end justify-between">
          <span className="text-base font-semibold tabular-nums text-stone-700">
            72<span className="ml-0.5 text-[10px] font-normal text-stone-400">bpm</span>
          </span>
          <svg viewBox="0 0 48 20" fill="none" className="h-5 w-12 text-emerald-500/70">
            <path
              d="M0 10 H12 l3 -6 l4 12 l3 -6 H48"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </motion.div>

      <motion.div
        className={`absolute bottom-[19%] left-[12%] hidden items-center gap-2.5 p-3 pr-4 lg:flex ${chip}`}
        {...bob(8.5, 1.2)}
      >
        <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-emerald-100/70 text-emerald-600">
          <Medicine02Icon className="size-4" />
        </span>
        <div>
          <div className="text-xs font-medium text-stone-600">Prescription ready</div>
          <div className="text-[11px] text-stone-400">Amoxicillin · 500mg</div>
        </div>
      </motion.div>
    </div>
  );
}
