"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, GitBranch, Queue, WarningCircle } from "@phosphor-icons/react";
import { getFarms } from "@/services/farms";
import type { Farm, RiskLevel } from "@/types/api";
import { FarmCard } from "@/components/farms";
import { DataUnavailable, EmptyState, Panel, SectionHeader } from "@/components/ui";

const groups: Array<{ risk: RiskLevel; title: string; description: string }> = [
  { risk: "HIGH", title: "High priority", description: "Evidence supports prompt field inspection." },
  { risk: "MODERATE", title: "Moderate priority", description: "Review after high priority cases or when new signals arrive." },
  { risk: "LOW", title: "Low priority", description: "No current risk signal requires urgent intervention." },
  { risk: "INSUFFICIENT_EVIDENCE", title: "Insufficient evidence", description: "Follow up on missing or conflicting information before advising." },
];

export default function PriorityQueuePage() {
  const [farms, setFarms] = useState<Farm[] | null>(null);
  const [error, setError] = useState(false);
  const load = useCallback(async () => { try { setFarms(await getFarms()); setError(false); } catch { setError(true); } }, []);
  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  const ranked = useMemo(() => farms?.slice().sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0)) ?? [], [farms]);

  return (
    <div className="mx-auto max-w-[1400px] space-y-8">
      <section><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">Backlog triage</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground text-balance">A queue that explains its urgency.</h2><p className="mt-3 max-w-2xl text-base leading-7 text-muted text-pretty">Prioritisation is only useful when an officer can see why one farm appears before another. Each section stays tied to returned evidence and confidence.</p></section>
      {error && <DataUnavailable endpoint="GET /api/farms or GET /api/priority-queue" onRetry={() => void load()} title="Priority queue unavailable" description="The queue cannot be populated without current farm risk assessments. No farms are ranked locally." />}
      {!error && !farms && <div className="grid gap-6 lg:grid-cols-2"><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /><div className="h-72 animate-pulse rounded-2xl bg-surface-muted" /></div>}
      {!error && farms && <>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{groups.map((group) => <div key={group.risk} className="rounded-2xl border border-line bg-surface p-5"><div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold text-foreground">{group.title}</span><span className="font-mono text-2xl font-semibold text-foreground">{farms.filter((farm) => farm.risk_level === group.risk).length}</span></div><p className="mt-2 text-sm leading-6 text-muted">{group.description}</p></div>)}</div>
        <div className="space-y-6">{groups.map((group, groupIndex) => <PriorityGroup key={group.risk} group={group} farms={ranked.filter((farm) => farm.risk_level === group.risk)} higherGroup={groups[groupIndex - 1]} />)}</div>
      </>}
    </div>
  );
}

function PriorityGroup({ group, farms, higherGroup }: { group: (typeof groups)[number]; farms: Farm[]; higherGroup?: (typeof groups)[number] }) {
  return <Panel><SectionHeader eyebrow="Queue section" title={group.title} description={group.description} action={<span className="inline-flex items-center gap-2 text-xs font-semibold text-muted"><Queue size={16} aria-hidden="true" />{farms.length} farms</span>} />{farms.length === 0 ? <EmptyState title={`No ${group.title.toLowerCase()} farms returned`} description="This is a live state from the analysis API, not a placeholder row." icon={<Queue size={22} weight="duotone" />} /> : <div className="grid gap-4 lg:grid-cols-2">{farms.map((farm) => <div key={farm.farm_id} className="space-y-3"><FarmCard farm={farm} /><details className="group rounded-xl border border-line bg-surface-muted/40"><summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3 text-sm font-semibold text-foreground [&::-webkit-details-marker]:hidden"><GitBranch size={16} className="text-forest" aria-hidden="true" /> Why ranked here? <ArrowDown size={15} className="ml-auto text-muted transition-transform duration-300 group-open:rotate-180" aria-hidden="true" /></summary><div className="border-t border-line px-4 py-4 text-sm leading-6 text-muted"><p>{farm.rank_reason ?? "The backend did not return a ranking explanation for this farm."}</p>{higherGroup && <p className="mt-3 flex items-center gap-2 text-xs text-muted"><ArrowUp size={14} className="text-forest" aria-hidden="true" />Compared with {higherGroup.title.toLowerCase()}, this section reflects a lower returned urgency level.</p>}{farm.missing_evidence && farm.missing_evidence.length > 0 && <p className="mt-3 flex items-start gap-2 text-xs text-amber"><WarningCircle size={15} className="mt-0.5 shrink-0" aria-hidden="true" />Missing: {farm.missing_evidence.join(", ")}</p>}</div></details></div>)}</div>}</Panel>;
}
