"use client";

import { useState } from "react";
import Link from "next/link";
import { Check, CheckCircle, PencilSimple, Prohibit, WarningCircle } from "@phosphor-icons/react";
import { approveAdvisory, editAdvisory, rejectAdvisory } from "@/services/advisories";
import type { Advisory } from "@/types/api";
import { EvidenceChain } from "./evidence";
import { ApprovalStatus, ConfidenceIndicator, RiskBadge } from "./ui";

export function AdvisoryCard({ advisory }: { advisory: Advisory }) {
  return <article className="rounded-2xl border border-line bg-surface p-5 shadow-[0_12px_32px_rgba(28,52,39,0.04)]"><div className="flex flex-wrap items-start justify-between gap-3"><div><Link href={`/advisories/${advisory.advisory_id}`} className="font-mono text-sm font-semibold text-forest underline decoration-forest/25 underline-offset-4">{advisory.advisory_id}</Link><p className="mt-2 text-sm text-muted">Farm {advisory.farm_id}{advisory.crop ? ` · ${advisory.crop}` : ""}</p></div><ApprovalStatus status={advisory.status} /></div><div className="mt-5 flex flex-wrap items-center gap-3"><RiskBadge risk={advisory.risk_level} /><ConfidenceIndicator value={advisory.confidence} /></div><p className="mt-5 text-sm leading-6 text-foreground text-pretty">{advisory.recommendation}</p><div className="mt-5 flex items-center justify-between gap-3 border-t border-line pt-4 text-xs text-muted"><span>Evidence items: {advisory.evidence.length}</span><Link href={`/advisories/${advisory.advisory_id}`} className="font-semibold text-forest hover:underline">Review advisory</Link></div></article>;
}

export function ApprovalPanel({ advisory, onUpdated }: { advisory: Advisory; onUpdated: (advisory: Advisory) => void }) {
  const [mode, setMode] = useState<"view" | "edit" | "reject">("view");
  const [recommendation, setRecommendation] = useState(advisory.recommendation);
  const [reason, setReason] = useState("");
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const officer = "Mpho M.";

  async function act(action: "approve" | "edit" | "reject") {
    setWorking(true); setError(null);
    try {
      const updated = action === "approve" ? await approveAdvisory(advisory.advisory_id, officer) : action === "edit" ? await editAdvisory(advisory.advisory_id, officer, recommendation) : await rejectAdvisory(advisory.advisory_id, officer, reason || undefined);
      onUpdated(updated); setMode("view");
    } catch (actionError) { setError(actionError instanceof Error ? actionError.message : "The approval action could not be saved."); } finally { setWorking(false); }
  }

  const reviewable = advisory.status === "PENDING_APPROVAL" || advisory.status === "EDITED";
  return <div className="rounded-2xl border border-forest/20 bg-sage-soft/45 p-5"><div className="flex items-start gap-3"><CheckCircle size={23} weight="duotone" className="mt-0.5 shrink-0 text-forest" aria-hidden="true" /><div><p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-forest">Human approval gate</p><h2 className="mt-2 text-lg font-semibold text-foreground">{reviewable ? "Officer review is required" : `Status: ${advisory.status.replaceAll("_", " ")}`}</h2><p className="mt-2 text-sm leading-6 text-muted">{reviewable ? "This advisory is AI generated. It cannot be used with a farmer until a named officer approves it." : `Recorded officer: ${advisory.approving_officer ?? "Not recorded"}.`}</p></div></div>
    {reviewable && mode === "view" && <div className="mt-6 grid gap-3 sm:grid-cols-3"><button type="button" onClick={() => void act("approve")} disabled={working} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white disabled:opacity-60"><Check size={17} weight="bold" aria-hidden="true" /> Approve</button><button type="button" onClick={() => setMode("edit")} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-line bg-surface px-4 text-sm font-semibold text-foreground hover:bg-surface-muted"><PencilSimple size={17} aria-hidden="true" /> Edit</button><button type="button" onClick={() => setMode("reject")} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-risk-red/20 bg-surface px-4 text-sm font-semibold text-risk-red hover:bg-risk-red-soft"><Prohibit size={17} aria-hidden="true" /> Reject</button></div>}
    {reviewable && mode === "edit" && <div className="mt-6"><label htmlFor="advisory-edit" className="block text-sm font-semibold text-foreground">Edit recommendation</label><textarea id="advisory-edit" value={recommendation} onChange={(event) => setRecommendation(event.target.value)} rows={5} className="mt-2 w-full rounded-xl border border-line bg-surface p-3 text-sm leading-6 text-foreground" /><div className="mt-3 flex flex-wrap gap-3"><button type="button" onClick={() => void act("edit")} disabled={working || !recommendation.trim()} className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white disabled:opacity-60">Save edit <Check size={16} weight="bold" /></button><button type="button" onClick={() => setMode("view")} className="min-h-10 rounded-xl px-4 text-sm font-semibold text-muted hover:bg-surface-muted">Cancel</button></div></div>}
    {reviewable && mode === "reject" && <div className="mt-6"><label htmlFor="rejection-reason" className="block text-sm font-semibold text-foreground">Reason <span className="font-normal text-muted">optional</span></label><textarea id="rejection-reason" value={reason} onChange={(event) => setReason(event.target.value)} rows={4} placeholder="Record what should be revisited" className="mt-2 w-full rounded-xl border border-line bg-surface p-3 text-sm leading-6 text-foreground placeholder:text-muted" /><div className="mt-3 flex flex-wrap gap-3"><button type="button" onClick={() => void act("reject")} disabled={working} className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-risk-red px-4 text-sm font-semibold text-white disabled:opacity-60">Reject advisory <Prohibit size={16} /></button><button type="button" onClick={() => setMode("view")} className="min-h-10 rounded-xl px-4 text-sm font-semibold text-muted hover:bg-surface-muted">Cancel</button></div></div>}
    {error && <div className="mt-4 flex items-start gap-3 rounded-xl border border-risk-red/20 bg-risk-red-soft p-4 text-sm text-risk-red"><WarningCircle size={18} weight="duotone" className="mt-0.5 shrink-0" aria-hidden="true" />{error}</div>}
  </div>;
}

export function AdvisoryEvidence({ advisory }: { advisory: Advisory }) { return <EvidenceChain evidence={advisory.evidence} risk={advisory.risk_level} nextAction={advisory.recommendation} missingEvidence={advisory.missing_information} />; }
