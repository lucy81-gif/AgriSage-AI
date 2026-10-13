import Link from "next/link";
import { ArrowLeft, WarningCircle } from "@phosphor-icons/react/ssr";

export default function NotFound() {
  return <main className="flex min-h-screen items-center justify-center bg-background px-6 py-16"><div className="max-w-md text-center"><span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-soft text-amber"><WarningCircle size={28} weight="duotone" aria-hidden="true" /></span><p className="mt-6 font-mono text-xs font-semibold uppercase tracking-[0.18em] text-forest">Page not found</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">This evidence trail does not exist.</h1><p className="mt-3 text-sm leading-6 text-muted">The route may be incomplete or the record may no longer be available from the backend.</p><Link href="/" className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-xl bg-forest px-4 text-sm font-semibold text-white"><ArrowLeft size={16} aria-hidden="true" /> Return to overview</Link></div></main>;
}
