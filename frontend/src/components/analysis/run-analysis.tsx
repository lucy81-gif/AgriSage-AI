"use client";

import { FormEvent, useState } from "react";
import { ArrowRight, CheckCircle, CircleNotch, MagnifyingGlass, WarningCircle } from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { runAnalysis } from "@/services/analysis";
import type { AnalysisRequest, Farm } from "@/types/api";

export function RunAnalysisButton({ districts = [], crops = [], farms = [] }: { districts?: string[]; crops?: string[]; farms?: Farm[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [scope, setScope] = useState<AnalysisRequest["scope"]>("all");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSubmitted(null);
    const form = new FormData(event.currentTarget);
    const selectedScope = String(form.get("scope") || "all") as AnalysisRequest["scope"];
    const farmId = String(form.get("farm_id") || "");
    if (selectedScope === "farm" && !farmId) {
      setError("Choose a farm record before running a one-farm analysis.");
      setSubmitting(false);
      return;
    }
    const request: AnalysisRequest = {
      district: String(form.get("district") || "") || undefined,
      crop: String(form.get("crop") || "") || undefined,
      scope: selectedScope,
      farm_id: selectedScope === "farm" ? farmId : undefined,
      analysis_start: String(form.get("analysis_start") || "") || undefined,
      analysis_end: String(form.get("analysis_end") || "") || undefined,
    };

    try {
      const response = await runAnalysis(request);
      setSubmitted(response.workflow_run_id);
      router.push("/priority-queue");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "The analysis request could not be submitted.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white shadow-sm transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-y-0.5 active:translate-y-px"><MagnifyingGlass size={17} weight="bold" aria-hidden="true" /> Run climate smart analysis <ArrowRight size={16} weight="bold" aria-hidden="true" /></button>
      {open && <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest-deep/45 p-5" role="dialog" aria-modal="true" aria-labelledby="analysis-dialog-title">
        <div className="w-full max-w-lg rounded-2xl border border-line bg-surface p-6 shadow-2xl">
          <div className="flex items-start justify-between gap-4"><div><p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-forest">Start an investigation</p><h2 id="analysis-dialog-title" className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Run climate smart analysis</h2><p className="mt-2 text-sm leading-6 text-muted">The backend will retrieve dated evidence, calculate structured risk, and stop every draft at officer approval.</p></div><button type="button" onClick={() => setOpen(false)} aria-label="Close analysis form" className="flex h-10 w-10 items-center justify-center rounded-xl text-muted hover:bg-surface-muted hover:text-foreground">×</button></div>
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div><label htmlFor="analysis-scope" className="mb-2 block text-sm font-semibold text-foreground">Scope</label><select id="analysis-scope" name="scope" value={scope} onChange={(event) => setScope(event.target.value as AnalysisRequest["scope"])} className="h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-foreground"><option value="all">All eligible farms</option><option value="cluster">A farm cluster</option><option value="farm">One farm</option></select></div>
            {scope === "farm" && <div><label htmlFor="analysis-farm" className="mb-2 block text-sm font-semibold text-foreground">Farm record</label><select id="analysis-farm" name="farm_id" required className="h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-foreground"><option value="">Choose a farm</option>{farms.map((farm) => <option key={farm.farm_id} value={farm.farm_id}>{farm.farm_id} · {farm.district} · {farm.crop}</option>)}</select>{farms.length === 0 && <p className="mt-2 text-sm text-amber">Farm records have not loaded from the backend yet.</p>}</div>}
            <div className="grid gap-4 sm:grid-cols-2"><div><label htmlFor="analysis-district" className="mb-2 block text-sm font-semibold text-foreground">District <span className="font-normal text-muted">optional</span></label><select id="analysis-district" name="district" defaultValue="" className="h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-foreground"><option value="">All districts</option>{districts.map((district) => <option key={district} value={district}>{district}</option>)}</select></div><div><label htmlFor="analysis-crop" className="mb-2 block text-sm font-semibold text-foreground">Crop <span className="font-normal text-muted">optional</span></label><select id="analysis-crop" name="crop" defaultValue="" className="h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-foreground"><option value="">All crops</option>{crops.map((crop) => <option key={crop} value={crop}>{crop}</option>)}</select></div></div>
            <div className="grid gap-4 sm:grid-cols-2"><div><label htmlFor="analysis-start" className="mb-2 block text-sm font-semibold text-foreground">Analysis start</label><input id="analysis-start" name="analysis_start" type="date" defaultValue="2026-10-01" className="h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-foreground" /></div><div><label htmlFor="analysis-end" className="mb-2 block text-sm font-semibold text-foreground">Analysis end</label><input id="analysis-end" name="analysis_end" type="date" defaultValue="2026-10-08" className="h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-foreground" /></div></div>
            {error && <div role="alert" className="flex items-start gap-3 rounded-xl border border-risk-red/20 bg-risk-red-soft p-4 text-sm text-risk-red"><WarningCircle size={18} weight="duotone" className="mt-0.5 shrink-0" aria-hidden="true" /><span>{error}</span></div>}
            {submitted && <div className="flex items-start gap-3 rounded-xl border border-forest/15 bg-sage-soft p-4 text-sm text-forest"><CheckCircle size={18} weight="duotone" className="mt-0.5 shrink-0" aria-hidden="true" /><span>Investigation {submitted} submitted. The priority queue will update when the analysis completes.</span></div>}
            <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end"><button type="button" onClick={() => setOpen(false)} className="min-h-11 rounded-xl px-4 text-sm font-semibold text-muted hover:bg-surface-muted">Cancel</button><button type="submit" disabled={submitting} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">{submitting ? <><CircleNotch size={17} className="animate-spin" aria-hidden="true" /> Submitting request</> : <>Submit investigation <ArrowRight size={16} weight="bold" aria-hidden="true" /></>}</button></div>
          </form>
        </div>
      </div>}
    </>
  );
}
