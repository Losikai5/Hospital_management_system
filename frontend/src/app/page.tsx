"use client";

import Link from "next/link";
import Image from "next/image";
import { motion, useReducedMotion } from "motion/react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/brand/logo";
import { AiChatWidget } from "@/components/ai/ai-chat-widget";
import { useAuth } from "@/lib/auth-context";
import {
  Appointment01Icon,
  SecurityValidationIcon,
  CheckmarkCircle02Icon,
  UserGroupIcon,
  Building03Icon,
  AnalyticsUpIcon,
  AiChipIcon,
  CloudIcon,
  ArrowRight01Icon,
  QuoteDownIcon,
  StarsIcon,
  MedicalFileIcon,
  PillIcon,
} from "hugeicons-react";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
};

const stagger = {
  initial: { opacity: 0 },
  whileInView: { opacity: 1 },
  viewport: { once: true, amount: 0.1 },
  transition: { staggerChildren: 0.08 },
};

/* Global nav — pure black, 44px, quiet 12px links, right-aligned CTA. */
function Nav() {
  const { isAuthenticated } = useAuth();
  return (
    <header className="sticky top-0 z-50 bg-void">
      <div className="mx-auto flex h-11 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo variant="light" />
        <nav className="hidden items-center gap-8 md:flex">
          {[
            ["Platform", "#platform"],
            ["Features", "#features"],
            ["For providers", "#providers"],
          ].map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="text-[12px] font-normal tracking-[-0.12px] text-white/80 transition-colors hover:text-white"
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <Button className="h-7 bg-focus px-4 text-[13px] text-white hover:bg-action" render={<Link href="/dashboard" />}>
              Dashboard
            </Button>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden rounded-lg bg-ink px-3.5 py-1.5 text-[13px] font-normal text-white transition-colors hover:bg-[#333333] sm:inline-flex"
              >
                Sign in
              </Link>
              <Button className="h-7 bg-focus px-4 text-[13px] text-white hover:bg-action" render={<Link href="/signup" />}>
                Get started
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function Hero() {
  const reduce = useReducedMotion();
  return (
    <section className="relative overflow-hidden bg-canvas px-4 pb-24 pt-20 sm:px-6 sm:pt-24 lg:px-8 lg:pb-32 lg:pt-28">
      <div className="pointer-events-none absolute inset-0 bg-plus-grid opacity-50" />
      <div className="relative mx-auto max-w-5xl text-center">
        <motion.div {...(reduce ? {} : fadeUp)}>
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-hairline bg-pearl px-4 py-1.5 text-[13px] font-medium text-ink-48">
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-action opacity-60" />
              <span className="relative inline-flex size-1.5 rounded-full bg-action" />
            </span>
            Now serving 12+ healthcare facilities
          </div>
          <h1 className="mx-auto max-w-4xl text-[2.75rem] font-semibold leading-[1.05] tracking-[-0.02em] text-ink sm:text-6xl lg:text-[4rem]">
            Healthcare management, made human.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-[19px] leading-snug font-normal text-ink-48">
            A unified platform for appointments, records, pharmacy, and care
            coordination — built so clinicians can focus on patients, not paperwork.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button
              size="lg"
              className="h-12 w-full gap-2 bg-action px-7 text-[17px] font-normal text-white hover:bg-focus sm:w-auto"
              render={<Link href="/signup" />}
            >
              Start free trial
              <ArrowRight01Icon className="size-4" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="h-12 w-full border-action/60 bg-transparent px-7 text-[17px] font-normal text-action hover:bg-emerald-50 hover:text-action sm:w-auto dark:border-link-blue dark:text-link-blue"
              render={<Link href="#platform" />}
            >
              See how it works
            </Button>
          </div>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-x-7 gap-y-3 text-[13px] text-ink-48">
            {["HIPAA compliant", "SOC 2 Type II", "Free for patients"].map((label) => (
              <span key={label} className="flex items-center gap-1.5">
                <CheckmarkCircle02Icon className="size-4 text-action" /> {label}
              </span>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="relative mx-auto mt-16 max-w-5xl"
          {...(reduce
            ? {}
            : {
                initial: { opacity: 0, y: 28 },
                whileInView: { opacity: 1, y: 0 },
                viewport: { once: true },
                transition: { duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] },
              })}
        >
          <div className="relative aspect-[16/9] overflow-hidden rounded-[18px] shadow-product">
            <Image
              src="https://images.unsplash.com/photo-1629909613654-28e377c37b09?w=1400&q=80"
              alt="Clinician reviewing patient data on a tablet"
              fill
              priority
              className="object-cover"
              sizes="(max-width: 1024px) 100vw, 64rem"
            />
            <div className="absolute inset-x-4 bottom-4 sm:inset-x-6 sm:bottom-6">
              <div className="frosted flex items-center gap-3 rounded-full border border-white/30 p-2 pl-4">
                <div className="flex items-center gap-1.5 rounded-full bg-action px-3 py-1 text-xs font-medium text-white">
                  <span className="size-1.5 rounded-full bg-white" />
                  Live
                </div>
                <span className="truncate text-[13px] text-ink">284 patients actively managed today</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function StatsBar() {
  const reduce = useReducedMotion();
  const stats = [
    { value: "12+", label: "Healthcare facilities", icon: Building03Icon },
    { value: "50K+", label: "Patients served", icon: UserGroupIcon },
    { value: "120K+", label: "Appointments booked", icon: Appointment01Icon },
    { value: "99.9%", label: "Uptime SLA", icon: AnalyticsUpIcon },
  ];
  return (
    <section className="border-y border-hairline bg-parchment">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 px-4 py-12 sm:px-6 md:grid-cols-4 md:divide-x md:divide-hairline lg:px-8">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            className="text-center"
            {...(reduce
              ? {}
              : {
                  initial: { opacity: 0, y: 12 },
                  whileInView: { opacity: 1, y: 0 },
                  viewport: { once: true },
                  transition: { duration: 0.5, delay: i * 0.05 },
                })}
          >
            <stat.icon className="mx-auto mb-2 size-5 text-action" />
            <div className="text-[1.75rem] font-semibold tracking-tight tabular-nums text-ink">
              {stat.value}
            </div>
            <div className="mt-0.5 text-[13px] text-ink-48">{stat.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

/* Dark editorial tile — the "from zero to operational" story. */
function HowItWorks() {
  const reduce = useReducedMotion();
  const steps = [
    {
      step: "01",
      title: "Register your facility",
      description:
        "Get your clinic or hospital onboarded in under 48 hours. We handle data migration and staff training.",
    },
    {
      step: "02",
      title: "Connect your workflows",
      description:
        "Bring scheduling, records, and pharmacy into a single dashboard your team will actually use.",
    },
    {
      step: "03",
      title: "Deliver better care",
      description:
        "Your staff spends less time on admin and more time with patients. Real-time data drives better outcomes.",
    },
  ];
  return (
    <section id="platform" className="bg-tile-1 px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
      <div className="mx-auto max-w-5xl">
        <motion.div className="text-center" {...(reduce ? {} : fadeUp)}>
          <div className="mb-5 inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-[13px] font-medium text-link-blue">
            <StarsIcon className="size-3.5" /> Simple setup
          </div>
          <h2 className="text-4xl font-semibold tracking-[-0.015em] text-white sm:text-5xl">
            From zero to operational in three steps
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-[19px] text-body-muted">
            No lengthy implementations. No disruption to your existing workflows.
          </p>
        </motion.div>
        <motion.div className="relative mt-20 grid gap-6 md:grid-cols-3" {...(reduce ? {} : stagger)}>
          {steps.map((s, i) => (
            <motion.div
              key={s.step}
              className="relative"
              {...(reduce
                ? {}
                : {
                    initial: { opacity: 0, y: 20 },
                    whileInView: { opacity: 1, y: 0 },
                    viewport: { once: true },
                    transition: { duration: 0.5, delay: i * 0.1 },
                  })}
            >
              {i < steps.length - 1 && (
                <div className="absolute right-0 top-1/2 hidden -translate-y-1/2 translate-x-1/2 md:block">
                  <ArrowRight01Icon className="size-5 text-white/25" />
                </div>
              )}
<div className="mb-5 flex size-11 items-center justify-center rounded-[13px] bg-white/10 text-sm font-semibold text-link-blue">
                  {s.step}
                </div>
                <h3 className="inline-block text-[19px] font-semibold text-white">{s.title}</h3>
              <p className="mt-2.5 text-[15px] leading-relaxed text-body-muted">{s.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

const featureRows = [
  {
    tag: "Appointments",
    icon: Appointment01Icon,
    title: "Smart scheduling that reduces no-shows",
    description:
      "Patients book online in real time, with automated reminders and intelligent queue management that keeps your waiting room moving.",
    image: "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=900&q=80",
    alt: "Doctor consulting with a patient",
    chips: ["Real-time sync", "Automated reminders", "Queue management"],
  },
  {
    tag: "Records",
    icon: MedicalFileIcon,
    title: "Complete digital health records, always accessible",
    description:
      "Secure, longitudinal patient records that follow every interaction. Lab results, imaging, and medications in one place, with granular access controls.",
    image: "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=900&q=80",
    alt: "Medical team reviewing patient records",
    chips: ["Encrypted at rest", "Role-based access", "Audit trail"],
  },
  {
    tag: "Pharmacy",
    icon: PillIcon,
    title: "Prescriptions and inventory, dispensed cleanly",
    description:
      "Track prescriptions from order to dispense, keep medicine inventory current, and give every role the view it needs — nothing more.",
    image: "https://images.unsplash.com/photo-1551076805-e1869033e561?w=900&q=80",
    alt: "Pharmacist reviewing medication data",
    chips: ["Live stock levels", "Low-stock alerts", "Dispense tracking"],
  },
];

/* Alternating light / dark tiles. Each tile holds a name, one-line tagline,
   full-bleed product imagery resting on the tile. The color change IS the divider. */
function FeatureTiles() {
  const reduce = useReducedMotion();
  return (
    <>
      {featureRows.map((item, i) => {
        const dark = i % 2 === 1;
        return (
          <section
            key={item.tag}
            id={i === 0 ? "features" : undefined}
            className={
              dark
                ? "bg-tile-2 px-4 py-24 sm:px-6 lg:px-8 lg:py-28"
                : "bg-canvas px-4 py-24 sm:px-6 lg:px-8 lg:py-28"
            }
          >
            <div className="mx-auto flex max-w-6xl flex-col items-center gap-14 lg:flex-row lg:gap-20">
              <motion.div
                className="w-full max-w-lg lg:flex-1"
                {...(reduce
                  ? {}
                  : {
                      initial: { opacity: 0, y: 30 },
                      whileInView: { opacity: 1, y: 0 },
                      viewport: { once: true, amount: 0.2 },
                      transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
                    })}
              >
                <div
                  className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[12px] font-semibold uppercase tracking-[0.08em] ${
                    dark
                      ? "border-white/15 bg-white/5 text-link-blue"
                      : "border-hairline bg-pearl text-action"
                  }`}
                >
                  <item.icon className="size-3.5" />
                  {item.tag}
                </div>
                <h3
                  className={`mt-5 text-3xl font-semibold tracking-[-0.015em] sm:text-4xl ${
                    dark ? "text-white" : "text-ink"
                  }`}
                >
                  {item.title}
                </h3>
                <p
                  className={`mt-5 text-[17px] leading-[1.47] ${
                    dark ? "text-body-muted" : "text-ink-48"
                  }`}
                >
                  {item.description}
                </p>
                <div className="mt-7 flex flex-wrap gap-2.5">
                  {item.chips.map((tag) => (
                    <span
                      key={tag}
                      className={
                        dark
                          ? "rounded-full border border-white/15 bg-white/5 px-3.5 py-1.5 text-[13px] font-normal text-white/85"
                          : "rounded-full border border-hairline bg-pearl px-3.5 py-1.5 text-[13px] font-normal text-ink-80"
                      }
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="mt-8">
                  <Button
                    variant="outline"
                    className={
                      dark
                        ? "h-11 border-white/25 bg-transparent px-6 text-[15px] text-white hover:bg-white/10"
                        : "h-11 border-action/50 bg-transparent px-6 text-[15px] text-action hover:bg-emerald-50"
                    }
                    render={<Link href="#platform" />}
                  >
                    Learn more
                    <ArrowRight01Icon className="size-4" />
                  </Button>
                </div>
              </motion.div>

              <motion.div
                className="relative w-full max-w-xl lg:flex-1"
                {...(reduce
                  ? {}
                  : {
                      initial: { opacity: 0, scale: 0.98, y: 16 },
                      whileInView: { opacity: 1, scale: 1, y: 0 },
                      viewport: { once: true, amount: 0.2 },
                      transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
                    })}
              >
                <div className="relative aspect-[4/3] overflow-hidden rounded-[18px] shadow-product">
                  <Image
                    src={item.image}
                    alt={item.alt}
                    fill
                    className="object-cover"
                    sizes="(max-width: 1024px) 100vw, 42rem"
                  />
                </div>
              </motion.div>
            </div>
          </section>
        );
      })}
    </>
  );
}

function Testimonials() {
  const reduce = useReducedMotion();
  const testimonials = [
    {
      quote:
        "We reduced patient wait times by 35% in the first quarter. The scheduling module alone transformed how our front desk operates.",
      name: "Dr. Sarah Mitchell",
      role: "Chief of Medicine, Northwell Clinic",
    },
    {
      quote:
        "The unified records system means I can pull up any patient's history in seconds. It's the first EMR my team actually enjoys using.",
      name: "Michael Torres",
      role: "Practice Manager, Maple Medical Group",
    },
    {
      quote:
        "Integration was surprisingly painless. We had our entire practice migrated and staff trained within two days.",
      name: "Dr. Priya Sharma",
      role: "Founder, Sharma Family Medicine",
    },
  ];
  return (
    <section className="bg-parchment px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
      <div className="mx-auto max-w-6xl">
        <motion.div className="text-center" {...(reduce ? {} : fadeUp)}>
          <h2 className="text-4xl font-semibold tracking-[-0.015em] text-ink sm:text-5xl">
            Trusted by healthcare professionals
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-[17px] text-ink-48">
            See what practitioners say about Serenity Health.
          </p>
        </motion.div>
        <motion.div className="mt-16 grid gap-6 md:grid-cols-3" {...(reduce ? {} : stagger)}>
          {testimonials.map((t) => (
            <motion.div
              key={t.name}
              className="flex flex-col rounded-[18px] border border-hairline bg-canvas p-7"
              {...(reduce
                ? {}
                : {
                    initial: { opacity: 0, y: 16 },
                    whileInView: { opacity: 1, y: 0 },
                    viewport: { once: true },
                    transition: { duration: 0.5 },
                  })}
            >
              <QuoteDownIcon className="mb-4 size-5 text-action/60" />
              <p className="flex-1 text-[15px] leading-[1.6] text-ink-80">
                &ldquo;{t.quote}&rdquo;
              </p>
              <div className="mt-6 flex items-center gap-3 border-t border-hairline pt-5">
                <div className="flex size-10 items-center justify-center rounded-full bg-emerald-100 text-[13px] font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                  {t.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </div>
                <div>
                  <div className="text-[15px] font-medium text-ink">{t.name}</div>
                  <div className="text-[13px] text-ink-48">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

/* Dark tile — enterprise + reliability, white text, Sky Link Blue links. */
function Security() {
  const reduce = useReducedMotion();
  const items = [
    { icon: SecurityValidationIcon, title: "HIPAA compliant", description: "Enterprise-grade security with BAA support. All data encrypted at rest and in transit." },
    { icon: AiChipIcon, title: "AI-powered insights", description: "Predictive analytics help you identify at-risk patients and optimize resource allocation." },
    { icon: CloudIcon, title: "99.9% uptime", description: "Cloud-native architecture with automatic failover. Your data is always available when you need it." },
  ];
  return (
    <section id="providers" className="bg-tile-1 px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
      <div className="mx-auto max-w-6xl">
        <motion.div className="text-center" {...(reduce ? {} : fadeUp)}>
          <h2 className="text-4xl font-semibold tracking-[-0.015em] text-white sm:text-5xl">
            Enterprise-grade, patient-friendly
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-[17px] text-body-muted">
            Security and reliability built into everything we do.
          </p>
        </motion.div>
        <motion.div className="mt-16 grid gap-6 md:grid-cols-3" {...(reduce ? {} : stagger)}>
          {items.map((item) => (
            <motion.div
              key={item.title}
              className="rounded-[18px] border border-white/10 bg-white/[0.04] p-8 text-center"
              {...(reduce
                ? {}
                : {
                    initial: { opacity: 0, y: 16 },
                    whileInView: { opacity: 1, y: 0 },
                    viewport: { once: true },
                    transition: { duration: 0.5 },
                  })}
            >
              <div className="mx-auto mb-5 flex size-12 items-center justify-center rounded-[14px] bg-action text-white">
                <item.icon className="size-6" />
              </div>
              <h3 className="text-[17px] font-semibold text-white">{item.title}</h3>
              <p className="mt-2.5 text-[14px] leading-relaxed text-body-muted">{item.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

function CTA() {
  const reduce = useReducedMotion();
  return (
    <section className="relative bg-tile-3 px-4 py-28 sm:px-6 lg:px-8 lg:py-40">
      <motion.div
        className="relative mx-auto max-w-3xl overflow-hidden rounded-[24px] bg-tile-1 px-8 py-20 text-center sm:px-20"
        {...(reduce
          ? {}
          : {
              initial: { opacity: 0, y: 24 },
              whileInView: { opacity: 1, y: 0 },
              viewport: { once: true },
              transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
            })}
      >
        <div className="pointer-events-none absolute inset-0 bg-plus-grid-invert opacity-50" />
        <div className="relative z-10">
          <h2 className="text-4xl font-semibold tracking-[-0.015em] text-white sm:text-5xl">
            Ready to transform your healthcare experience?
          </h2>
          <p className="mx-auto mt-5 max-w-lg text-[17px] leading-relaxed text-body-muted">
            Join the providers already using Serenity Health. Free for patients —
            start today.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button
              className="h-12 w-full bg-focus px-7 text-[17px] font-normal text-white hover:bg-action sm:w-auto"
              render={<Link href="/signup" />}
            >
              Start free trial
              <ArrowRight01Icon className="size-4" />
            </Button>
            <Button
              variant="outline"
              className="h-12 w-full border-white/25 bg-transparent px-7 text-[17px] font-normal text-white hover:bg-white/10 sm:w-auto"
              render={<Link href="/login" />}
            >
              Sign in
            </Button>
          </div>
          <p className="mt-5 text-[12px] text-white/50">No credit card required to get started.</p>
        </div>
      </motion.div>
    </section>
  );
}

/* Dense parchment footer — relaxed 2.41 link columns, fine-print legal row. */
function Footer() {
  const columns: { heading: string; links: [string, string][] }[] = [
    {
      heading: "Platform",
      links: [
        ["Appointments", "#platform"],
        ["Records", "#features"],
        ["Pharmacy", "#features"],
      ],
    },
    {
      heading: "Company",
      links: [
        ["For providers", "#providers"],
        ["Security", "#providers"],
        ["Contact", "/login"],
      ],
    },
    {
      heading: "Account",
      links: [
        ["Sign in", "/login"],
        ["Create account", "/signup"],
      ],
    },
  ];
  return (
    <footer className="bg-parchment px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="grid gap-10 md:grid-cols-4">
          <div className="md:col-span-1">
            <Logo />
            <p className="mt-4 max-w-xs text-[12px] leading-[1.6] text-ink-48">
              One calm system for the whole hospital. Appointments, records,
              pharmacy, and billing in a single place.
            </p>
          </div>
          {columns.map((col) => (
            <div key={col.heading}>
              <div className="text-[13px] font-semibold text-ink">{col.heading}</div>
              <ul className="mt-3">
                {col.links.map(([label, href]) => (
                  <li key={label}>
                    {href.startsWith("#") ? (
                      <a
                        href={href}
                        className="text-[15px] leading-[2.2] text-ink-48 transition-colors hover:text-action"
                      >
                        {label}
                      </a>
                    ) : (
                      <Link
                        href={href}
                        className="text-[15px] leading-[2.2] text-ink-48 transition-colors hover:text-action"
                      >
                        {label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-14 border-t border-hairline pt-6 text-[12px] text-ink-48">
          {`© ${new Date().getFullYear()} Serenity Health · Secure hospital management`}
        </div>
      </div>
    </footer>
  );
}

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <Nav />
      <main className="flex-1">
        <Hero />
        <StatsBar />
        <HowItWorks />
        <FeatureTiles />
        <Testimonials />
        <Security />
        <CTA />
      </main>
      <Footer />
      <AiChatWidget />
    </div>
  );
}