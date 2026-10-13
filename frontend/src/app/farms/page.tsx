"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Funnel, MagnifyingGlass, MapPinLine, Plant } from "@phosphor-icons/react";
import { getFarms } from "@/services/farms";
import type { Farm } from "@/types/api";
import { FarmTable } from "@/components/farms";
import { DataUnavailable, Panel, SectionHeader } from "@/components/ui";

export default function FarmsPage() {
  const [farms, setFarms] = useState<Farm[] | null>(null);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("all");
  const [crop, setCrop] = useState("all");
  const [risk, setRisk] = useState("all");
  const [zone, setZone] = useState("all");

  const load = useCallback(async () => {
    try { setFarms(await getFarms()); setError(false); } catch { setError(true); }
  }, []);
  // This effect bridges the client component to the live API.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  const options = useMemo(() => ({
    districts: [...new Set(farms?.map((farm) => farm.district) ?? [])].sort(),
    crops: [...new Set(farms?.map((farm) => farm.crop) ?? [])].sort(),
    zones: [...new Set(farms?.map((farm) => farm.agroclimatic_zone) ?? [])].sort(),
  }), [farms]);

  const filtered = useMemo(() => farms?.filter((farm) => {
    const matchesQuery = !query || [farm.farm_id, farm.district, farm.crop, farm.crop_variety].some((field) => field.toLowerCase().includes(query.toLowerCase()));
    return matchesQuery && (district === "all" || farm.district === district) && (crop === "all" || farm.crop === crop) && (risk === "all" || farm.risk_level === risk) && (zone === "all" || farm.agroclimatic_zone === zone);
  }) ?? [], [farms, query, district, crop, risk, zone]);

  return (
    <div className="mx-auto max-w-[1600px] space-y-8">
      <section><p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">Monitoring register</p><h2 className="mt-3 text-3xl font-semibold tracking-tight text-foreground text-balance">Every plot, with its evidence context.</h2><p className="mt-3 max-w-2xl text-base leading-7 text-muted text-pretty">Search the farm register and filter the current risk picture. Missing data stays visible so the office can follow up before an advisory is drafted.</p></section>
      <Panel>
        <SectionHeader eyebrow="Farm register" title="Search and filter farms" description={farms ? `${filtered.length} of ${farms.length} records shown` : "Waiting for the farm API"} />
        <div className="grid gap-3 border-b border-line pb-5 md:grid-cols-2 xl:grid-cols-5">
          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-line bg-surface px-3 md:col-span-2 xl:col-span-1"><MagnifyingGlass size={17} className="text-muted" aria-hidden="true" /><span className="sr-only">Search farms</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search farms" className="min-w-0 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted" /></label>
          <FilterSelect label="District" value={district} onChange={setDistrict} options={options.districts} />
          <FilterSelect label="Crop" value={crop} onChange={setCrop} options={options.crops} icon={<Plant size={15} aria-hidden="true" />} />
          <FilterSelect label="Risk" value={risk} onChange={setRisk} options={["HIGH", "MODERATE", "LOW", "INSUFFICIENT_EVIDENCE"]} />
          <FilterSelect label="Agroclimatic zone" value={zone} onChange={setZone} options={options.zones} icon={<MapPinLine size={15} aria-hidden="true" />} />
        </div>
        <div className="mt-5 flex items-center gap-2 text-xs text-muted"><Funnel size={15} aria-hidden="true" />Filters are derived from backend records.</div>
        <div className="mt-4">
          {error && <DataUnavailable endpoint="GET /api/farms" onRetry={() => void load()} title="Farm register unavailable" description="No farm rows are shown because the register endpoint did not respond." />}
          {!error && !farms && <div className="h-80 animate-pulse rounded-xl bg-surface-muted" />}
          {!error && farms && <FarmTable farms={filtered} />}
        </div>
      </Panel>
    </div>
  );
}

function FilterSelect({ label, value, onChange, options, icon }: { label: string; value: string; onChange: (value: string) => void; options: string[]; icon?: ReactNode }) {
  return <label className="relative"><span className="sr-only">Filter by {label}</span>{icon && <span className="pointer-events-none absolute left-3 top-3 text-muted">{icon}</span>}<select aria-label={`Filter by ${label}`} value={value} onChange={(event) => onChange(event.target.value)} className={`h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-foreground ${icon ? "pl-9" : ""}`}><option value="all">All {label.toLowerCase()}</option>{options.map((option) => <option key={option} value={option}>{option.replaceAll("_", " ")}</option>)}</select></label>;
}
