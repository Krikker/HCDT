from typing import Literal

from pydantic import BaseModel, Field


class Operator(BaseModel):
    id: str
    full_name: str
    role: str
    department: str
    skill_level: Literal["junior", "middle", "senior"]
    station_ids: list[str]
    grade: int = Field(ge=1, le=6)
    hourly_rate_rub: float = Field(ge=0)
    shift_start_trust_score: float = Field(ge=0, le=100)
    trust_score: float = Field(ge=0, le=100)
    fatigue_base: float = Field(ge=0, le=1)
    current_shift_hours: float = Field(ge=0, le=12)
    recent_errors: int = Field(ge=0)
    training_gap: float = Field(ge=0, le=1)


class Station(BaseModel):
    id: str
    name: str
    department: str
    segment: Literal["welding", "assembly", "paint", "quality", "logistics", "infrastructure"]
    line: str
    equipment: list[str]
    allowed_tools: list[str]
    process_steps: list[str]
    risk_zone: Literal["low", "medium", "high"]
    quality_cost_rub: int = Field(ge=0)


class SensorSnapshot(BaseModel):
    station_id: str
    tool_connected: str
    torque_ok: bool
    lighting_ok: bool
    noise_level: float = Field(ge=0)
    cycle_deviation_sec: int
    micro_pause_minutes: int = Field(ge=0)


class MesTask(BaseModel):
    operator_id: str
    station_id: str
    vin: str
    model_code: str
    current_step: str
    completed_steps: list[str]
    shift_type: Literal["day", "night"]


class ErpMotivation(BaseModel):
    operator_id: str
    bonus_plan_percent: float = Field(ge=0)
    discipline_weight: float = Field(ge=0, le=1)
    quality_weight: float = Field(ge=0, le=1)


class DigitalTrace(BaseModel):
    operator_id: str
    station_id: str
    shift_type: str
    current_step: str
    completed_steps: list[str]
    tool_connected: str
    trust_score: float
    fatigue_index: float
    attention_risk: float
    training_gap: float
    environment_risk: float
    cycle_drift: float
    predicted_next_step: str


class RegulationDecision(BaseModel):
    current_step_allowed: bool
    tool_allowed: bool
    next_allowed_steps: list[str]
    violation_reason: str | None


class RiskDecision(BaseModel):
    cognitive_risk_index: float = Field(ge=0, le=1)
    level: Literal["low", "medium", "high", "critical"]
    top_factors: list[str]
    breakdown: list[dict[str, str | float]]


class Recommendation(BaseModel):
    summary: str
    explanation: str
    actions: list[str]
    teaching_points: list[str]
    recommended_tool: str
    next_check_in_minutes: int = Field(ge=1)


class LearningState(BaseModel):
    trust_score: float = Field(ge=0, le=100)
    bonus_coefficient: float = Field(ge=0)
    growth_hint: str
    micro_lesson: str
    skill_progress_percent: float = Field(ge=0, le=100)
    shift_trust_delta: float = 0


class PayrollState(BaseModel):
    earned_so_far_rub: float = Field(ge=0)
    projected_shift_total_rub: float = Field(ge=0)
    quality_bonus_rub: float
    risk_penalty_rub: float
    incident_penalty_rub: float
    mentor_bonus_rub: float
    explanation: str


class WorkflowStep(BaseModel):
    code: str
    title: str
    status: Literal["done", "current", "next", "blocked"]
    instruction: str
    requirement: str
    worker_state: str
    check_item: str
    required_tool: str


class WorkflowState(BaseModel):
    station_label: str
    current_step_title: str
    next_step_title: str
    completion_percent: float = Field(ge=0, le=100)
    steps: list[WorkflowStep]
    cycle_number: int = Field(ge=1)


class AccessDecision(BaseModel):
    allowed: bool
    message: str
    suggested_stations: list[str]


class InteractionState(BaseModel):
    selected_tool: str
    required_tool: str
    completion_ready: bool
    hint: str
    progress_message: str
    available_incidents: list[dict[str, str]]


class ToolSelectionRequest(BaseModel):
    tool_name: str


class ActionResult(BaseModel):
    success: bool
    message: str


class IncidentEvent(BaseModel):
    event_id: str
    title: str
    incident_code: str
    severity: Literal["warning", "incident", "defect", "critical", "recovery"]
    source: str
    description: str
    trust_delta: float
    payroll_delta_rub: float
    step_code: str


class AnalyticsState(BaseModel):
    cycle_count: int = Field(ge=0)
    total_incidents: int = Field(ge=0)
    critical_incidents: int = Field(ge=0)
    recovery_actions: int = Field(ge=0)
    top_incident: str


class ShiftSummary(BaseModel):
    operator_id: str
    operator_name: str
    station_id: str
    station_name: str
    cycle_count: int = Field(ge=0)
    total_incidents: int = Field(ge=0)
    critical_incidents: int = Field(ge=0)
    recovery_actions: int = Field(ge=0)
    trust_delta: float
    projected_shift_total_rub: float
    incident_penalty_rub: float
    kind_feedback: str
    csv_download_url: str


class TwinEvaluation(BaseModel):
    operator: Operator
    station: Station
    mes_task: MesTask
    sensor_snapshot: SensorSnapshot
    digital_trace: DigitalTrace
    regulation: RegulationDecision
    risk: RiskDecision
    recommendation: Recommendation
    learning: LearningState
    payroll: PayrollState
    workflow: WorkflowState
    access: AccessDecision
    interaction: InteractionState
    event_log: list[IncidentEvent]
    analytics: AnalyticsState
