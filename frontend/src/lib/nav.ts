import {
  Calendar01Icon,
  DashboardSquare02Icon,
  Doctor01Icon,
  MedicalFileIcon,
  PackageIcon,
  PillIcon,
  UserCircleIcon,
  UserGroupIcon,
} from "hugeicons-react";
import type { AuthUser } from "./auth-context";

const items = [
  { href: "/dashboard", label: "Overview", icon: DashboardSquare02Icon },
  { href: "/dashboard/appointments", label: "Appointments", icon: Calendar01Icon },
  { href: "/dashboard/doctors", label: "Doctors", icon: Doctor01Icon },
  { href: "/dashboard/records", label: "Medical records", icon: MedicalFileIcon },
  { href: "/dashboard/pharmacy", label: "Pharmacy", icon: PillIcon },
  { href: "/dashboard/billing", label: "Billing", icon: PackageIcon },
  { href: "/dashboard/staff", label: "Staff", icon: UserGroupIcon },
  { href: "/dashboard/profile", label: "My profile", icon: UserCircleIcon },
];

export function navForUser(user: AuthUser) {
  const isAdmin = (user.is_superuser ?? false) || user.roles.includes("ADMIN");
  const has = (permission: string) => isAdmin || user.permissions.includes(permission);
  const hasAny = (prefixes: string[]) =>
    isAdmin ||
    user.permissions.some((permission) =>
      prefixes.some((prefix) => permission.includes(prefix))
    );
  return items.filter((item) => {
    if (item.href === "/dashboard/staff") return has("can_view_roles") || has("can_view_users") || has("can_create_users");
    if (item.href === "/dashboard/billing") return has("can_view_invoices") || has("can_create_invoices");
    if (item.href === "/dashboard/records") return hasAny(["medical_records"]);
    if (item.href === "/dashboard/pharmacy") return hasAny(["medicine", "prescription"]);
    return true;
  });
}
