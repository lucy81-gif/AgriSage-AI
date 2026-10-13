"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ShieldCheck, WarningCircle } from "@phosphor-icons/react";
import { useParams } from "next/navigation";
import { getAdvisory } from "@/services/advisories";
import type { Advisory } from "@/types/api";
import { AdvisoryEvidence, ApprovalPanel } from "@/components/advisories";
import { DataUnavailable, Panel, RiskBadge, SectionHeader } from "@/components/ui";

function formatDate(value?: string | null) { return value ? new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Not recorded"; }

export default function AdvisoryDetailPage() {
  return <Suspense fallback={<div className="mx-auto max-w-[1200px] space-y-6"><div className="h-8 w-40 animate-pulse rounded-lg bg-surface-muted" /><div className="h-52 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /></div>}><AdvisoryDetailContent /></Suspense>;
}

function AdvisoryDetailContent() {
  const params = useParams<{ advisoryId: string }>();
  const advisoryId = params.advisoryId;
  const [advisory, setAdvisory] = useState<Advisory | null>(null);
  const [error, setError] = useState(false);
  const load = useCallback(async () => { try { setAdvisory(await getAdvisory(advisoryId)); setError(false); } catch { setError(true); } }, [advisoryId]);
  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  if (error) return <div className="mx-auto max-w-[1200px] space-y-6"><Link href="/advisories" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline"><ArrowLeft size={16} /> Back to advisories</Link><DataUnavailable endpoint={`GET /api/advisories/${advisoryId}`} onRetry={() => void load()} title="Advisory detail unavailable" description="The advisory could not be loaded. No approval control is shown until the backend record is available." /></div>;
  if (!advisory) return <div className="mx-auto max-w-[1200px] space-y-6"><div className="h-8 w-40 animate-pulse rounded-lg bg-surface-muted" /><div className="h-52 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /></div>;

  return <div className="mx-auto max-w-[1300px] space-y-8"><Link href="/advisories" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline"><ArrowLeft size={16} /> Back to advisory register</Link><section className="rounded-2xl border border-line bg-surface p-6 shadow-[0_12px_32px_rgba(28,52,39,0.04)] sm:p-8"><div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between"><div><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">AI generated advisory</p><h2 className="mt-3 font-mono text-3xl font-semibold tracking-tight text-foreground">{advisory.advisory_id}</h2><p className="mt-3 text-sm text-muted">Farm {advisory.farm_id}{advisory.crop ? ` · ${advisory.crop}` : ""} · Created {formatDate(advisory.created_at)}</p></div><div className="flex flex-wrap items-center gap-3"><RiskBadge risk={advisory.risk_level} /><span className="rounded-full bg-sage-soft px-3 py-1 text-xs font-semibold text-forest">Confidence {advisory.confidence === null ? "unavailable" : `${Math.round(advisory.confidence * 100)}%`}</span></div></div></section><ApprovalPanel advisory={advisory} onUpdated={setAdvisory} /><div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]"><Panel><SectionHeader eyebrow="Recommendation" title="Proposed next step" description="Review the wording together with its evidence before taking action." /><div className="rounded-xl border border-line bg-surface-muted/45 p-5"><p className="text-base leading-7 text-foreground text-pretty">{advisory.recommendation}</p></div>{advisory.reason && <div className="mt-5"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Reason</p><p className="mt-2 text-sm leading-6 text-muted">{advisory.reason}</p></div>}</Panel><Panel><SectionHeader eyebrow="Evidence quality" title="What is missing?" />{advisory.missing_information.length > 0 ? <div className="flex items-start gap-3 rounded-xl border border-amber/25 bg-amber-soft/50 p-4"><WarningCircle size={19} weight="duotone" className="mt-0.5 shrink-0 text-amber" aria-hidden="true" /><div><p className="text-sm font-semibold text-foreground">This advisory has known gaps.</p><ul className="mt-3 space-y-2 text-sm leading-6 text-muted">{advisory.missing_information.map((item) => <li key={item}>• {item}</li>)}</ul></div></div> : <div className="flex items-start gap-3 rounded-xl border border-forest/15 bg-sage-soft/50 p-4"><ShieldCheck size={19} weight="duotone" className="mt-0.5 shrink-0 text-forest" aria-hidden="true" /><p className="text-sm leading-6 text-forest">The backend returned no missing information for this record.</p></div>}</Panel></div><Panel><SectionHeader eyebrow="Evidence chain" title="Why this recommendation exists" description="Each item should point back to a tool result or a plot record." /><AdvisoryEvidence advisory={advisory} /></Panel></div>;
}
