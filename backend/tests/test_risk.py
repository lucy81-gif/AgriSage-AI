from backend.app.services.risk import assess_farm


def _plot(**overrides):
    value = {
        "farm_id": "F-TEST",
        "crop": "maize",
        "planting_date": "2026-08-01",
        "growth_stage": "V4",
        "soil_type": "loam",
        "irrigation_type": "rainfed",
        "previous_pest_incidents": [],
        "data_quality_notes": "Complete plot record.",
    }
    value.update(overrides)
    return value


def test_drought_and_pest_evidence_raise_structured_risk_without_guessing():
    result = assess_farm(
        _plot(),
        {
            "availability_status": "AVAILABLE",
            "signals": [{
                "rainfall_anomaly_pct": -72,
                "drought_indicator": True,
                "heavy_rain_indicator": False,
                "data_confidence": 0.96,
                "signal_date": "2026-10-01",
            }],
        },
        {"signals": [{"pest_type": "fall armyworm", "severity": "HIGH", "report_count": 5, "confidence": 0.9}]},
    )

    assert result["risk_level"] == "HIGH"
    assert any("drought" in factor for factor in result["risk_factors"])
    assert any(item["source"] == "get_climate_signals" for item in result["evidence_chain"])


def test_missing_climate_is_insufficient_evidence():
    result = assess_farm(_plot(), {"availability_status": "UNAVAILABLE", "signals": []}, {"signals": []})

    assert result["risk_level"] == "INSUFFICIENT_EVIDENCE"
    assert any("Climate data" in item for item in result["missing_evidence"])


def test_stale_climate_is_not_used_as_current_rainfall_evidence():
    result = assess_farm(
        _plot(),
        {
            "availability_status": "STALE",
            "signals": [{
                "availability_status": "STALE",
                "freshness": "STALE",
                "rainfall_anomaly_pct": -80,
                "drought_indicator": True,
                "heavy_rain_indicator": False,
                "data_confidence": 0.4,
                "signal_date": "2026-08-01",
            }],
        },
        {"signals": []},
    )
    assert any("stale climate evidence" in factor for factor in result["risk_factors"])
    assert not any("drought indicator" in factor for factor in result["risk_factors"])
