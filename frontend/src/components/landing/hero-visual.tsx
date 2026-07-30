import {
  Calendar01Icon,
  HospitalLocationIcon,
  Activity01Icon,
  Medicine02Icon,
  CheckmarkCircle02Icon,
} from "hugeicons-react";

/**
 * Product-true hero signature: a small cluster of real UI (an appointment card,
 * a vitals chip, a prescription chip) rendered from the design system — no stock
 * photos, no external assets. Floating chips hide below `sm` to avoid overflow.
 */
export function HeroVisual() {
  return (
    <div className="relative mx-auto w-full max-w-md">
      {/* Depth plate + soft glow */}
      <div className="absolute inset-0 -z-10 translate-x-4 translate-y-5 rounded-[2rem] bg-emerald-600/[0.06] bg-plus-grid ring-1 ring-emerald-600/10" />
      <div className="pointer-events-none absolute -right-8 -top-10 -z-10 size-56 rounded-full bg-emerald-400/20 blur-3xl" />

      {/* Appointment card */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-[0_24px_60px_-28px_rgba(6,78,59,0.4)]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-full bg-emerald-100 text-sm font-semibold text-emerald-700">
              AO
            </span>
            <div>
              <div className="text-sm font-semibold text-foreground">Dr. Amina Osei</div>
              <div className="text-xs text-muted-foreground">Cardiology</div>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-700 ring-1 ring-emerald-600/15">
            <CheckmarkCircle02Icon className="size-3.5" />
            Confirmed
          </span>
        </div>
        <div className="mt-4 space-y-2.5 border-t border-border pt-4 text-sm">
          <div className="flex items-center gap-2.5 text-foreground">
            <Calendar01Icon className="size-4 text-muted-foreground" />
            Tue, 12 Aug · 10:30 AM
          </div>
          <div className="flex items-center gap-2.5 text-foreground">
            <HospitalLocationIcon className="size-4 text-muted-foreground" />
            Ward B · Room 204
          </div>
        </div>
      </div>

      {/* Vitals chip */}
      <div className="absolute -right-5 top-20 hidden w-40 rounded-xl border border-border bg-card p-3 shadow-lg sm:block">
        <div className="flex items-center gap-2">
          <span className="grid size-7 place-items-center rounded-lg bg-emerald-100 text-emerald-700">
            <Activity01Icon className="size-4" />
          </span>
          <span className="text-xs text-muted-foreground">Heart rate</span>
        </div>
        <div className="mt-1.5 flex items-end justify-between">
          <span className="text-lg font-semibold tabular-nums text-foreground">
            72<span className="ml-0.5 text-xs font-normal text-muted-foreground">bpm</span>
          </span>
          <svg viewBox="0 0 64 24" fill="none" className="h-6 w-16 text-emerald-500" aria-hidden>
            <path
              d="M0 12 H16 l4 -8 l5 16 l4 -8 H64"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      {/* Prescription chip */}
      <div className="absolute -bottom-6 -left-6 hidden items-center gap-3 rounded-xl border border-border bg-card p-3 pr-4 shadow-lg sm:flex">
        <span className="grid size-9 place-items-center rounded-lg bg-emerald-100 text-emerald-700">
          <Medicine02Icon className="size-5" />
        </span>
        <div>
          <div className="text-xs font-medium text-foreground">Amoxicillin · 500mg</div>
          <div className="text-[11px] text-emerald-700">Dispensed</div>
        </div>
      </div>
    </div>
  );
}
