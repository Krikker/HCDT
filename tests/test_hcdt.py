from app.services.twin_service import TwinService


def test_door_station_produces_proactive_warning():
    service = TwinService()
    result = service.evaluate("op-101", "st-door")

    assert result.risk.level in {"high", "critical"}
    assert result.regulation.tool_allowed is False
    assert result.regulation.violation_reason
    assert result.access.allowed is True


def test_quality_station_remains_more_stable():
    service = TwinService()
    result = service.evaluate("op-202", "st-qc")

    assert result.risk.level in {"low", "medium"}
    assert result.learning.trust_score >= 90
    assert result.payroll.risk_penalty_rub > 0
    assert result.interaction.required_tool


def test_wrong_department_is_blocked():
    service = TwinService()
    safe = service.evaluate("op-202", "st-qc")
    result = service.evaluate("op-202", "st-engine")

    assert result.access.allowed is False
    assert len(result.access.suggested_stations) > 0
    assert result.learning.trust_score < safe.learning.trust_score
    assert result.risk.cognitive_risk_index > safe.risk.cognitive_risk_index


def test_step_completion_requires_correct_tool():
    service = TwinService()
    bad = service.complete_current_step("op-101", "st-engine")
    assert bad.success is False

    tool = service.set_selected_tool("op-101", "st-engine", "torque-wrench")
    assert tool.success is True

    done = service.complete_current_step("op-101", "st-engine")
    assert done.success is True


def test_incident_changes_trust_and_event_log():
    service = TwinService()
    before = service.evaluate("op-101", "st-engine")
    response = service.register_incident("op-101", "st-engine", "otk_return")
    after = service.evaluate("op-101", "st-engine")

    assert response.success is True
    assert len(after.event_log) == len(before.event_log) + 1
    assert after.learning.trust_score < before.learning.trust_score
    assert after.payroll.incident_penalty_rub < 0


def test_cycle_restarts_after_last_step():
    service = TwinService()
    service.set_selected_tool("op-202", "st-qc", "scanner")
    service.complete_current_step("op-202", "st-qc")
    service.set_selected_tool("op-202", "st-qc", "camera-rig")
    service.complete_current_step("op-202", "st-qc")
    service.set_selected_tool("op-202", "st-qc", "tablet")
    result = service.complete_current_step("op-202", "st-qc")
    refreshed = service.evaluate("op-202", "st-qc")

    assert result.success is True
    assert "перезапущен" in result.message.lower()
    assert "VIN" in refreshed.workflow.current_step_title
    assert refreshed.analytics.cycle_count >= 1


def test_close_shift_returns_summary_and_resets_state():
    service = TwinService()
    service.register_incident("op-101", "st-engine", "wrong_tool")

    summary = service.close_shift("op-101", "st-engine")
    refreshed = service.evaluate("op-101", "st-engine")

    assert summary.operator_id == "op-101"
    assert summary.station_id == "st-engine"
    assert isinstance(summary.kind_feedback, str) and summary.kind_feedback
    assert summary.csv_download_url.endswith("/api/session/op-101/st-engine/report.csv")
    assert len(refreshed.event_log) == 0
    assert refreshed.workflow.completion_percent == 0


def test_shift_csv_contains_header_and_events():
    service = TwinService()
    service.register_incident("op-101", "st-engine", "otk_return")

    csv_report = service.build_shift_report_csv("op-101", "st-engine")

    assert "operator_id,op-101" in csv_report
    assert "event_id,severity,incident_code,title,step_code,trust_delta,payroll_delta_rub,description" in csv_report
    assert "otk_return" in csv_report


def test_csv_after_close_shift_uses_snapshot_not_reset_state():
    service = TwinService()
    service.set_selected_tool("op-202", "st-qc", "scanner")
    service.complete_current_step("op-202", "st-qc")
    service.set_selected_tool("op-202", "st-qc", "gap-gauge")
    service.complete_current_step("op-202", "st-qc")
    service.set_selected_tool("op-202", "st-qc", "scanner")
    service.complete_current_step("op-202", "st-qc")
    service.set_selected_tool("op-202", "st-qc", "camera-rig")
    service.complete_current_step("op-202", "st-qc")
    service.set_selected_tool("op-202", "st-qc", "tablet")
    service.complete_current_step("op-202", "st-qc")

    summary = service.close_shift("op-202", "st-qc")
    csv_report = service.build_shift_report_csv("op-202", "st-qc")

    assert summary.cycle_count >= 1
    assert f"cycles_completed,{summary.cycle_count}" in csv_report
