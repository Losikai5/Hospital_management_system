"use client";

import { useMemo, useState } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { EmptyState, ErrorState, LoadingRows } from "@/components/dashboard/data-state";
import { Input } from "@/components/ui/input";
import { apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { formatDateTime } from "@/lib/format";
import { useApiData } from "@/lib/use-api-data";
import type { AuditLog } from "@/lib/types";
import { Search01Icon } from "hugeicons-react";

export default function AuditPage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("can_view_audit_logs");
  const logs = useApiData<AuditLog[]>(
    () => (canView ? apiRequest("/audit/logs/?limit=100") : Promise.resolve([])),
    String(canView)
  );
  const [search, setSearch] = useState("");
  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return logs.data ?? [];
    return (logs.data ?? []).filter((log) =>
      [
        log.actor_email,
        log.action,
        log.method,
        log.path,
        log.request_id,
        String(log.status_code),
      ].some((value) => value.toLowerCase().includes(query))
    );
  }, [logs.data, search]);

  if (!canView) {
    return (
      <EmptyState
        icon={Search01Icon}
        title="Audit access required"
        description="Your role does not include permission to view audit records."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit trail"
        description="Immutable records of API changes, actors, outcomes and request IDs."
      />
      <Input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search actor, action, path, status or request ID"
        className="max-w-xl"
      />
      <section className="overflow-hidden rounded-[18px] border border-hairline bg-canvas dark:border-stone-800 dark:bg-stone-900">
        {logs.loading ? (
          <div className="p-5"><LoadingRows rows={8} /></div>
        ) : logs.error ? (
          <ErrorState message={logs.error} onRetry={logs.reload} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={Search01Icon}
            title="No audit records found"
            description="Mutation records will appear here as the API is used."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-left text-sm">
              <thead className="bg-stone-50 text-xs uppercase tracking-wide text-stone-500 dark:bg-stone-950/50">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Result</th>
                  <th className="px-4 py-3">Request ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 dark:divide-stone-800">
                {filtered.map((log) => (
                  <tr key={log.id}>
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                      {formatDateTime(log.created_at)}
                    </td>
                    <td className="px-4 py-3">{log.actor_email || "Public/anonymous"}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{log.method} · {log.action}</div>
                      <div className="max-w-md truncate text-xs text-muted-foreground">{log.path}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={log.status_code < 400 ? "text-emerald-600" : "text-red-600"}>
                        {log.status_code}
                      </span>
                    </td>
                    <td className="max-w-48 truncate px-4 py-3 font-mono text-xs text-muted-foreground">
                      {log.request_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

