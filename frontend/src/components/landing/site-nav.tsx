"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/brand/logo";
import { useAuth } from "@/lib/auth-context";

const LINKS = [
  { label: "Modules", href: "#modules" },
  { label: "For patients", href: "#audience" },
];

export function SiteNav() {
  const { isAuthenticated } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Logo />

        <nav className="hidden items-center gap-8 md:flex">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <Button className="h-9 px-4" render={<Link href="/dashboard" />}>
              Go to dashboard
            </Button>
          ) : (
            <>
              <Button variant="ghost" className="hidden h-9 px-3 sm:inline-flex" render={<Link href="/login" />}>
                Sign in
              </Button>
              <Button className="h-9 px-4" render={<Link href="/signup" />}>
                Create account
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
