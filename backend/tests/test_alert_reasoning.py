from pipeline.alert_reasoning import explain_alert


def test_reasoning_explains_danger_zone_entry_without_inferring_intent():
    result = explain_alert({
        "activity": "IN_DANGER_ZONE",
        "currently_in_track_zone": True,
        "ever_entered_track_zone": True,
        "frames_in_track_zone": 12,
        "duration_tracked_s": 4.5,
    })

    assert result["mode"] == "rule_based"
    assert "entered the calibrated danger zone" in result["summary"]
    assert any(item["signal"] == "frames_in_track_zone" for item in result["evidence"])
    assert "does not determine intent" in result["limitations"]


def test_reasoning_has_fallback_for_missing_signals():
    result = explain_alert({"activity": "UNKNOWN"})

    assert result["evidence"][0]["signal"] == "activity"
    assert result["mode"] == "rule_based"


def test_reasoning_uses_rule_based_fallback_without_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = explain_alert({"activity": "ERRATIC_MOVEMENT", "direction_reversals": 3})

    assert result["mode"] == "rule_based"
    assert result["evidence"][0]["signal"] == "direction_reversals"