import Link from "next/link";
import { cn } from "@/lib/utils";

type LogoProps = {
  /** "light" for use on dark/emerald surfaces, "dark" for light surfaces. */
  variant?: "light" | "dark";
  /** Wrap in a link. Pass null to render a plain (non-interactive) mark. */
  href?: string | null;
  className?: string;
};

export function Logo({ variant = "dark", href = "/", className }: LogoProps) {
  const light = variant === "light";

  const content = (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "flex size-9 items-center justify-center rounded-[11px] text-sm font-bold",
          light
            ? "bg-white/10 text-white ring-1 ring-white/25 backdrop-blur-sm"
            : "bg-action text-white"
        )}
        aria-hidden
      >
        S
      </span>
      <span
        className={cn(
          "text-[15px] font-semibold tracking-tight",
          light ? "text-white" : "text-foreground"
        )}
      >
        Serenity Health
      </span>
    </span>
  );

  if (href === null) return content;

  return (
    <Link href={href} className="inline-flex rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
      {content}
    </Link>
  );
}
