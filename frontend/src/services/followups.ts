import { apiFetch } from "./api";

export interface FollowUpTask {
  id: number;
  farm_id: string;
  workflow_run_id: string | null;
  reason: string;
  priority: string;
  status: string;
  created_at: string;
  completed_at?: string | null;
}

export function createFollowUp(farmId: string, reason: string, priority = "HIGH"): Promise<FollowUpTask> {
  return apiFetch<FollowUpTask>("/api/follow-ups", {
    method: "POST",
    body: JSON.stringify({ farm_id: farmId, reason, priority }),
  });
}
