"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  ChartLineUp,
  ClipboardText,
  Gear,
  House,
  List,
  MagnifyingGlass,
  MapPinLine,
  Pulse,
  Queue,
  ShieldCheck,
  X,
} from "@phosphor-icons/react";

const primaryNavigation = [
  { label: "Overview", href: "/", icon: House },
  { label: "Farms", href: "/farms", icon: MapPinLine },
  { label: "Priority queue", href: "/priority-queue", icon: Queue },
  { label: "Advisories", href: "/advisories", icon: ClipboardText },
  { label: "Agent trace", href: "/trace", icon: Pulse },
  { label: "Evaluations", href: "/evaluations", icon: ChartLineUp },
];

const pageTitles: Record<string, string> = {
  "/": "Overview",
  "/farms": "Farms",
  "/priority-queue": "Priority queue",
  "/advisories": "Advisories",
  "/trace": "Agent trace",
  "/evaluations": "Evaluations",
  "/settings": "Settings",
};

function Navigation({ onNavigate }: { onNavigate: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary navigation" className="flex flex-1 flex-col">
      <div className="space-y-1">
        {primaryNavigation.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={`group flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition-colors duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] ${active ? "bg-white/12 text-white" : "text-sage hover:bg-white/8 hover:text-white"}`}
            >
              <Icon size={19} weight={active ? "fill" : "regular"} aria-hidden="true" />
              <span>{item.label}</span>
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-sage" aria-hidden="true" />}
            </Link>
          );
        })}
      </div>

      <div className="mt-auto space-y-1 border-t border-white/12 pt-5">
        <Link href="/settings" onClick={onNavigate} className="flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium text-sage transition-colors duration-300 hover:bg-white/8 hover:text-white">
          <Gear size={19} weight="regular" aria-hidden="true" />
          Settings
        </Link>
      </div>
    </nav>
  );
}

function Sidebar({ mobile = false, onClose = () => undefined }: { mobile?: boolean; onClose?: () => void }) {
  return (
    <aside className={`${mobile ? "flex" : "hidden md:flex"} fixed inset-y-0 left-0 z-40 w-72 flex-col bg-forest-deep px-5 py-6 text-white`}>
      <div className="flex items-center justify-between px-2">
        <Link href="/" onClick={onClose} className="flex items-center gap-3" aria-label="AgriSage AI overview">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-sage font-mono text-lg font-bold text-forest-deep">A</span>
          <span>
            <span className="block text-sm font-semibold tracking-wide text-white">AgriSage AI</span>
            <span className="mt-0.5 block font-mono text-xs uppercase tracking-[0.18em] text-sage">Evidence first</span>
          </span>
        </Link>
        {mobile && <button type="button" onClick={onClose} aria-label="Close navigation" className="flex h-10 w-10 items-center justify-center rounded-xl text-sage hover:bg-white/8 hover:text-white"><X size={20} /></button>}
      </div>

      <div className="mt-10 mb-4 px-3 font-mono text-xs font-semibold uppercase tracking-[0.2em] text-sage/70">Workspace</div>
      <Navigation onNavigate={onClose} />

      <div className="mt-8 rounded-2xl border border-white/12 bg-white/6 p-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-white"><ShieldCheck size={16} weight="duotone" className="text-sage" /> Human approval gate</div>
        <p className="mt-2 text-xs leading-5 text-sage">Every advisory stops here before it can be used with a farmer.</p>
      </div>
    </aside>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const title = Object.entries(pageTitles).find(([path]) => path !== "/" && pathname.startsWith(path))?.[1] ?? pageTitles[pathname] ?? "Overview";

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      {mobileOpen && <><button type="button" aria-label="Close navigation overlay" onClick={() => setMobileOpen(false)} className="fixed inset-0 z-30 bg-forest-deep/50 md:hidden" /><Sidebar mobile onClose={() => setMobileOpen(false)} /></>}
      <div className="min-h-screen md:pl-72">
        <header className="sticky top-0 z-20 border-b border-line bg-background/95 backdrop-blur">
          <div className="flex min-h-20 items-center justify-between gap-4 px-5 py-3 sm:px-8 lg:px-10">
            <div className="flex items-center gap-3">
              <button type="button" onClick={() => setMobileOpen(true)} aria-label="Open navigation" className="flex h-11 w-11 items-center justify-center rounded-xl border border-line bg-surface text-forest md:hidden"><List size={21} /></button>
              <div>
                <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-muted">Extension office / Lesotho</p>
                <h1 className="mt-1 text-xl font-semibold tracking-tight text-foreground">{title}</h1>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              <Link href="/farms" className="hidden items-center gap-2 rounded-xl border border-line bg-surface px-3 text-sm text-muted transition-colors duration-300 hover:text-forest lg:flex" aria-label="Search farms">
                <MagnifyingGlass size={16} aria-hidden="true" />
                <span className="h-10 w-32 py-2.5 text-sm text-foreground">Search farms</span>
                <kbd className="rounded-md bg-surface-muted px-1.5 py-0.5 font-mono text-xs text-muted">/</kbd>
              </Link>
              <Link href="/advisories" aria-label="View advisory notifications" className="relative flex h-11 w-11 items-center justify-center rounded-xl border border-line bg-surface text-muted transition-colors duration-300 hover:text-forest">
                <Bell size={19} aria-hidden="true" />
                <span className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-amber" aria-label="Unread notification" />
              </Link>
              <div className="hidden items-center gap-3 border-l border-line pl-3 sm:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-forest font-mono text-xs font-semibold text-sage">MM</div>
                <div className="hidden xl:block">
                  <p className="text-sm font-semibold text-foreground">Mpho M.</p>
                  <p className="text-xs text-muted">Extension officer</p>
                </div>
              </div>
            </div>
          </div>
        </header>
        <main id="main-content" className="px-5 py-8 sm:px-8 lg:px-10">{children}</main>
        <footer className="border-t border-line px-5 py-6 sm:px-8 lg:px-10">
          <div className="flex flex-col gap-2 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
            <span>AgriSage AI · Evidence before advice</span>
            <span className="flex flex-wrap items-center gap-3"><span>All records shown by the workspace must come from the advisory API.</span><Link href="/privacy" className="font-semibold text-forest hover:underline">Privacy</Link><Link href="/terms" className="font-semibold text-forest hover:underline">Terms</Link></span>
          </div>
        </footer>
      </div>
    </div>
  );
}
