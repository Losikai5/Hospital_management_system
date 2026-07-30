"use client";

import Link from "next/link";
import Image from "next/image";
import { motion, useReducedMotion } from "motion/react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/brand/logo";
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

function Nav() {
  const { isAuthenticated } = useAuth();
  return (
    <header className="sticky top-0 z-50 border-b border-stone-200/70 bg-white/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Logo />
        <nav className="hidden items-center gap-8 md:flex">
          {[
            ["Platform", "#platform"],
            ["Features", "#features"],
            ["For providers", "#providers"],
          ].map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="text-sm font-medium text-stone-500 transition-colors hover:text-stone-900"
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <Button size="lg" className="h-9 px-4" render={<Link href="/dashboard" />}>
              Dashboard
            </Button>
          ) : (
            <>
              <Button
                variant="ghost"
                size="lg"
                className="hidden h-9 px-3 sm:inline-flex"
                render={<Link href="/login" />}
              >
                Sign in
              </Button>
              <Button size="lg" className="h-9 px-4" render={<Link href="/signup" />}>
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
    <section className="relative overflow-hidden px-4 pb-16 pt-16 sm:px-6 lg:px-8 lg:pb-24 lg:pt-20">
      <div className="pointer-events-none absolute inset-0 bg-plus-grid opacity-60" />
      <div className="pointer-events-none absolute -top-40 right-0 size-[500px] rounded-full bg-emerald-500/[0.07] blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 left-0 size-[420px] rounded-full bg-emerald-500/[0.04] blur-3xl" />
      <div className="relative mx-auto max-w-7xl">
        <div className="grid items-center gap-12 lg:grid-cols-5 lg:gap-16">
          <motion.div className="lg:col-span-3" {...(reduce ? {} : fadeUp)}>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50/80 px-3.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-500/10 backdrop-blur">
              <span className="relative flex size-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex size-1.5 rounded-full bg-emerald-500" />
              </span>
              Now serving 12+ healthcare facilities
            </div>
            <h1 className="text-4xl font-bold leading-[1.05] tracking-tight text-stone-900 sm:text-5xl lg:text-[3.5rem]">
              Healthcare management{" "}
              <span className="text-emerald-600">made human</span>
            </h1>
            <p className="mt-5 max-w-lg text-[17px] leading-relaxed text-stone-500">
              A unified platform for appointments, records, pharmacy, and care coordination —
              built so clinicians can focus on patients, not paperwork.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button size="lg" className="h-11 w-full gap-1.5 px-5 text-sm sm:w-auto" render={<Link href="/signup" />}>
                Start free trial
                <ArrowRight01Icon className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="h-11 w-full px-5 text-sm sm:w-auto"
                render={<Link href="#platform" />}
              >
                See how it works
              </Button>
            </div>
            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-stone-400">
              {["HIPAA compliant", "SOC 2 Type II", "Free for patients"].map((label) => (
                <span key={label} className="flex items-center gap-1.5">
                  <CheckmarkCircle02Icon className="size-4 text-emerald-500" /> {label}
                </span>
              ))}
            </div>
          </motion.div>

          <motion.div
            className="relative lg:col-span-2"
            {...(reduce
              ? {}
              : {
                  initial: { opacity: 0, x: 20 },
                  whileInView: { opacity: 1, x: 0 },
                  viewport: { once: true },
                  transition: { duration: 0.7, delay: 0.15, ease: [0.16, 1, 0.3, 1] },
                })}
          >
            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-stone-200/60 shadow-[0_30px_60px_-25px_rgba(6,78,59,0.4)]">
              <Image
                src="https://images.unsplash.com/photo-1629909613654-28e377c37b09?w=800&q=80"
                alt="Clinician reviewing patient data on a tablet"
                fill
                className="object-cover"
                priority
                sizes="(max-width: 1024px) 100vw, 40vw"
              />
              <div className="absolute inset-0 bg-gradient-to-tr from-emerald-950/30 via-transparent to-transparent" />
              <div className="absolute inset-x-4 bottom-4 rounded-xl border border-white/20 bg-white/75 p-3 backdrop-blur-md">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-2.5 py-1 text-xs font-semibold text-white">
                    <span className="size-1.5 rounded-full bg-white" />
                    Live
                  </div>
                  <span className="text-xs text-stone-600">284 patients actively managed today</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
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
    <section className="border-y border-stone-200/60 bg-stone-50/60">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <motion.div
          className="grid grid-cols-2 gap-8 md:grid-cols-4 md:divide-x md:divide-stone-200/70"
          {...(reduce ? {} : stagger)}
        >
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              className="text-center md:px-4"
              {...(reduce
                ? {}
                : {
                    initial: { opacity: 0, y: 12 },
                    whileInView: { opacity: 1, y: 0 },
                    viewport: { once: true },
                    transition: { duration: 0.5 },
                  })}
            >
              <stat.icon className="mx-auto mb-2 size-5 text-emerald-500" />
              <div className="text-2xl font-bold tracking-tight tabular-nums text-stone-900">
                {stat.value}
              </div>
              <div className="mt-0.5 text-sm text-stone-500">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

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
    <section id="platform" className="px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <div className="mx-auto max-w-7xl">
        <motion.div className="text-center" {...(reduce ? {} : fadeUp)}>
          <div className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            <StarsIcon className="size-3.5" /> Simple setup
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">
            From zero to operational in three steps
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[17px] text-stone-500">
            No lengthy implementations. No disruption to your existing workflows.
          </p>
        </motion.div>
        <motion.div className="relative mt-16 grid gap-6 md:grid-cols-3" {...(reduce ? {} : stagger)}>
          {steps.map((s, i) => (
            <motion.div
              key={s.step}
              className="relative rounded-2xl border border-stone-200 bg-white p-8 transition-colors hover:border-emerald-600/30"
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
                  <ArrowRight01Icon className="size-5 text-stone-300" />
                </div>
              )}
              <div className="mb-4 flex size-10 items-center justify-center rounded-xl bg-emerald-50 text-sm font-bold text-emerald-600">
                {s.step}
              </div>
              <h3 className="text-lg font-semibold text-stone-900">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-stone-500">{s.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

function Features() {
  const reduce = useReducedMotion();
  const items = [
    {
      tag: "Appointments",
      title: "Smart scheduling that reduces no-shows",
      description:
        "Patients book online in real time, with automated reminders and intelligent queue management that keeps your waiting room moving.",
      image: "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=700&q=80",
      alt: "Doctor consulting with a patient",
    },
    {
      tag: "Records",
      title: "Complete digital health records, always accessible",
      description:
        "Secure, longitudinal patient records that follow every interaction. Lab results, imaging, and medications in one place, with granular access controls.",
      image: "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=700&q=80",
      alt: "Medical team reviewing patient records",
    },
    {
      tag: "Pharmacy",
      title: "Prescriptions and inventory, dispensed cleanly",
      description:
        "Track prescriptions from order to dispense, keep medicine inventory current, and give every role the view it needs — nothing more.",
      image: "https://images.unsplash.com/photo-1551076805-e1869033e561?w=700&q=80",
      alt: "Pharmacist reviewing medication data",
    },
  ];
  return (
    <section id="features" className="border-t border-stone-200/60 bg-stone-50/40 px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <div className="mx-auto max-w-7xl">
        <motion.div className="text-center" {...(reduce ? {} : fadeUp)}>
          <h2 className="text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">
            A platform built for every role
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[17px] text-stone-500">
            Purpose-built modules that work together over one shared record.
          </p>
        </motion.div>
        <div className="mt-16 space-y-20">
          {items.map((item, i) => (
            <motion.div
              key={item.tag}
              className="grid items-center gap-10 lg:grid-cols-5 lg:gap-16"
              {...(reduce
                ? {}
                : {
                    initial: { opacity: 0, y: 30 },
                    whileInView: { opacity: 1, y: 0 },
                    viewport: { once: true, amount: 0.2 },
                    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
                  })}
            >
              <div className={i % 2 === 0 ? "lg:col-span-3" : "lg:col-span-2 lg:order-2"}>
                <div className="text-xs font-semibold uppercase tracking-wider text-emerald-600">
                  {item.tag}
                </div>
                <h3 className="mt-3 text-2xl font-bold tracking-tight text-stone-900 sm:text-3xl">
                  {item.title}
                </h3>
                <p className="mt-4 text-[15px] leading-relaxed text-stone-500">{item.description}</p>
                <div className="mt-6 flex flex-wrap gap-2.5">
                  {["Real-time sync", "Role-based access", "Audit trail"].map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-stone-200 bg-white px-3 py-1 text-xs font-medium text-stone-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <div
                className={`relative aspect-[4/3] overflow-hidden rounded-2xl border border-stone-200/60 shadow-[0_24px_50px_-28px_rgba(28,25,23,0.35)] ${
                  i % 2 === 0 ? "lg:col-span-2" : "lg:col-span-3 lg:order-1"
                }`}
              >
                <Image src={item.image} alt={item.alt} fill className="object-cover" sizes="(max-width: 1024px) 100vw, 40vw" />
                <div className="absolute inset-0 bg-gradient-to-t from-stone-900/10 to-transparent" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
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
    <section className="px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <div className="mx-auto max-w-7xl">
        <motion.div className="text-center" {...(reduce ? {} : fadeUp)}>
          <h2 className="text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">
            Trusted by healthcare professionals
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[17px] text-stone-500">
            See what practitioners say about Serenity Health.
          </p>
        </motion.div>
        <motion.div className="mt-16 grid gap-6 md:grid-cols-3" {...(reduce ? {} : stagger)}>
          {testimonials.map((t) => (
            <motion.div
              key={t.name}
              className="flex flex-col rounded-2xl border border-stone-200 bg-white p-6"
              {...(reduce
                ? {}
                : {
                    initial: { opacity: 0, y: 16 },
                    whileInView: { opacity: 1, y: 0 },
                    viewport: { once: true },
                    transition: { duration: 0.5 },
                  })}
            >
              <QuoteDownIcon className="mb-3 size-5 text-emerald-400/70" />
              <p className="flex-1 text-sm leading-relaxed text-stone-600">&ldquo;{t.quote}&rdquo;</p>
              <div className="mt-5 flex items-center gap-3 border-t border-stone-100 pt-4">
                <div className="flex size-9 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700">
                  {t.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </div>
                <div>
                  <div className="text-sm font-medium text-stone-900">{t.name}</div>
                  <div className="text-xs text-stone-500">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

function Security() {
  const reduce = useReducedMotion();
  const items = [
    {
      icon: SecurityValidationIcon,
      title: "HIPAA compliant",
      description: "Enterprise-grade security with BAA support. All data encrypted at rest and in transit.",
    },
    {
      icon: AiChipIcon,
      title: "AI-powered insights",
      description: "Predictive analytics help you identify at-risk patients and optimize resource allocation.",
    },
    {
      icon: CloudIcon,
      title: "99.9% uptime",
      description: "Cloud-native architecture with automatic failover. Your data is always available when you need it.",
    },
  ];
  return (
    <section id="providers" className="border-t border-stone-200/60 bg-stone-50/40 px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <div className="mx-auto max-w-7xl">
        <motion.div className="text-center" {...(reduce ? {} : fadeUp)}>
          <h2 className="text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">
            Enterprise-grade, patient-friendly
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[17px] text-stone-500">
            Security and reliability built into everything we do.
          </p>
        </motion.div>
        <motion.div className="mt-16 grid gap-6 md:grid-cols-3" {...(reduce ? {} : stagger)}>
          {items.map((item) => (
            <motion.div
              key={item.title}
              className="rounded-2xl border border-stone-200 bg-white p-6 text-center"
              {...(reduce
                ? {}
                : {
                    initial: { opacity: 0, y: 16 },
                    whileInView: { opacity: 1, y: 0 },
                    viewport: { once: true },
                    transition: { duration: 0.5 },
                  })}
            >
              <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
                <item.icon className="size-6" />
              </div>
              <h3 className="text-base font-semibold text-stone-900">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-stone-500">{item.description}</p>
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
    <section className="px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <motion.div
          className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-600 via-emerald-700 to-emerald-900 px-8 py-16 text-center sm:px-16"
          {...(reduce
            ? {}
            : {
                initial: { opacity: 0, y: 24 },
                whileInView: { opacity: 1, y: 0 },
                viewport: { once: true },
                transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
              })}
        >
          <div className="pointer-events-none absolute inset-0 bg-plus-grid-invert opacity-70" />
          <div className="pointer-events-none absolute -right-20 -top-20 size-60 rounded-full bg-emerald-400/20 blur-3xl" />
          <div className="relative z-10 mx-auto max-w-2xl">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to transform your healthcare experience?
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-[17px] leading-relaxed text-emerald-50/90">
              Join the providers already using Serenity Health. Free for patients — start today.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex h-11 w-full items-center justify-center gap-1.5 rounded-lg bg-white px-6 text-sm font-medium text-emerald-700 shadow-sm transition-colors hover:bg-emerald-50 sm:w-auto"
              >
                Start free trial
                <ArrowRight01Icon className="size-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex h-11 w-full items-center justify-center rounded-lg border border-white/30 px-6 text-sm font-medium text-white transition-colors hover:bg-white/10 sm:w-auto"
              >
                Sign in
              </Link>
            </div>
            <p className="mt-4 text-xs text-emerald-200/80">No credit card required to get started.</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-stone-200/60 bg-stone-50">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6 lg:px-8">
        <Logo href={null} />
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-stone-400">
          <a href="#platform" className="transition-colors hover:text-stone-600">Platform</a>
          <a href="#features" className="transition-colors hover:text-stone-600">Features</a>
          <Link href="/login" className="transition-colors hover:text-stone-600">Sign in</Link>
          <span>{`© ${new Date().getFullYear()} Serenity Health`}</span>
        </div>
      </div>
    </footer>
  );
}

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col overflow-x-clip bg-white">
      <Nav />
      <main className="flex-1">
        <Hero />
        <StatsBar />
        <HowItWorks />
        <Features />
        <Testimonials />
        <Security />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
