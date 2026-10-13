export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "INSUFFICIENT_EVIDENCE";

export type AdvisoryStatus = "PENDING_APPROVAL" | "APPROVED" | "EDITED" | "REJECTED";

export interface BootstrapSummary {
  farms: number;
  climate_signals: number;
  pest_signals: number;
  advisory_records: number;
  tool_call_logs: number;
  districts: string[];
  crops: string[];
}

export interface EvidenceItem {
  id?: string;
  label: string;
  detail: string;
  source: string;
  observed_at?: string;
  confidence?: number;
  kind?: "climate" | "pest" | "plot" | "history" | "decision" | "missing" | "reference_context" | string;
}

export interface ClimateSignal {
  signal_id: string;
  district: string;
  agroclimatic_zone: string;
  signal_date: string;
  rainfall_mm_7d: number | null;
  forecast_rainfall_mm_7d: number | null;
  average_temperature_c: number | null;
  rainfall_anomaly_pct: number | null;
  drought_indicator: boolean | null;
  heavy_rain_indicator: boolean | null;
  availability_status: "AVAILABLE" | "STALE" | "UNAVAILABLE" | string;
  source_type: "LIVE" | "CACHED" | "SYNTHETIC" | string;
  freshness?: "FRESH" | "STALE" | "UNAVAILABLE" | string;
  source: string;
  observed_at: string;
  data_confidence: number;
  notes?: string | null;
}

export interface PestSignal {
  signal_id: string;
  district: string;
  agroclimatic_zone: string;
  crop: string;
  pest_type: string;
  report_count: number;
  severity: string;
  report_date: string;
  confidence: number;
  source: string;
  notes?: string | null;
}

export interface Farm {
  farm_id: string;
  household_id?: string;
  district: string;
  agroclimatic_zone: string;
  crop: string;
  crop_variety: string;
  planting_date: string | null;
  current_growth_stage: string | null;
  soil_type: string | null;
  previous_crop: string | null;
  previous_pest_incidents: Array<Record<string, unknown>>;
  previous_disease_incidents: Array<Record<string, unknown>>;
  previous_interventions: string[];
  field_size_ha: number;
  irrigation_type: string;
  last_inspection_date: string | null;
  data_quality_notes?: string | null;
  risk_level?: RiskLevel;
  confidence?: number | null;
  evidence_strength?: number | null;
  recommended_next_action?: string | null;
  risk_factors?: string[];
  supporting_evidence?: EvidenceItem[];
  missing_evidence?: string[];
  climate?: ClimateSignal | null;
  pest_signals?: PestSignal[];
  advisory_status?: AdvisoryStatus | null;
  last_analysed_at?: string | null;
  rank_reason?: string | null;
}

export interface Advisory {
  advisory_id: string;
  farm_id: string;
  farm?: Farm;
  crop?: string;
  risk_level: RiskLevel;
  recommendation: string;
  evidence: EvidenceItem[];
  missing_information: string[];
  confidence: number | null;
  created_at: string;
  status: AdvisoryStatus;
  reason?: string | null;
  actor?: string;
  approving_officer?: string | null;
  approval_timestamp?: string | null;
  edited_text?: string | null;
  rejection_reason?: string | null;
}

export interface ToolCall {
  id?: number;
  server_name?: string | null;
  tool_name: string;
  input_payload: Record<string, unknown>;
  output_payload: Record<string, unknown>;
  timestamp: string;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  output_summary?: string | null;
  status: "SUCCESS" | "FAILURE" | "PENDING" | string;
  action_type?: string | null;
  human_approval_required?: boolean;
}

export interface TraceEvent {
  id?: string;
  label: string;
  detail?: string;
  timestamp: string;
  status: "complete" | "active" | "blocked" | "failed" | string;
  tool_call?: ToolCall;
  decision_change?: DecisionChangeData;
}

export interface DecisionChangeData {
  from: RiskLevel;
  to: RiskLevel;
  reason: string;
  source: string;
  timestamp: string;
}

export interface TraceRun {
  workflow_run_id: string;
  request: string;
  started_at: string;
  completed_at?: string | null;
  status: "RUNNING" | "COMPLETE" | "FAILED" | string;
  events: TraceEvent[];
  tool_calls: ToolCall[];
  final_summary?: Record<string, unknown>;
}

export interface EvaluationResult {
  task_id: string;
  evaluation_run_id?: string | null;
  scenario: string;
  expected_behaviour: string;
  actual_behaviour: string;
  tools_called: string[];
  advisory_produced: boolean;
  evidence_used: string[];
  result: "PASS" | "FAIL" | "NOT_RUN" | string;
  run_id?: string | null;
  recorded_at?: string | null;
}

export interface AnalysisRequest {
  district?: string;
  crop?: string;
  analysis_start?: string;
  analysis_end?: string;
  scope: "all" | "farm" | "cluster";
  farm_id?: string;
}

export interface AnalysisRunResponse {
  workflow_run_id: string;
  status: string;
  message?: string;
}
