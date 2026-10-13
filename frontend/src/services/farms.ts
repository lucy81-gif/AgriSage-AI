import { apiFetch } from "./api";
import type { BootstrapSummary, Farm } from "@/types/api";

export function getBootstrapSummary(): Promise<BootstrapSummary> {
  return apiFetch<BootstrapSummary>("/api/v1/bootstrap-summary");
}

export function getFarms(): Promise<Farm[]> {
  return apiFetch<Farm[]>("/api/farms");
}

export function getFarm(farmId: string): Promise<Farm> {
  return apiFetch<Farm>(`/api/farms/${encodeURIComponent(farmId)}`);
}
