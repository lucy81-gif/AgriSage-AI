from __future__ import annotations

from typing import Any

from backend.app.services.risk_config import (
    MULTIPLE_REPORT_BONUS,
    MULTIPLE_REPORT_COUNT,
    RISK_THRESHOLDS,
    SEVERITY_POINTS,
    VULNERABLE_STAGES,
)


def _evidence(label: str, detail: str, source: str, confidence: float, kind: str) -> dict[str, Any]:
    return {
        "label": label,
        "detail": detail,
        "source": source,
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
        "kind": kind,
    }


def assess_farm(
    plot: dict[str, Any], climate: dict[str, Any], pests: dict[str, Any]
) -> dict[str, Any]:
    score = 0
    factors: list[str] = []
    missing: list[str] = []
    evidence: list[dict[str, Any]] = []
    climate_rows = climate.get("signals", [])
    climate_row = climate_rows[0] if climate_rows else None
    pest_rows = pests.get("signals", [])

    if not plot.get("planting_date"):
        missing.append("Planting date is missing; crop timing cannot be checked.")
    if not plot.get("growth_stage"):
        missing.append("Current growth stage is missing.")
    if not plot.get("soil_type"):
        missing.append("Soil type is missing; water-retention interpretation is limited.")

    quality_notes = (plot.get("data_quality_notes") or "").lower()
    has_stage_conflict = "conflict" in quality_notes
    if has_stage_conflict:
        missing.append("Growth stage is conflicting across farm records.")
        factors.append("conflicting growth-stage records")
        evidence.append(
            _evidence(
                "Conflicting plot record",
                "The farm record flags conflicting growth-stage entries; confirm the stage in the field.",
                "get_plot_context",
                1.0,
                "missing",
            )
        )

    if not climate_row or climate.get("availability_status") == "UNAVAILABLE":
        missing.append("Climate data is unavailable for this district and zone.")
    elif (
        climate_row.get("availability_status") == "STALE"
        or climate_row.get("freshness") == "STALE"
    ):
        missing.append("The latest climate signal is stale for the selected analysis period.")
        factors.append("stale climate evidence")
        evidence.append(
            _evidence(
                "Stale climate signal",
                f"The latest climate observation is dated {climate_row.get('signal_date')} and should be refreshed.",
                "get_climate_signals",
                climate_row.get("data_confidence", 0.5),
                "climate",
            )
        )
    else:
        anomaly = climate_row.get("rainfall_anomaly_pct")
        if anomaly is not None and anomaly <= -30:
            score += 18
            factors.append(f"rainfall anomaly {anomaly:.0f}% below expected")
            evidence.append(
                _evidence(
                    "Below-normal rainfall",
                    f"Rainfall is {abs(anomaly):.0f}% below the expected range.",
                    "get_climate_signals",
                    climate_row.get("data_confidence", 0.0),
                    "climate",
                )
            )
        if climate_row.get("drought_indicator"):
            score += 24 if plot.get("irrigation_type") == "rainfed" else 12
            factors.append("drought indicator on a rainfed plot" if plot.get("irrigation_type") == "rainfed" else "drought indicator")
            evidence.append(
                _evidence(
                    "Drought signal",
                    "The climate feed flags drought conditions; irrigation status changes exposure.",
                    "get_climate_signals",
                    climate_row.get("data_confidence", 0.0),
                    "climate",
                )
            )
        if climate_row.get("heavy_rain_indicator"):
            score += 22
            factors.append("heavy-rain indicator")
            evidence.append(
                _evidence(
                    "Heavy-rain signal",
                    "Observed or forecast rainfall is above the local baseline; inspect drainage and erosion exposure.",
                    "get_climate_signals",
                    climate_row.get("data_confidence", 0.0),
                    "climate",
                )
            )

    if plot.get("growth_stage") in VULNERABLE_STAGES:
        score += 10
        factors.append(f"vulnerable crop stage ({plot['growth_stage']})")
        evidence.append(
            _evidence(
                "Vulnerable crop stage",
                f"The plot is recorded at {plot['growth_stage']}, which warrants closer inspection under weather stress.",
                "get_plot_context",
                1.0,
                "plot",
            )
        )

    for pest in pest_rows:
        pest_points = SEVERITY_POINTS.get(str(pest.get("severity", "")).lower(), 0)
        if pest_points:
            score += pest_points
            if pest.get("report_count", 0) >= MULTIPLE_REPORT_COUNT:
                score += MULTIPLE_REPORT_BONUS
            factors.append(f"{pest['severity']} {pest['pest_type']} signal ({pest['report_count']} reports)")
            evidence.append(
                _evidence(
                    "Recent pest signal",
                    f"{pest['report_count']} reports of {pest['pest_type']} at {pest['severity']} severity were recorded in the zone.",
                    "get_pest_signals",
                    pest.get("confidence", 0.0),
                    "pest",
                )
            )

    historical_pests = plot.get("previous_pest_incidents") or []
    high_history = any(str(item.get("severity", "")).lower() == "high" for item in historical_pests if isinstance(item, dict))
    if high_history:
        score += 8
        factors.append("high-severity pest history")
        evidence.append(
            _evidence(
                "Historical pest risk",
                "The plot has a prior high-severity pest incident; current confirmation is still required.",
                "get_plot_context",
                1.0,
                "history",
            )
        )

    core_missing = len(missing)
    unavailable_climate = not climate_row or climate.get("availability_status") == "UNAVAILABLE"
    conflict = has_stage_conflict
    if unavailable_climate or core_missing >= 3 or (conflict and core_missing >= 2):
        level = "INSUFFICIENT_EVIDENCE"
    elif score >= RISK_THRESHOLDS["high"]:
        level = "HIGH"
    elif score >= RISK_THRESHOLDS["moderate"]:
        level = "MODERATE"
    else:
        level = "LOW"

    confidence_values = [item.get("confidence", 1.0) for item in evidence if item.get("confidence") is not None]
    confidence = min(confidence_values, default=0.45)
    if missing:
        confidence -= min(0.3, 0.06 * len(missing))
    confidence = round(max(0.2, min(0.98, confidence)), 2)
    evidence_strength = round(max(0.0, min(1.0, len(evidence) / 5)), 2)

    if level == "INSUFFICIENT_EVIDENCE":
        next_action = "Create a follow-up task to verify missing or conflicting evidence before advising."
    elif level == "HIGH":
        next_action = "Inspect within 48 hours and verify field symptoms before any treatment decision."
    elif level == "MODERATE":
        next_action = "Schedule a field check and monitor the next climate and pest update."
    else:
        next_action = "Continue routine monitoring and record the next inspection."

    return {
        "risk_level": level,
        "score": score,
        "confidence": confidence,
        "evidence_strength": evidence_strength,
        "risk_factors": factors,
        "missing_evidence": missing,
        "recommended_next_action": next_action,
        "evidence_chain": evidence,
    }
