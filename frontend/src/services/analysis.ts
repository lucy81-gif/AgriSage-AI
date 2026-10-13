import { apiFetch } from "./api";
import type { AnalysisRequest, AnalysisRunResponse } from "@/types/api";

export function runAnalysis(request: AnalysisRequest): Promise<AnalysisRunResponse> {
  return apiFetch<AnalysisRunResponse>("/api/analysis/run", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
