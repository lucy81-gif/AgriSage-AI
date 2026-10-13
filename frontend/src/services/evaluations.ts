import { apiFetch } from "./api";
import type { EvaluationResult } from "@/types/api";

export function getEvaluations(): Promise<EvaluationResult[]> {
  return apiFetch<EvaluationResult[]>("/api/evaluations");
}
