"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Pulse } from "@phosphor-icons/react";
import { useParams } from "next/navigation";
import { getTrace } from "@/services/traces";
import type { TraceRun } from "@/types/api";
import { AgentTraceTimeline } from "@/components/evidence";
import { DataUnavailable, Panel, SectionHeader, StatusDot } from "@/components/ui";

function formatDate(value: string) { return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); }

export default function TraceDetailPage() {
  return <Suspense fallback={<div className="mx-auto max-w-[1200px] space-y-6"><div className="h-8 w-40 animate-pulse rounded-lg bg-surface-muted" /><div className="h-36 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-96 animate-pulse rounded-2xl bg-surface-muted" /></div>}><TraceDetailContent /></Suspense>;
}

function TraceDetailContent() {
  const params = useParams<{ traceId: string }>();
  const traceId = params.traceId;
  const [trace, setTrace] = useState<TraceRun | null>(null);
  const [error, setError] = useState(false);
  const load = useCallback(async () => { try { setTrace(await getTrace(traceId)); setError(false); } catch { setError(true); } }, [traceId]);
  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);
  if (error) return <div className="mx-auto max-w-[1200px] space-y-6"><Link href="/trace" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline"><ArrowLeft size={16} /> Back to traces</Link><DataUnavailable endpoint={`GET /api/traces/${traceId}`} onRetry={() => void load()} title="Trace detail unavailable" description="The run could not be loaded, so no workflow sequence is shown." /></div>;
  if (!trace) return <div className="mx-auto max-w-[1200px] space-y-6"><div className="h-8 w-40 animate-pulse rounded-lg bg-surface-muted" /><div className="h-36 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-96 animate-pulse rounded-2xl bg-surface-muted" /></div>;
  return <div className="mx-auto max-w-[1200px] space-y-8"><Link href="/trace" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline"><ArrowLeft size={16} /> Back to trace history</Link><section className="rounded-2xl border border-line bg-surface p-6 shadow-[0_12px_32px_rgba(28,52,39,0.04)] sm:p-8"><div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between"><div><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">Workflow run</p><h2 className="mt-3 font-mono text-2xl font-semibold tracking-tight text-foreground">{trace.workflow_run_id}</h2><p className="mt-3 text-sm text-muted">{trace.request}</p></div><span className="flex items-center gap-2 text-xs font-semibold text-muted"><StatusDot status={trace.status === "COMPLETE" ? "success" : trace.status === "FAILED" ? "danger" : "warning"} />{trace.status} · {formatDate(trace.started_at)}</span></div></section><Panel><SectionHeader eyebrow="Agent trace" title="Investigation sequence" description="A readable audit of tool use and explicit decisions." /><AgentTraceTimeline events={trace.events} /></Panel><Panel><SectionHeader eyebrow="Tool audit" title={`${trace.tool_calls.length} tool calls`} />{trace.tool_calls.length === 0 ? <div className="flex items-center gap-3 text-sm text-muted"><Pulse size={18} aria-hidden="true" />No tool calls returned for this run.</div> : <div className="space-y-3">{trace.tool_calls.map((call, index) => <div key={call.id ?? `${call.tool_name}-${index}`} className="rounded-xl border border-line bg-surface-muted/45 p-4"><p className="font-mono text-sm font-semibold text-forest">{call.tool_name}</p><p className="mt-2 text-sm text-muted">{call.status} · {formatDate(call.timestamp)}</p></div>)}</div>}</Panel></div>;
}
