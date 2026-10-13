"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Pulse, Timer } from "@phosphor-icons/react";
import { getTraces } from "@/services/traces";
import type { TraceRun } from "@/types/api";
import { DataUnavailable, EmptyState, Panel, SectionHeader, StatusDot } from "@/components/ui";

function formatDate(value: string) { return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); }

export default function TracePage() {
  const [traces, setTraces] = useState<TraceRun[] | null>(null);
  const [error, setError] = useState(false);
  const load = useCallback(async () => { try { setTraces(await getTraces()); setError(false); } catch { setError(true); } }, []);
  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);
  return <div className="mx-auto max-w-[1300px] space-y-8"><section><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">Transparent workflow</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground text-balance">See the decisions without exposing hidden reasoning.</h2><p className="mt-3 max-w-2xl text-base leading-7 text-muted text-pretty">Trace views show the request, state transitions, tool calls, evidence, and explicit decision changes that an officer can audit.</p></section><Panel><SectionHeader eyebrow="Run history" title="Agent investigations" description="Tool calls and state transitions are loaded from the trace API." />{error && <DataUnavailable endpoint="GET /api/traces" onRetry={() => void load()} title="Trace history unavailable" description="The trace list is intentionally empty until the backend returns an auditable run history." />}{!error && !traces && <div className="space-y-3"><div className="h-20 animate-pulse rounded-xl bg-surface-muted" /><div className="h-20 animate-pulse rounded-xl bg-surface-muted" /></div>}{!error && traces && traces.length === 0 && <EmptyState title="No investigations recorded" description="Submit a climate smart analysis to create the first trace run." icon={<Pulse size={22} weight="duotone" />} />}{!error && traces && traces.length > 0 && <div className="space-y-3">{traces.map((trace) => <Link href={`/trace/${trace.workflow_run_id}`} key={trace.workflow_run_id} className="flex flex-col gap-4 rounded-xl border border-line p-4 transition-colors duration-300 hover:bg-surface-muted/50 sm:flex-row sm:items-center"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sage-soft text-forest"><Pulse size={20} weight="duotone" aria-hidden="true" /></span><span className="min-w-0 flex-1"><span className="block font-mono text-sm font-semibold text-forest">{trace.workflow_run_id}</span><span className="mt-1 block text-sm text-foreground">{trace.request}</span><span className="mt-1 block font-mono text-xs text-muted">Started {formatDate(trace.started_at)} · {trace.tool_calls.length} tool calls</span></span><span className="flex items-center gap-3 text-xs font-semibold text-muted"><StatusDot status={trace.status === "COMPLETE" ? "success" : trace.status === "FAILED" ? "danger" : "warning"} />{trace.status}<ArrowRight size={16} aria-hidden="true" /></span></Link>)}</div>}</Panel><div className="flex items-start gap-3 rounded-2xl border border-line bg-surface p-5"><Timer size={21} weight="duotone" className="mt-0.5 shrink-0 text-forest" aria-hidden="true" /><p className="text-sm leading-6 text-muted">Trace output intentionally excludes private model chain of thought. It includes only auditable actions and decision explanations.</p></div></div>;
}
