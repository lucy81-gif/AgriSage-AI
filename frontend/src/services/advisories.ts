import { apiFetch } from "./api";
import type { Advisory } from "@/types/api";

export function getAdvisories(): Promise<Advisory[]> {
  return apiFetch<Advisory[]>("/api/advisories");
}

export function getAdvisory(advisoryId: string): Promise<Advisory> {
  return apiFetch<Advisory>(`/api/advisories/${encodeURIComponent(advisoryId)}`);
}

export function approveAdvisory(advisoryId: string, officer: string): Promise<Advisory> {
  return apiFetch<Advisory>(`/api/advisories/${encodeURIComponent(advisoryId)}/approve`, {
    method: "POST",
    body: JSON.stringify({ officer_name: officer }),
  });
}

export function editAdvisory(
  advisoryId: string,
  officer: string,
  recommendation: string,
): Promise<Advisory> {
  return apiFetch<Advisory>(`/api/advisories/${encodeURIComponent(advisoryId)}/edit`, {
    method: "POST",
    body: JSON.stringify({ officer_name: officer, recommendation }),
  });
}

export function rejectAdvisory(
  advisoryId: string,
  officer: string,
  reason?: string,
): Promise<Advisory> {
  return apiFetch<Advisory>(`/api/advisories/${encodeURIComponent(advisoryId)}/reject`, {
    method: "POST",
    body: JSON.stringify({ officer_name: officer, rejection_reason: reason }),
  });
}
