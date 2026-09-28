"use client";

import Link from "next/link";
import { UserEdit01Icon, ArrowRight01Icon } from "hugeicons-react";
import { useAuth } from "@/lib/auth-context";

/**
 * Nudges any user (patient or invited staff) to fill in their CustomUser
 * details after logging in. Renders nothing once name + phone + DOB are set.
 * Everything saves via PATCH /auth/profile/ on the profile page.
 */
export function ProfileCompletionBanner() {
  const { user } = useAuth();
  if (!user) return null;

  const missing: string[] = [];
  if (!user.first_name || !user.last_name) missing.push("your name");
  if (!user.phone) missing.push("phone number");
  if (!user.date_of_birth) missing.push("date of birth");

  if (missing.length === 0) return null;

  const list =
    missing.length === 1
      ? missing[0]
      : `${missing.slice(0, -1).join(", ")} and ${missing[missing.length - 1]}`;

  return (
    <div className="flex flex-col gap-3 rounded-[18px] border border-hairline bg-emerald-50 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-emerald-900/50 dark:bg-emerald-950/30">
      <div className="flex items-start gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-300">
          <UserEdit01Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <div className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">
            Complete your profile
          </div>
          <div className="text-sm text-emerald-800/80 dark:text-emerald-300/80">
            Add {list} so the care team can identify you.
          </div>
        </div>
      </div>
      <Button href="/dashboard/profile" />
    </div>
  );
}

function Button({ href }: { href: string }) {
  return (
    <Link
      href={href}
      className="press-active inline-flex shrink-0 items-center justify-center gap-1.5 rounded-full bg-action px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-focus"
    >
      Complete profile
      <ArrowRight01Icon className="size-4" />
    </Link>
  );
}
