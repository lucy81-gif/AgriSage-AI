import Link from "next/link";
import { ArrowDown, ArrowRight, CheckCircle, GitBranch, Info, WarningCircle } from "@phosphor-icons/react";
import type { DecisionChangeData, EvidenceItem, RiskLevel, ToolCall, TraceEvent } from "@/types/api";
import { ConfidenceIndicator, EmptyState, RiskBadge, StatusDot } from "./ui";

function formatDate(value?: string | null) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(new Date(value));
}

function formatTimestamp(value?: string | null) {
  if (!value) return "Time not recorded";
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function EvidenceChain({
  evidence,
  risk,
  nextAction,
  missingEvidence = [],
}: {
  evidence: EvidenceItem[];
  risk?: RiskLevel | null;
  nextAction?: string | null;
  missingEvidence?: string[];
}) {
  if (evidence.length === 0) {
    return <EmptyState title="No evidence chain returned" description="The backend has not supplied evidence for this decision yet. AgriSage AI will not fill this gap with an assumption." icon={<Info size={22} weight="duotone" />} />;
  }

  return (
    <div>
      <div className="relative space-y-0">
        {evidence.map((item, index) => (
          <div key={item.id ?? `${item.source}-${item.label}-${index}`} className="relative flex gap-4 pb-5 last:pb-0">
            {index < evidence.length - 1 && <span className="absolute bottom-1 left-3 top-7 w-px bg-line-strong" aria-hidden="true" />}
            <span className="relative z-10 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-line-strong bg-surface text-forest" aria-hidden="true">
              {item.kind === "missing" ? <WarningCircle size={14} weight="duotone" className="text-amber" /> : <CheckCircle size={14} weight="duotone" />}
            </span>
            <div className="min-w-0 flex-1 rounded-xl border border-line bg-surface-muted/45 p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-foreground">{item.label}</p>
                  <p className="mt-1 text-sm leading-6 text-muted text-pretty">{item.detail}</p>
                </div>
                {item.confidence !== undefined && <ConfidenceIndicator value={item.confidence} />}
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-xs text-muted">
                <span>Source: {item.source}</span>
                {item.observed_at && <span>Observed: {formatDate(item.observed_at)}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 flex flex-col gap-3 rounded-xl border border-forest/15 bg-sage-soft/50 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-forest">Decision reached</p>
          <div className="mt-2 flex items-center gap-3"><RiskBadge risk={risk} /><ArrowDown size={15} className="text-muted" aria-hidden="true" /><span className="text-sm font-semibold text-foreground">{nextAction ?? "No next action supplied"}</span></div>
        </div>
        <span className="text-xs leading-5 text-muted">The evidence chain is inspectable by the officer before approval.</span>
      </div>
      {missingEvidence.length > 0 && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber/25 bg-amber-soft/40 p-4">
          <WarningCircle size={18} weight="duotone" className="mt-0.5 shrink-0 text-amber" aria-hidden="true" />
          <div><p className="text-sm font-semibold text-foreground">Missing evidence</p><p className="mt-1 text-sm leading-6 text-muted">{missingEvidence.join(" · ")}</p></div>
        </div>
      )}
    </div>
  );
}

export function DecisionChange({ change }: { change: DecisionChangeData }) {
  return (
    <div className="rounded-2xl border border-blue/20 bg-blue-soft/60 p-5">
      <div className="flex items-start gap-3">
        <GitBranch size={22} weight="duotone" className="mt-0.5 shrink-0 text-blue" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-blue">Decision updated</p>
          <div className="mt-3 flex flex-wrap items-center gap-3"><RiskBadge risk={change.from} /><ArrowRight size={16} className="text-blue" aria-hidden="true" /><RiskBadge risk={change.to} /></div>
          <p className="mt-4 text-sm leading-6 text-foreground">{change.reason}</p>
          <p className="mt-3 font-mono text-xs text-blue">Source: {change.source} · {formatDate(change.timestamp)}</p>
        </div>
      </div>
    </div>
  );
}

function JsonBlock({ value }: { value: Record<string, unknown> }) {
  return <pre className="max-h-60 overflow-auto rounded-xl bg-forest-deep p-4 font-mono text-xs leading-5 text-sage">{JSON.stringify(value, null, 2)}</pre>;
}

export function ToolCallCard({ call }: { call: ToolCall }) {
  const success = call.status.toUpperCase() === "SUCCESS";
  return (
    <details className="group rounded-xl border border-line bg-surface">
      <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-4 [&::-webkit-details-marker]:hidden">
        <StatusDot status={success ? "success" : call.status.toUpperCase() === "FAILURE" ? "danger" : "warning"} />
        <span className="flex-1 font-mono text-xs font-semibold text-foreground">{call.tool_name}</span>
        <span className="font-mono text-xs text-muted">{formatTimestamp(call.started_at ?? call.timestamp)}</span>
        <ArrowDown size={16} className="text-muted transition-transform duration-300 group-open:rotate-180" aria-hidden="true" />
      </summary>
      <div className="grid gap-4 border-t border-line px-4 py-4 md:grid-cols-2">
        <p className="md:col-span-2 text-xs text-muted">Server: <span className="font-semibold text-foreground">{call.server_name ?? "Server not recorded"}</span>{call.duration_ms !== null && call.duration_ms !== undefined ? ` · ${call.duration_ms} ms` : ""}</p>
        <div><p className="mb-2 font-mono text-xs font-semibold uppercase tracking-[0.14em] text-muted">Input</p><JsonBlock value={call.input_payload} /></div>
        <div><p className="mb-2 font-mono text-xs font-semibold uppercase tracking-[0.14em] text-muted">Output</p><JsonBlock value={call.output_payload} /></div>
      </div>
    </details>
  );
}

export function AgentTraceTimeline({ events }: { events: TraceEvent[] }) {
  if (events.length === 0) return <EmptyState title="No trace events returned" description="Trace events will appear here after an analysis run is available." />;
  return (
    <div className="relative space-y-1">
      {events.map((event, index) => (
        <div key={event.id ?? `${event.label}-${index}`} className="relative flex gap-4 pb-5 last:pb-0">
          {index < events.length - 1 && <span className="absolute bottom-1 left-3 top-7 w-px bg-line-strong" aria-hidden="true" />}
          <span className={`relative z-10 mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border bg-surface ${event.status === "failed" || event.status === "blocked" ? "border-amber text-amber" : "border-line-strong text-forest"}`} aria-hidden="true">
            {event.status === "failed" || event.status === "blocked" ? <WarningCircle size={14} weight="duotone" /> : <CheckCircle size={14} weight="duotone" />}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"><p className="text-sm font-semibold text-foreground">{event.label}</p><span className="font-mono text-xs text-muted">{formatDate(event.timestamp)}</span></div>
            {event.detail && <p className="mt-1 text-sm leading-6 text-muted">{event.detail}</p>}
            {event.tool_call && <div className="mt-3"><ToolCallCard call={event.tool_call} /></div>}
            {event.decision_change && <div className="mt-3"><DecisionChange change={event.decision_change} /></div>}
          </div>
        </div>
      ))}
    </div>
  );
}

export function EvidenceSourceLink({ source }: { source: string }) {
  return <Link href="/trace" className="font-mono text-xs text-forest underline decoration-forest/30 underline-offset-4 hover:decoration-forest">{source}</Link>;
}
