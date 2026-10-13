"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardText, Funnel, ShieldCheck } from "@phosphor-icons/react";
import { getAdvisories } from "@/services/advisories";
import type { Advisory } from "@/types/api";
import { AdvisoryCard } from "@/components/advisories";
import { DataUnavailable, EmptyState, Panel, SectionHeader } from "@/components/ui";

const statuses = ["ALL", "PENDING_APPROVAL", "APPROVED", "EDITED", "REJECTED"];

export default function AdvisoriesPage() {
  const [advisories, setAdvisories] = useState<Advisory[] | null>(null);
  const [status, setStatus] = useState("ALL");
  const [error, setError] = useState(false);
  const load = useCallback(async () => { try { setAdvisories(await getAdvisories()); setError(false); } catch { setError(true); } }, []);
  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);
  const filtered = useMemo(() => advisories?.filter((advisory) => status === "ALL" || advisory.status === status) ?? [], [advisories, status]);

  return <div className="mx-auto max-w-[1400px] space-y-8"><section><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">Officer review</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground text-balance">Advisories stop here before they travel.</h2><p className="mt-3 max-w-2xl text-base leading-7 text-muted text-pretty">Every recommendation keeps its evidence, missing information, and human approval status in the same review surface.</p></section><Panel><SectionHeader eyebrow="Advisory register" title="AI generated advisory records" description={advisories ? `${filtered.length} of ${advisories.length} records shown` : "Waiting for the advisory API"} action={<span className="inline-flex items-center gap-2 text-xs font-semibold text-forest"><ShieldCheck size={16} weight="duotone" aria-hidden="true" /> Human approval required</span>} /><div className="flex flex-wrap gap-2 border-b border-line pb-5" role="group" aria-label="Filter advisories by status">{statuses.map((item) => <button type="button" key={item} aria-pressed={status === item} onClick={() => setStatus(item)} className={`min-h-10 rounded-xl px-3 text-sm font-semibold transition-colors duration-300 ${status === item ? "bg-forest text-white" : "bg-surface-muted text-muted hover:text-foreground"}`}>{item === "ALL" ? "All statuses" : item.replaceAll("_", " ")}</button>)}</div><div className="mt-5">{error && <DataUnavailable endpoint="GET /api/advisories" onRetry={() => void load()} title="Advisories unavailable" description="No advisory records are shown because the backend did not return them." />}{!error && !advisories && <div className="grid gap-4 lg:grid-cols-2"><div className="h-56 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-56 animate-pulse rounded-2xl bg-surface-muted" /></div>}{!error && advisories && filtered.length === 0 && <EmptyState title="No advisories in this status" description="The API returned no advisory records for the current filter." icon={<ClipboardText size={22} weight="duotone" />} />}{!error && advisories && filtered.length > 0 && <div className="grid gap-4 lg:grid-cols-2">{filtered.map((advisory) => <AdvisoryCard key={advisory.advisory_id} advisory={advisory} />)}</div>}</div><div className="mt-6 flex items-start gap-3 rounded-xl border border-line bg-surface-muted/40 p-4"><Funnel size={18} className="mt-0.5 shrink-0 text-forest" aria-hidden="true" /><p className="text-sm leading-6 text-muted">Filters are applied to records returned by the backend. The frontend never invents an approval state.</p></div></Panel></div>;
}
