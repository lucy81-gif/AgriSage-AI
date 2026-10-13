"use client";

import type { ReactNode } from "react";
import { ArrowUpRight, CheckCircle, Circle, WarningCircle } from "@phosphor-icons/react";
import type { RiskLevel } from "@/types/api";

const riskStyles: Record<RiskLevel, { label: string; className: string }> = {
  LOW: { label: "Low", className: "bg-sage-soft text-forest" },
  MODERATE: { label: "Moderate", className: "bg-amber-soft text-amber" },
  HIGH: { label: "High", className: "bg-risk-red-soft text-risk-red" },
  INSUFFICIENT_EVIDENCE: {
    label: "Insufficient evidence",
    className: "bg-surface-muted text-muted",
  },
};

export function RiskBadge({ risk }: { risk?: RiskLevel | null }) {
  if (!risk) {
    return <span className="rounded-full bg-surface-muted px-3 py-1 text-xs font-semibold text-muted">Unavailable</span>;
  }

  const style = riskStyles[risk] ?? riskStyles.INSUFFICIENT_EVIDENCE;
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${style.className}`}>
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
      <span>{style.label}</span>
    </span>
  );
}

export function ConfidenceIndicator({ value }: { value?: number | null }) {
  if (value === null || value === undefined) {
    return <span className="text-sm text-muted">Confidence unavailable</span>;
  }

  const percentage = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <span className="inline-flex min-w-32 items-center gap-3 text-sm text-muted">
      <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-muted" aria-hidden="true">
        <span className="block h-full rounded-full bg-forest" style={{ width: `${percentage}%` }} />
      </span>
      <span className="font-mono text-xs font-semibold text-foreground">{percentage}%</span>
    </span>
  );
}

export function StatCard({
  label,
  value,
  meta,
  icon,
  tone = "default",
}: {
  label: string;
  value: string | number;
  meta: string;
  icon: ReactNode;
  tone?: "default" | "danger" | "warning" | "muted";
}) {
  const toneClass = {
    default: "bg-sage-soft text-forest",
    danger: "bg-risk-red-soft text-risk-red",
    warning: "bg-amber-soft text-amber",
    muted: "bg-surface-muted text-muted",
  }[tone];

  return (
    <article className="rounded-2xl border border-line bg-surface p-5 shadow-[0_12px_32px_rgba(28,52,39,0.04)]">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm font-medium text-muted">{label}</p>
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${toneClass}`} aria-hidden="true">
          {icon}
        </span>
      </div>
      <p className="mt-5 font-mono text-3xl font-semibold tracking-tight text-foreground">{value}</p>
      <p className="mt-2 text-xs leading-5 text-muted">{meta}</p>
    </article>
  );
}

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-line bg-surface p-5 shadow-[0_12px_32px_rgba(28,52,39,0.04)] ${className}`}>{children}</section>;
}

export function SectionHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-forest">{eyebrow}</p>}
        <h2 className="mt-1 text-xl font-semibold tracking-tight text-foreground text-balance">{title}</h2>
        {description && <p className="mt-1 max-w-2xl text-sm leading-6 text-muted text-pretty">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded-xl border border-dashed border-line-strong bg-surface-muted/40 px-6 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-surface text-forest shadow-sm" aria-hidden="true">
        {icon ?? <Circle size={20} weight="duotone" />}
      </span>
      <h3 className="mt-4 text-base font-semibold text-foreground text-balance">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-muted text-pretty">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function DataUnavailable({
  title = "Backend data is not available",
  description = "This view is connected to the live API and will populate when its endpoint is available.",
  endpoint,
  onRetry,
}: {
  title?: string;
  description?: string;
  endpoint: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-2xl border border-amber/30 bg-amber-soft/50 p-6">
      <div className="flex items-start gap-3">
        <WarningCircle size={22} weight="duotone" className="mt-0.5 shrink-0 text-amber" aria-hidden="true" />
        <div>
          <h3 className="text-base font-semibold text-foreground">{title}</h3>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-muted">{description}</p>
          <p className="mt-3 font-mono text-xs text-amber">Expected endpoint: {endpoint}</p>
          {onRetry && (
            <button type="button" onClick={onRetry} className="mt-5 inline-flex min-h-10 items-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-y-0.5 active:translate-y-px">
              Retry connection <ArrowUpRight size={16} weight="bold" aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function ButtonLink({ children, href }: { children: ReactNode; href: string }) {
  return (
    <a href={href} className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-y-0.5 active:translate-y-px">
      {children}
      <ArrowUpRight size={16} weight="bold" aria-hidden="true" />
    </a>
  );
}

export function StatusDot({ status }: { status: "success" | "warning" | "neutral" | "danger" }) {
  const classes = {
    success: "bg-forest text-forest",
    warning: "bg-amber text-amber",
    neutral: "bg-muted text-muted",
    danger: "bg-risk-red text-risk-red",
  }[status];

  return <span className={`inline-flex h-2 w-2 rounded-full ${classes}`} aria-hidden="true" />;
}

export function ApprovalStatus({ status }: { status: string }) {
  const map: Record<string, { label: string; className: string; icon: ReactNode }> = {
    PENDING_APPROVAL: { label: "Pending approval", className: "bg-amber-soft text-amber", icon: <Circle size={14} /> },
    APPROVED: { label: "Approved", className: "bg-sage-soft text-forest", icon: <CheckCircle size={14} weight="fill" /> },
    EDITED: { label: "Edited", className: "bg-blue-soft text-blue", icon: <CheckCircle size={14} /> },
    REJECTED: { label: "Rejected", className: "bg-risk-red-soft text-risk-red", icon: <WarningCircle size={14} /> },
  };
  const current = map[status] ?? { label: status, className: "bg-surface-muted text-muted", icon: <Circle size={14} /> };
  return <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${current.className}`}>{current.icon}{current.label}</span>;
}
