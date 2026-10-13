"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowLeft, ChartLineUp, Drop, Leaf, MapPinLine, Ruler, Thermometer, WarningCircle, Wind } from "@phosphor-icons/react";
import { useParams } from "next/navigation";
import { getFarm } from "@/services/farms";
import type { Farm } from "@/types/api";
import { EvidenceChain } from "@/components/evidence";
import { MissingEvidencePanel } from "@/components/farms";
import { ConfidenceIndicator, DataUnavailable, Panel, RiskBadge, SectionHeader } from "@/components/ui";

function formatDate(value?: string | null) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(new Date(value));
}

export default function FarmDetailPage() {
  return <Suspense fallback={<div className="mx-auto max-w-[1200px] space-y-6"><div className="h-8 w-32 animate-pulse rounded-lg bg-surface-muted" /><div className="h-48 animate-pulse rounded-2xl bg-surface-muted" /><div className="grid gap-6 lg:grid-cols-2"><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /></div></div>}><FarmDetailContent /></Suspense>;
}

function FarmDetailContent() {
  const params = useParams<{ farmId: string }>();
  const farmId = params.farmId;
  const [farm, setFarm] = useState<Farm | null>(null);
  const [error, setError] = useState(false);
  const load = useCallback(async () => { try { setFarm(await getFarm(farmId)); setError(false); } catch { setError(true); } }, [farmId]);
  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  if (error) return <div className="mx-auto max-w-[1200px] space-y-6"><Link href="/farms" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline"><ArrowLeft size={16} /> Back to farms</Link><DataUnavailable endpoint={`GET /api/farms/${farmId}`} onRetry={() => void load()} title="Farm detail unavailable" description="This farm could not be loaded from the backend. No plot context or risk assessment is being inferred." /></div>;
  if (!farm) return <div className="mx-auto max-w-[1200px] space-y-6"><div className="h-8 w-32 animate-pulse rounded-lg bg-surface-muted" /><div className="h-48 animate-pulse rounded-2xl bg-surface-muted" /><div className="grid gap-6 lg:grid-cols-2"><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /></div></div>;

  const missing = farm.missing_evidence ?? [
    ...(farm.planting_date ? [] : ["planting date"]),
    ...(farm.current_growth_stage ? [] : ["current crop stage"]),
    ...(farm.soil_type ? [] : ["soil type"]),
  ];

  return (
    <div className="mx-auto max-w-[1400px] space-y-8">
      <Link href="/farms" className="inline-flex items-center gap-2 text-sm font-semibold text-forest hover:underline"><ArrowLeft size={16} /> Back to farm register</Link>
      <section className="rounded-2xl border border-line bg-surface p-6 shadow-[0_12px_32px_rgba(28,52,39,0.04)] sm:p-8"><div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between"><div><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">Farm detail / {farm.agroclimatic_zone}</p><div className="mt-3 flex flex-wrap items-center gap-4"><h2 className="font-mono text-3xl font-semibold tracking-tight text-foreground">{farm.farm_id}</h2><RiskBadge risk={farm.risk_level} /></div><p className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted"><span className="flex items-center gap-2"><MapPinLine size={16} aria-hidden="true" />{farm.district}</span><span className="flex items-center gap-2"><Leaf size={16} aria-hidden="true" />{farm.crop} · {farm.crop_variety}</span><span className="flex items-center gap-2"><Ruler size={16} aria-hidden="true" />{farm.field_size_ha} ha</span></p></div><div className="min-w-56"><p className="mb-2 text-xs font-semibold uppercase tracking-[0.12em] text-muted">Current confidence</p><ConfidenceIndicator value={farm.confidence} /></div></div></section>

      {missing.length > 0 && <MissingEvidencePanel farmId={farm.farm_id} missing={missing} />}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Panel><SectionHeader eyebrow="Plot context" title="Farm context" description="The records that ground any later risk assessment." /><div className="grid gap-4 sm:grid-cols-2">{[
          ["Crop", farm.crop], ["Variety", farm.crop_variety], ["Planting date", formatDate(farm.planting_date)], ["Growth stage", farm.current_growth_stage ?? "Not recorded"], ["Soil type", farm.soil_type ?? "Not recorded"], ["Previous crop", farm.previous_crop ?? "Not recorded"], ["Irrigation", farm.irrigation_type], ["Last inspection", formatDate(farm.last_inspection_date)],
        ].map(([label, value]) => <div key={label} className="rounded-xl bg-surface-muted/55 p-4"><p className="text-xs font-medium uppercase tracking-[0.12em] text-muted">{label}</p><p className="mt-2 text-sm font-semibold text-foreground">{value}</p></div>)}</div><div className="mt-5 grid gap-4 border-t border-line pt-5 md:grid-cols-3"><HistoryBlock label="Previous pest incidents" values={farm.previous_pest_incidents.map((item) => JSON.stringify(item))} /><HistoryBlock label="Previous disease incidents" values={farm.previous_disease_incidents.map((item) => JSON.stringify(item))} /><HistoryBlock label="Previous interventions" values={farm.previous_interventions} /></div></Panel>

        <Panel><SectionHeader eyebrow="Environmental evidence" title="Climate signals" description="Signal freshness and confidence are part of the evidence, not hidden metadata." />{farm.climate ? <div className="grid gap-4 sm:grid-cols-2"><ClimateMetric icon={<Drop size={18} weight="duotone" />} label="Rainfall, 7 days" value={farm.climate.rainfall_mm_7d === null ? "Unavailable" : `${farm.climate.rainfall_mm_7d} mm`} /><ClimateMetric icon={<Wind size={18} weight="duotone" />} label="Forecast, 7 days" value={farm.climate.forecast_rainfall_mm_7d === null ? "Unavailable" : `${farm.climate.forecast_rainfall_mm_7d} mm`} /><ClimateMetric icon={<Thermometer size={18} weight="duotone" />} label="Temperature" value={farm.climate.average_temperature_c === null ? "Unavailable" : `${farm.climate.average_temperature_c} °C`} /><ClimateMetric icon={<ChartIcon />} label="Rainfall anomaly" value={farm.climate.rainfall_anomaly_pct === null ? "Unavailable" : `${farm.climate.rainfall_anomaly_pct}%`} /></div> : <DataUnavailable endpoint="GET /api/farms/:id with climate context" title="Climate data not attached" description="The farm record loaded without a climate signal. A reliable farm specific advisory should wait for current climate evidence." />} {farm.climate && <div className="mt-5 grid gap-3 border-t border-line pt-5 text-sm"><div className="flex items-center justify-between gap-4"><span className="text-muted">Signal status</span><span className="font-semibold text-foreground">{farm.climate.availability_status}</span></div><div className="flex items-center justify-between gap-4"><span className="text-muted">Drought indicator</span><span className="font-semibold text-foreground">{farm.climate.drought_indicator === null ? "Unavailable" : farm.climate.drought_indicator ? "Detected" : "Not detected"}</span></div><div className="flex items-center justify-between gap-4"><span className="text-muted">Heavy rain indicator</span><span className="font-semibold text-foreground">{farm.climate.heavy_rain_indicator === null ? "Unavailable" : farm.climate.heavy_rain_indicator ? "Detected" : "Not detected"}</span></div><div className="flex items-center justify-between gap-4"><span className="text-muted">Source confidence</span><ConfidenceIndicator value={farm.climate.data_confidence} /></div></div>}</Panel>
      </div>

      <Panel><SectionHeader eyebrow="Signal review" title="Pest signals" description="Nearby reports guide inspection priority. They do not prove a plot level infestation." />{farm.pest_signals && farm.pest_signals.length > 0 ? <div className="overflow-x-auto rounded-xl border border-line"><table className="min-w-full divide-y divide-line text-left"><thead className="bg-surface-muted/60"><tr>{["Pest", "Reports", "Severity", "Reported", "Confidence", "Source"].map((heading) => <th key={heading} scope="col" className="whitespace-nowrap px-4 py-3 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-muted">{heading}</th>)}</tr></thead><tbody className="divide-y divide-line">{farm.pest_signals.map((signal) => <tr key={signal.signal_id}><td className="px-4 py-4 text-sm font-semibold text-foreground">{signal.pest_type}</td><td className="px-4 py-4 font-mono text-sm text-foreground">{signal.report_count}</td><td className="px-4 py-4 text-sm font-semibold text-amber">{signal.severity}</td><td className="px-4 py-4 text-sm text-muted">{formatDate(signal.report_date)}</td><td className="px-4 py-4"><ConfidenceIndicator value={signal.confidence} /></td><td className="px-4 py-4 font-mono text-xs text-muted">{signal.source}</td></tr>)}</tbody></table></div> : <DataUnavailable endpoint="GET /api/farms/:id with pest signals" title="No pest signal set returned" description="No nearby report set is attached to this farm. The absence of a signal is not treated as proof that no pest is present." />}</Panel>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]"><Panel><SectionHeader eyebrow="Signature feature" title="Evidence chain" description="Follow the path from retrieved signals to a proposed next action." /><EvidenceChain evidence={farm.supporting_evidence ?? []} risk={farm.risk_level} nextAction={farm.recommended_next_action} missingEvidence={farm.missing_evidence} /></Panel>{farm.risk_factors && farm.risk_factors.length > 0 ? <Panel><SectionHeader eyebrow="Decision context" title="Why this risk level?" /><ul className="space-y-3">{farm.risk_factors.map((factor) => <li key={factor} className="flex items-start gap-3 text-sm leading-6 text-muted"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-forest" aria-hidden="true" />{factor}</li>)}</ul>{farm.last_analysed_at && <p className="mt-5 border-t border-line pt-4 font-mono text-xs text-muted">Last analysed: {formatDate(farm.last_analysed_at)}</p>}</Panel> : <Panel><SectionHeader eyebrow="Decision context" title="No risk assessment returned" /><div className="rounded-xl border border-dashed border-line-strong bg-surface-muted/40 p-6 text-center"><WarningCircle size={24} className="mx-auto text-amber" aria-hidden="true" /><p className="mt-3 text-sm font-semibold text-foreground">Risk factors are not available yet.</p><p className="mt-2 text-sm leading-6 text-muted">Connect the analysis endpoint to render a decision explanation.</p></div></Panel>}</div>
    </div>
  );
}

function HistoryBlock({ label, values }: { label: string; values: string[] }) { return <div><p className="text-xs font-medium uppercase tracking-[0.12em] text-muted">{label}</p>{values.length > 0 ? <ul className="mt-3 space-y-2 text-sm text-foreground">{values.map((value) => <li key={value} className="line-clamp-2">{value}</li>)}</ul> : <p className="mt-3 text-sm text-muted">No records</p>}</div>; }
function ClimateMetric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) { return <div className="rounded-xl bg-surface-muted/55 p-4"><span className="text-forest" aria-hidden="true">{icon}</span><p className="mt-4 text-xs font-medium uppercase tracking-[0.12em] text-muted">{label}</p><p className="mt-2 font-mono text-lg font-semibold text-foreground">{value}</p></div>; }
function ChartIcon() { return <ChartLineUp size={18} weight="duotone" />; }
