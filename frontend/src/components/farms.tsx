"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, CalendarBlank, CheckCircle, CircleNotch, MapPinLine, Plant, Ruler, WarningCircle } from "@phosphor-icons/react";
import type { Farm } from "@/types/api";
import { createFollowUp } from "@/services/followups";
import { ConfidenceIndicator, EmptyState, RiskBadge } from "./ui";

function formatDate(value?: string | null) {
  if (!value) return "Not recorded";
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(new Date(value));
}

export function FarmCard({ farm, compact = false }: { farm: Farm; compact?: boolean }) {
  return (
    <article className={`rounded-2xl border border-line bg-surface p-5 shadow-[0_12px_32px_rgba(28,52,39,0.04)] transition-transform duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-y-0.5 ${compact ? "" : "h-full"}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link href={`/farms/${farm.farm_id}`} className="font-mono text-sm font-semibold text-forest underline decoration-forest/25 underline-offset-4 hover:decoration-forest">{farm.farm_id}</Link>
          <p className="mt-2 flex items-center gap-2 text-sm text-muted"><Plant size={16} weight="duotone" className="text-forest" aria-hidden="true" />{farm.crop}{farm.crop_variety ? ` · ${farm.crop_variety}` : ""}</p>
        </div>
        <RiskBadge risk={farm.risk_level} />
      </div>

      <div className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
        <div className="flex items-center gap-2 text-muted"><MapPinLine size={16} aria-hidden="true" />{farm.district}</div>
        <div className="flex items-center gap-2 text-muted"><Ruler size={16} aria-hidden="true" />{farm.field_size_ha ? `${farm.field_size_ha} ha` : "Field size unavailable"}</div>
      </div>

      <div className="mt-5 border-t border-line pt-4">
        <div className="flex items-center justify-between gap-4"><span className="text-xs font-medium uppercase tracking-[0.12em] text-muted">Confidence</span><ConfidenceIndicator value={farm.confidence} /></div>
        {farm.rank_reason && <p className="mt-3 text-sm leading-6 text-muted text-pretty">{farm.rank_reason}</p>}
        {farm.recommended_next_action && <p className="mt-3 rounded-xl bg-sage-soft/60 px-3 py-2 text-sm font-medium text-forest">Next step: {farm.recommended_next_action}</p>}
      </div>

      <div className="mt-5 flex items-center justify-between gap-4 text-xs text-muted">
        <span className="flex items-center gap-2"><CalendarBlank size={15} aria-hidden="true" />Inspected {formatDate(farm.last_inspection_date)}</span>
        <Link href={`/farms/${farm.farm_id}`} className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 text-xs font-semibold text-forest hover:bg-sage-soft">View evidence <ArrowUpRight size={14} aria-hidden="true" /></Link>
      </div>
    </article>
  );
}

export function FarmTable({ farms }: { farms: Farm[] }) {
  if (farms.length === 0) return <EmptyState title="No farms match these filters" description="Try a different district, crop, risk level, or advisory status." />;
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="min-w-full divide-y divide-line text-left">
        <thead className="bg-surface-muted/60"><tr>{["Farm ID", "District", "Crop", "Stage", "Soil", "Risk", "Confidence", "Last inspection", "Advisory"].map((heading) => <th key={heading} scope="col" className="whitespace-nowrap px-4 py-3 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-muted">{heading}</th>)}</tr></thead>
        <tbody className="divide-y divide-line bg-surface">
          {farms.map((farm) => <tr key={farm.farm_id} className="transition-colors duration-300 hover:bg-surface-muted/50">
            <td className="whitespace-nowrap px-4 py-4"><Link href={`/farms/${farm.farm_id}`} className="font-mono text-sm font-semibold text-forest underline decoration-forest/25 underline-offset-4">{farm.farm_id}</Link></td>
            <td className="whitespace-nowrap px-4 py-4 text-sm text-muted">{farm.district}</td>
            <td className="whitespace-nowrap px-4 py-4 text-sm font-medium text-foreground">{farm.crop}</td>
            <td className="whitespace-nowrap px-4 py-4 text-sm text-muted">{farm.current_growth_stage ?? "Not recorded"}</td>
            <td className="whitespace-nowrap px-4 py-4 text-sm text-muted">{farm.soil_type ?? "Not recorded"}</td>
            <td className="whitespace-nowrap px-4 py-4"><RiskBadge risk={farm.risk_level} /></td>
            <td className="whitespace-nowrap px-4 py-4"><ConfidenceIndicator value={farm.confidence} /></td>
            <td className="whitespace-nowrap px-4 py-4 text-sm text-muted">{formatDate(farm.last_inspection_date)}</td>
            <td className="whitespace-nowrap px-4 py-4 text-sm text-muted">{farm.advisory_status?.replaceAll("_", " ") ?? "Not available"}</td>
          </tr>)}
        </tbody>
      </table>
    </div>
  );
}

export function MissingEvidencePanel({ farmId, missing }: { farmId: string; missing: string[] }) {
  const [working, setWorking] = useState(false);
  const [created, setCreated] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    setWorking(true);
    setError(null);
    try {
      await createFollowUp(farmId, missing.join("; "), missing.length > 1 ? "HIGH" : "MODERATE");
      setCreated(true);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The follow up task could not be created.");
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="rounded-2xl border border-amber/25 bg-amber-soft/50 p-5">
      <div className="flex items-start gap-3"><WarningCircle size={21} weight="duotone" className="mt-0.5 shrink-0 text-amber" aria-hidden="true" /><div><p className="text-base font-semibold text-foreground">Insufficient evidence</p><p className="mt-1 text-sm leading-6 text-muted">AgriSage AI cannot generate a reliable farm specific advisory yet.</p><ul className="mt-4 space-y-2 text-sm text-foreground">{missing.map((item) => <li key={item} className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-amber" aria-hidden="true" />{item}</li>)}</ul><button type="button" onClick={() => void handleCreate()} disabled={working || created} className="mt-5 inline-flex min-h-10 items-center gap-2 rounded-xl border border-amber/30 bg-surface px-4 text-sm font-semibold text-amber hover:bg-amber-soft disabled:cursor-not-allowed disabled:opacity-60">{working ? <><CircleNotch size={16} className="animate-spin" aria-hidden="true" /> Creating follow up</> : created ? <><CheckCircle size={16} weight="fill" aria-hidden="true" /> Follow up task created</> : "Create follow up task"}</button>{error && <p className="mt-3 text-sm text-risk-red">{error}</p>}</div></div>
    </div>
  );
}
