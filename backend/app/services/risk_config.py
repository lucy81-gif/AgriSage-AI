"""Risk thresholds and factor weights used by the deterministic assessment service."""

VULNERABLE_STAGES = {"emergence", "V2", "V3", "V4", "flowering", "fruiting"}
SEVERITY_POINTS = {"low": 6, "moderate": 15, "high": 28, "critical": 35}
MULTIPLE_REPORT_COUNT = 4
MULTIPLE_REPORT_BONUS = 8
RISK_THRESHOLDS = {"moderate": 25, "high": 55}
MAX_FRESH_CLIMATE_AGE_DAYS = 14
