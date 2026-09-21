"use client";

import { FormEvent, useMemo, useState } from "react";
import { toast } from "sonner";
import { PageHeader, StatCard } from "@/components/dashboard/page-header";
import { EmptyState, ErrorState, LoadingRows } from "@/components/dashboard/data-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiDownload, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { formatDateTime } from "@/lib/format";
import { useApiData } from "@/lib/use-api-data";
import type { Appointment, Invoice } from "@/lib/types";
import { MedicalFileIcon } from "hugeicons-react";

const PAYMENT_METHODS = [
  ["CASH", "Cash"],
  ["CARD", "Card"],
  ["MOBILE_MONEY", "Mobile money"],
  ["INSURANCE", "Insurance"],
  ["BANK_TRANSFER", "Bank transfer"],
] as const;

export default function BillingPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("can_view_invoices");
  const canCreate = hasPermission("can_create_invoices");
  const canRecordPayment = hasPermission("can_record_invoice_payments");
  const invoices = useApiData<Invoice[]>(
    () => (canView ? apiRequest("/billing/") : Promise.resolve([])),
    String(canView)
  );
  const appointments = useApiData<Appointment[]>(
    () => (canCreate ? apiRequest("/appointments/?status=COMPLETED") : Promise.resolve([])),
    String(canCreate)
  );
  const [appointmentId, setAppointmentId] = useState("");
  const [paymentInvoice, setPaymentInvoice] = useState<Invoice | null>(null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("CASH");
  const [paymentReference, setPaymentReference] = useState("");
  const [busy, setBusy] = useState(false);

  const invoicedAppointmentIds = useMemo(
    () => new Set((invoices.data ?? []).map((invoice) => invoice.appointment)),
    [invoices.data]
  );
  const invoiceCandidates = (appointments.data ?? []).filter(
    (appointment) => !invoicedAppointmentIds.has(appointment.id)
  );
  const totals = (invoices.data ?? []).reduce(
    (summary, invoice) => ({
      total: summary.total + Number(invoice.total_amount),
      paid: summary.paid + Number(invoice.amount_paid),
      balance: summary.balance + Number(invoice.balance),
    }),
    { total: 0, paid: 0, balance: 0 }
  );

  if (!canView && !canCreate) {
    return (
      <EmptyState
        icon={MedicalFileIcon}
        title="Billing access required"
        description="Your assigned role does not include billing permissions."
      />
    );
  }

  const generateInvoice = async (event: FormEvent) => {
    event.preventDefault();
    if (!appointmentId) return;
    setBusy(true);
    try {
      await apiRequest("/billing/", {
        method: "POST",
        body: { appointment: Number(appointmentId) },
      });
      toast.success("Invoice generated");
      setAppointmentId("");
      invoices.reload();
      appointments.reload();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not generate invoice");
    } finally {
      setBusy(false);
    }
  };

  const recordPayment = async (event: FormEvent) => {
    event.preventDefault();
    if (!paymentInvoice) return;
    setBusy(true);
    try {
      await apiRequest(`/billing/${paymentInvoice.id}/payments/`, {
        method: "POST",
        body: {
          amount: paymentAmount,
          method: paymentMethod,
          reference: paymentReference,
        },
      });
      toast.success("Payment recorded");
      setPaymentInvoice(null);
      setPaymentAmount("");
      setPaymentReference("");
      invoices.reload();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not record payment");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Billing"
        description="Generate completed-visit invoices and track their payment status."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard icon={MedicalFileIcon} label="Invoiced" value={totals.total.toFixed(2)} />
        <StatCard icon={MedicalFileIcon} label="Paid" value={totals.paid.toFixed(2)} />
        <StatCard icon={MedicalFileIcon} label="Outstanding" value={totals.balance.toFixed(2)} />
      </div>

      {canCreate && (
        <form
          onSubmit={generateInvoice}
          className="flex flex-col gap-3 rounded-[18px] border border-hairline bg-canvas p-5 sm:flex-row dark:border-stone-800 dark:bg-stone-900"
        >
          <select
            value={appointmentId}
            onChange={(event) => setAppointmentId(event.target.value)}
            className="h-10 flex-1 rounded-md border border-input bg-background px-3 text-sm"
            required
          >
            <option value="">Select a completed appointment</option>
            {invoiceCandidates.map((appointment) => (
              <option key={appointment.id} value={appointment.id}>
                #{appointment.id} · {appointment.patient_name} · {appointment.appointment_date}
              </option>
            ))}
          </select>
          <Button type="submit" disabled={busy || !appointmentId}>
            Generate invoice
          </Button>
        </form>
      )}

      <section className="rounded-[18px] border border-hairline bg-canvas dark:border-stone-800 dark:bg-stone-900">
        {invoices.loading ? (
          <div className="p-5"><LoadingRows rows={5} /></div>
        ) : invoices.error ? (
          <ErrorState message={invoices.error} onRetry={invoices.reload} />
        ) : (invoices.data ?? []).length === 0 ? (
          <EmptyState
            icon={MedicalFileIcon}
            title="No invoices yet"
            description="Invoices generated from completed appointments will appear here."
          />
        ) : (
          <div className="divide-y divide-stone-100 dark:divide-stone-800">
            {(invoices.data ?? []).map((invoice) => (
              <article key={invoice.id} className="space-y-3 p-5">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-semibold">Invoice #{invoice.id}</h2>
                      <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs font-medium dark:bg-stone-800">
                        {invoice.status}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {invoice.patient_email} · {formatDateTime(invoice.created_at)}
                    </p>
                  </div>
                  <div className="text-left sm:text-right">
                    <div className="text-lg font-semibold">{invoice.total_amount}</div>
                    <div className="text-xs text-muted-foreground">
                      Paid {invoice.amount_paid} · Balance {invoice.balance}
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      apiDownload(`/billing/${invoice.id}/pdf/`, `invoice-${invoice.id}.pdf`)
                        .catch((error) => toast.error(error.message))
                    }
                  >
                    Download PDF
                  </Button>
                  {canRecordPayment && invoice.status !== "PAID" && (
                    <Button
                      size="sm"
                      onClick={() => {
                        setPaymentInvoice(invoice);
                        setPaymentAmount(invoice.balance);
                      }}
                    >
                      Record payment
                    </Button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {paymentInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/50 p-4">
          <form
            onSubmit={recordPayment}
            className="w-full max-w-md space-y-4 rounded-[18px] border border-hairline bg-canvas p-6 dark:border-stone-800 dark:bg-stone-900"
          >
            <div>
              <h2 className="font-semibold">Record payment</h2>
              <p className="text-sm text-muted-foreground">
                Invoice #{paymentInvoice.id} · Outstanding {paymentInvoice.balance}
              </p>
            </div>
            <Input
              type="number"
              min="0.01"
              step="0.01"
              max={paymentInvoice.balance}
              value={paymentAmount}
              onChange={(event) => setPaymentAmount(event.target.value)}
              placeholder="Amount"
              required
            />
            <select
              value={paymentMethod}
              onChange={(event) => setPaymentMethod(event.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              {PAYMENT_METHODS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            <Input
              value={paymentReference}
              onChange={(event) => setPaymentReference(event.target.value)}
              placeholder="Reference (optional)"
            />
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setPaymentInvoice(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={busy}>Save payment</Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

