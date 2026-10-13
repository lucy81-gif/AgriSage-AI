"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowRight, ChartLineUp, ClipboardText, CloudRain, MapPinLine, Plant, Pulse, ShieldWarning, UsersThree } from "@phosphor-icons/react";
import Link from "next/link";
import { getAdvisories } from "@/services/advisories";
import { getBootstrapSummary, getFarms } from "@/services/farms";
import { getTraces } from "@/services/traces";
import type { Advisory, BootstrapSummary, Farm, TraceRun } from "@/types/api";
import { RunAnalysisButton } from "@/components/analysis/run-analysis";
import { FarmCard } from "@/components/farms";
import { DataUnavailable, Panel, SectionHeader, StatCard } from "@/components/ui";

function formatTime(value?: string) {
  if (!value) return "Time not available";
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

export default function OverviewPage() {
  const [summary, setSummary] = useState<BootstrapSummary | null>(null);
  const [farms, setFarms] = useState<Farm[] | null>(null);
  const [advisories, setAdvisories] = useState<Advisory[] | null>(null);
  const [traces, setTraces] = useState<TraceRun[] | null>(null);
  const [summaryError, setSummaryError] = useState(false);
  const [farmsError, setFarmsError] = useState(false);
  const [tracesError, setTracesError] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    const results = await Promise.allSettled([getBootstrapSummary(), getFarms(), getAdvisories(), getTraces()]);
    const [summaryResult, farmsResult, advisoriesResult, tracesResult] = results;
    if (summaryResult.status === "fulfilled") { setSummary(summaryResult.value); setSummaryError(false); } else setSummaryError(true);
    if (farmsResult.status === "fulfilled") { setFarms(farmsResult.value); setFarmsError(false); } else setFarmsError(true);
    if (advisoriesResult.status === "fulfilled") setAdvisories(advisoriesResult.value);
    if (tracesResult.status === "fulfilled") { setTraces(tracesResult.value); setTracesError(false); } else setTracesError(true);
    setLoading(false);
  }, []);

  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void loadData(); }, [loadData]);

  const counts = useMemo(() => ({
    high: farms?.filter((farm) => farm.risk_level === "HIGH").length,
    moderate: farms?.filter((farm) => farm.risk_level === "MODERATE").length,
    insufficient: farms?.filter((farm) => farm.risk_level === "INSUFFICIENT_EVIDENCE").length,
  }), [farms]);
  const attentionFarms = useMemo(() => farms?.filter((farm) => ["HIGH", "MODERATE", "INSUFFICIENT_EVIDENCE"].includes(farm.risk_level ?? "")).slice(0, 4) ?? [], [farms]);
  const activity = traces?.flatMap((trace) => trace.events.map((event) => ({ ...event, workflow_run_id: trace.workflow_run_id }))).sort((a, b) => b.timestamp.localeCompare(a.timestamp)).slice(0, 5) ?? [];

  return (
    <div className="mx-auto max-w-[1600px] space-y-8">
      <section className="flex flex-col gap-6 rounded-2xl border border-forest/15 bg-forest p-6 text-white shadow-[0_18px_44px_rgba(13,45,37,0.14)] sm:p-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl"><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-sage">Lesotho climate-smart advisory workspace</p><h2 className="mt-4 text-3xl font-semibold tracking-tight text-white text-balance sm:text-4xl">See which farms need attention before the week gets away.</h2><p className="mt-4 max-w-xl text-base leading-7 text-sage text-pretty">AgriSage AI brings plot history, climate signals, and pest reports into one reviewable queue for the extension office.</p><div className="mt-6 flex flex-wrap items-center gap-4"><RunAnalysisButton districts={summary?.districts} crops={summary?.crops} farms={farms ?? []} /><span className="inline-flex items-center gap-2 text-xs text-sage"><ShieldWarning size={16} weight="duotone" aria-hidden="true" />Consequential advice always stops for officer approval.</span></div><p className="mt-4 text-xs text-sage">Synthetic demonstration farms, pest reports, and climate signals. Confirm all evidence in the field.</p></div>
        <div className="hidden max-w-xs lg:block"><div className="border-l border-sage/25 pl-5"><p className="font-mono text-xs uppercase tracking-[0.16em] text-sage">Operating principle</p><p className="mt-3 text-xl font-semibold leading-8 text-white">Evidence before advice.</p><p className="mt-2 text-sm leading-6 text-sage">Every recommendation will show its source, confidence, and missing evidence.</p></div></div>
      </section>

      <section aria-label="Workspace summary" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Farms monitored" value={summary?.farms ?? "—"} meta={summary ? `${summary.districts.length} districts in scope` : "Connect to the bootstrap API"} icon={<UsersThree size={19} weight="duotone" />} />
        <StatCard label="High risk farms" value={counts.high ?? "—"} meta={farms ? "Based on current farm risk data" : "Awaiting risk assessments"} icon={<ShieldWarning size={19} weight="duotone" />} tone="danger" />
        <StatCard label="Moderate risk farms" value={counts.moderate ?? "—"} meta={farms ? "Based on current farm risk data" : "Awaiting risk assessments"} icon={<ChartLineUp size={19} weight="duotone" />} tone="warning" />
        <StatCard label="Insufficient evidence" value={counts.insufficient ?? "—"} meta={farms ? "Missing data is shown explicitly" : "Awaiting farm risk data"} icon={<CloudRain size={19} weight="duotone" />} tone="muted" />
        <StatCard label="Awaiting approval" value={advisories ? advisories.filter((advisory) => advisory.status === "PENDING_APPROVAL").length : "—"} meta={advisories ? "Advisory records from the API" : "Awaiting advisory endpoint"} icon={<ClipboardText size={19} weight="duotone" />} />
      </section>

      {summaryError && <DataUnavailable endpoint="GET /api/v1/bootstrap-summary" onRetry={() => void loadData()} title="Workspace summary unavailable" description="The backend did not return the current monitoring scope. No summary numbers are being invented." />}

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.8fr)]">
        <Panel>
          <SectionHeader eyebrow="Priority review" title="What needs attention this week?" description="Ranked farms come from the analysis API. Open a farm to inspect its evidence chain before acting." action={<Link href="/priority-queue" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline">Open priority queue <ArrowRight size={16} aria-hidden="true" /></Link>} />
          {loading && <div className="grid gap-4 sm:grid-cols-2"><div className="h-56 animate-pulse rounded-xl bg-surface-muted" /><div className="h-56 animate-pulse rounded-xl bg-surface-muted" /></div>}
          {!loading && farmsError && <DataUnavailable endpoint="GET /api/farms" onRetry={() => void loadData()} title="Priority data unavailable" description="The dashboard can show the live monitoring scope, but it cannot rank farms until the farm analysis endpoint responds." />}
          {!loading && !farmsError && attentionFarms.length === 0 && <div className="rounded-xl border border-dashed border-line-strong bg-surface-muted/40 p-8 text-center"><p className="text-base font-semibold text-foreground">No prioritised farms returned</p><p className="mt-2 text-sm leading-6 text-muted">Run an analysis or connect the priority data endpoint to populate this review list.</p></div>}
          {!loading && !farmsError && attentionFarms.length > 0 && <div className="grid gap-4 sm:grid-cols-2">{attentionFarms.map((farm) => <FarmCard key={farm.farm_id} farm={farm} />)}</div>}
        </Panel>

        <Panel>
          <SectionHeader eyebrow="Audit trail" title="Recent agent activity" description="Only tool calls, state transitions, and explicit decisions appear here." action={<Link href="/trace" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline">Full trace <ArrowRight size={16} aria-hidden="true" /></Link>} />
          {loading && <div className="space-y-4"><div className="h-16 animate-pulse rounded-xl bg-surface-muted" /><div className="h-16 animate-pulse rounded-xl bg-surface-muted" /><div className="h-16 animate-pulse rounded-xl bg-surface-muted" /></div>}
          {!loading && tracesError && <DataUnavailable endpoint="GET /api/traces" onRetry={() => void loadData()} title="Agent activity unavailable" description="The trace endpoint is not responding, so this panel is intentionally empty rather than speculative." />}
          {!loading && !tracesError && activity.length === 0 && <div className="rounded-xl border border-dashed border-line-strong bg-surface-muted/40 p-8 text-center"><Pulse size={24} className="mx-auto text-forest" aria-hidden="true" /><p className="mt-3 text-base font-semibold text-foreground">No agent runs recorded</p><p className="mt-2 text-sm leading-6 text-muted">Activity will appear after the first investigation is submitted.</p></div>}
          {!loading && !tracesError && activity.length > 0 && <div className="space-y-2">{activity.map((event, index) => <Link key={`${event.workflow_run_id}-${event.timestamp}-${index}`} href={`/trace/${event.workflow_run_id}`} className="flex gap-3 rounded-xl p-3 transition-colors duration-300 hover:bg-surface-muted"><span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-forest" aria-hidden="true" /><span className="min-w-0 flex-1"><span className="block text-sm font-medium text-foreground">{event.label}</span><span className="mt-1 block text-xs text-muted">{event.detail ?? "State transition recorded"}</span></span><span className="whitespace-nowrap font-mono text-xs text-muted">{formatTime(event.timestamp)}</span></Link>)}</div>}
        </Panel>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <Panel className="lg:col-span-2"><SectionHeader eyebrow="Working context" title="A review surface for the extension backlog" description="The workspace keeps decisions grounded in farm records, not conversational guesses." /><div className="grid gap-4 sm:grid-cols-3"><div className="rounded-xl bg-surface-muted/60 p-4"><MapPinLine size={20} className="text-forest" aria-hidden="true" /><p className="mt-4 font-mono text-2xl font-semibold text-foreground">{summary?.districts.length ?? "—"}</p><p className="mt-1 text-sm text-muted">Districts in the current scope</p></div><div className="rounded-xl bg-surface-muted/60 p-4"><PlantIcon /><p className="mt-4 font-mono text-2xl font-semibold text-foreground">{summary?.crops.length ?? "—"}</p><p className="mt-1 text-sm text-muted">Crops represented in data</p></div><div className="rounded-xl bg-surface-muted/60 p-4"><Pulse size={20} className="text-forest" aria-hidden="true" /><p className="mt-4 font-mono text-2xl font-semibold text-foreground">{summary?.tool_call_logs ?? "—"}</p><p className="mt-1 text-sm text-muted">Tool calls logged</p></div></div></Panel>
        <Panel><div className="flex items-start gap-3"><ShieldWarning size={22} weight="duotone" className="text-amber" aria-hidden="true" /><div><p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-amber">Safety boundary</p><h2 className="mt-2 text-lg font-semibold text-foreground">Human review is part of the workflow.</h2><p className="mt-2 text-sm leading-6 text-muted">AgriSage AI can draft an advisory. A named extension officer must approve, edit, or reject it before it can be used.</p><Link href="/advisories" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline">Review advisories <ArrowRight size={16} aria-hidden="true" /></Link></div></div></Panel>
      </section>
    </div>
  );
}

function PlantIcon() {
  return <span className="inline-flex text-forest" aria-hidden="true"><Plant size={20} weight="duotone" /></span>;
}
