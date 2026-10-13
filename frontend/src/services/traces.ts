import { apiFetch } from "./api";
import type { TraceRun } from "@/types/api";

export function getTraces(): Promise<TraceRun[]> {
  return apiFetch<TraceRun[]>("/api/traces");
}

export function getTrace(traceId: string): Promise<TraceRun> {
  return apiFetch<TraceRun>(`/api/traces/${encodeURIComponent(traceId)}`);
}
