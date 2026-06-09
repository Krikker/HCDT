import json
from datetime import datetime
from io import StringIO
from copy import deepcopy
from pathlib import Path
import csv

from app.config import DATA_DIR
from app.integrations.erp_adapter import ERPAdapter
from app.integrations.mes_adapter import MESAdapter
from app.integrations.scada_adapter import SCADAAdapter
from app.models import (
    AccessDecision,
    ActionResult,
    AnalyticsState,
    IncidentEvent,
    InteractionState,
    Operator,
    ShiftSummary,
    Station,
    TwinEvaluation,
    WorkflowState,
    WorkflowStep,
)
from app.services.digital_trace import DigitalTraceService
from app.services.payroll_engine import PayrollEngine
from app.services.recommendation_engine import RecommendationEngine
from app.services.regulation_engine import RegulationEngine
from app.services.reputation_engine import ReputationEngine
from app.services.risk_engine import RiskEngine
from app.tool_catalog import tool_label


class TwinService:
    def __init__(self) -> None:
        self.mes = MESAdapter()
        self.scada = SCADAAdapter()
        self.erp = ERPAdapter()
        self.trace_service = DigitalTraceService()
        self.regulation_engine = RegulationEngine()
        self.risk_engine = RiskEngine()
        self.recommendation_engine = RecommendationEngine()
        self.reputation_engine = ReputationEngine()
        self.payroll_engine = PayrollEngine()
        self.runtime_state: dict[str, dict[str, object]] = {}
        self.event_seq = 0
        self.operators = self._load_json(DATA_DIR / "operators.json", Operator)
        self.stations = self._load_json(DATA_DIR / "stations.json", Station)

    @staticmethod
    def _load_json(path: Path, model_class):
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {item["id"]: model_class(**item) for item in payload}

    def list_operators(self) -> list[Operator]:
        return list(self.operators.values())

    def list_stations(self) -> list[Station]:
        return list(self.stations.values())

    @staticmethod
    def _key(operator_id: str, station_id: str) -> str:
        return f"{operator_id}:{station_id}"

    @staticmethod
    def _step_title(step_code: str) -> str:
        step_titles = {
            "identify-body": "Идентификация кузова",
            "load-welding-program": "Загрузка программы сварки",
            "verify-clamps": "Проверка прижимов",
            "run-weld-cycle": "Запуск сварочного цикла",
            "measure-seam": "Контроль шва",
            "identify-engine": "Идентификация двигателя",
            "mount-block": "Установка блока",
            "tighten-head-bolts": "Затяжка болтов ГБЦ",
            "check-torque-curve": "Проверка кривой момента",
            "close-operation": "Закрытие операции",
            "identify-vin": "Идентификация VIN",
            "mount-door": "Установка двери",
            "tighten-bolts": "Затяжка крепежа",
            "scan-checkpoint": "Сканирование контрольной точки",
            "visual-inspection": "Визуальный контроль",
            "check-gaps": "Проверка зазоров",
            "check-torque-mark": "Проверка метки момента",
            "photo-fixation": "Фотофиксация",
            "release-car": "Разрешение на выпуск",
            "prepare-surface": "Подготовка поверхности",
            "set-paint-mode": "Выбор режима покраски",
            "spray-layer": "Нанесение слоя",
            "measure-thickness": "Контроль толщины",
            "read-route-task": "Чтение маршрутного задания",
            "scan-cell": "Сканирование ячейки",
            "pick-parts": "Отбор деталей",
            "verify-kit": "Проверка комплекта",
            "deliver-kit": "Подача комплекта на линию",
        }
        return step_titles.get(step_code, step_code.replace("-", " ").replace("_", " ").capitalize())

    @staticmethod
    def _step_profiles() -> dict[str, tuple[str, str, str, str]]:
        return {
            "identify-body": ("Считать идентификатор кузова и привязать его к посту.", "Кузов считан и маршрут получен.", "VIN кузова считан без ошибки.", "scanner"),
            "load-welding-program": ("Выбрать программу сварки под модификацию кузова.", "Программа сварки выбрана на пульте.", "Номер программы совпадает с моделью.", "welding-console"),
            "verify-clamps": ("Проверить прижимы и фиксацию кузова перед циклом.", "Положение кузова подтверждено.", "Все прижимы в зеленой зоне.", "voice-terminal"),
            "run-weld-cycle": ("Запустить цикл и контролировать отсутствие аварий.", "Цикл выполнен или выполняется.", "Нет аварий и остановов робота.", "welding-console"),
            "measure-seam": ("Измерить шов и подтвердить геометрию.", "Идет контроль геометрии шва.", "Шов укладывается в допуск.", "seam-gauge"),
            "identify-engine": ("Считать номер двигателя и открыть маршрут сборки.", "Двигатель идентифицирован.", "Маршрут соответствует модификации.", "scanner"),
            "mount-block": ("Установить блок на стенд и зафиксировать.", "Блок установлен на стенде.", "Фиксация блока подтверждена.", "voice-terminal"),
            "tighten-head-bolts": ("Затянуть болты ГБЦ по карте момента и угла.", "Оператор выполняет затяжку.", "Кривая момента не выходит за допуск.", "torque-wrench"),
            "check-torque-curve": ("Сравнить фактическую кривую момента с эталоном.", "Данные затяжки записаны.", "Кривая подтверждена системой.", "angle-gauge"),
            "close-operation": ("Закрыть операцию в терминале и передать узел дальше.", "Операция ожидает закрытия.", "Все контрольные точки отмечены.", "scanner"),
            "identify-vin": ("Считать VIN автомобиля перед началом операции.", "VIN считан и закреплен за постом.", "VIN совпадает с маршрутным заданием.", "scanner"),
            "mount-door": ("Установить дверь в позиционер и совместить петли.", "Дверь установлена на позицию.", "Совмещение петель без перекоса.", "hinge-aligner"),
            "tighten-bolts": ("Затянуть крепеж двери по регламенту.", "Выполняется затяжка крепежа.", "Момент затяжки в допуске.", "torque-wrench"),
            "scan-checkpoint": ("Сканировать контрольную точку после затяжки.", "Контрольная точка ожидает сканирования.", "Скан подтвержден без ошибки.", "scanner"),
            "visual-inspection": ("Проверить зазоры и внешний вид узла.", "Идет визуальный контроль.", "Нет перекоса, сколов и следов доработки.", "voice-terminal"),
            "check-gaps": ("Измерить зазоры по карте контроля.", "Зазоры проверяются.", "Зазоры в пределах допуска.", "gap-gauge"),
            "check-torque-mark": ("Проверить наличие метки момента.", "Метка момента сверяется.", "Маркировка читается и не смещена.", "scanner"),
            "photo-fixation": ("Сделать фотофиксацию контрольной зоны.", "Фотофиксация ожидается.", "Фото загружено в систему.", "camera-rig"),
            "release-car": ("Разрешить выпуск автомобиля со станции.", "Автомобиль готов к выпуску.", "Все замечания закрыты.", "tablet"),
            "prepare-surface": ("Подготовить поверхность к покраске.", "Поверхность очищена и обезжирена.", "Нет загрязнений и влаги.", "voice-terminal"),
            "set-paint-mode": ("Выставить режим камеры и тип нанесения.", "Параметры камеры настраиваются.", "Температура и влажность в норме.", "tablet"),
            "spray-layer": ("Нанести слой краски по технологической карте.", "Идет нанесение слоя.", "Факел и подача материала стабильны.", "paint-gun"),
            "measure-thickness": ("Проверить толщину покрытия после прохода.", "Толщина покрытия измеряется.", "Толщина в нормативном диапазоне.", "thickness-meter"),
            "read-route-task": ("Открыть маршрутное задание на комплект.", "Задание на комплект получено.", "Код задания подтвержден.", "tablet"),
            "scan-cell": ("Сканировать ячейку хранения деталей.", "Ячейка отсканирована.", "Система подтвердила правильную ячейку.", "scanner"),
            "pick-parts": ("Отобрать детали в комплект по списку.", "Оператор отбирает комплект.", "Каждая позиция отмечена сканером.", "pick-to-light"),
            "verify-kit": ("Проверить полноту набора перед отправкой.", "Комплект ожидает верификации.", "В комплекте нет пропусков.", "scanner"),
            "deliver-kit": ("Подать комплект на линию и закрыть маршрут.", "Комплект готов к подаче.", "Подача подтверждена в системе.", "voice-terminal"),
        }

    @staticmethod
    def incident_catalog() -> list[dict[str, str]]:
        return [
            {"code": "wrong_tool", "label": "Неверный инструмент"},
            {"code": "skipped_check", "label": "Пропущена контрольная операция"},
            {"code": "parameter_out", "label": "Параметр вне допуска"},
            {"code": "otk_return", "label": "ОТК вернул узел"},
            {"code": "foreign_interference", "label": "Вмешательство на чужом участке"},
            {"code": "mentor_fix", "label": "Мастер помог исправить"},
            {"code": "self_fix", "label": "Рабочий сам исправил ошибку"},
        ]

    def _ensure_state(self, operator_id: str, station_id: str) -> dict[str, object]:
        key = self._key(operator_id, station_id)
        return self.runtime_state.setdefault(key, {"event_log": [], "cycle_count": 1})

    def _append_event(
        self,
        operator_id: str,
        station_id: str,
        incident_code: str,
        title: str,
        severity: str,
        description: str,
        trust_delta: float,
        payroll_delta_rub: float,
        step_code: str,
        source: str = "worker_ui",
    ) -> IncidentEvent:
        self.event_seq += 1
        event = IncidentEvent(
            event_id=f"evt-{self.event_seq:04d}",
            title=title,
            incident_code=incident_code,
            severity=severity,
            source=source,
            description=description,
            trust_delta=trust_delta,
            payroll_delta_rub=payroll_delta_rub,
            step_code=step_code,
        )
        state = self._ensure_state(operator_id, station_id)
        event_log = list(state.get("event_log", []))
        event_log.append(event.model_dump())
        state["event_log"] = event_log
        return event

    def _current_events(self, operator_id: str, station_id: str) -> list[IncidentEvent]:
        state = self._ensure_state(operator_id, station_id)
        return [IncidentEvent(**item) for item in state.get("event_log", [])]

    def _build_access(self, operator: Operator, station: Station) -> AccessDecision:
        allowed = station.id in operator.station_ids
        if allowed:
            return AccessDecision(
                allowed=True,
                message=f"Оператор закреплен за участком '{station.department}'. Можно продолжать работу.",
                suggested_stations=[],
            )

        suggested = [self.stations[station_id].name for station_id in operator.station_ids if station_id in self.stations]
        return AccessDecision(
            allowed=False,
            message=(
                f"Оператор '{operator.full_name}' закреплен за отделом '{operator.department}', "
                f"а выбран участок '{station.department}'. Подтверждение шага заблокировано."
            ),
            suggested_stations=suggested,
        )

    @staticmethod
    def _risk_level_from_index(value: float) -> str:
        if value >= 0.8:
            return "critical"
        if value >= 0.6:
            return "high"
        if value >= 0.35:
            return "medium"
        return "low"

    def _get_base_context(self, operator_id: str, station_id: str):
        operator = self.operators[operator_id]
        station = self.stations[station_id]
        mes_task = deepcopy(self.mes.get_task(operator_id, station_id))
        sensor_snapshot = deepcopy(self.scada.get_snapshot(station_id))
        motivation = self.erp.get_motivation_profile(operator_id)
        state = self._ensure_state(operator_id, station_id)

        if "completed_steps" in state:
            mes_task.completed_steps = list(state["completed_steps"])
        if "current_step" in state:
            mes_task.current_step = str(state["current_step"])
        if "selected_tool" in state:
            sensor_snapshot.tool_connected = str(state["selected_tool"])

        return operator, station, mes_task, sensor_snapshot, motivation

    def _build_workflow(self, operator_id: str, station: Station, current_step: str, completed_steps: list[str]) -> WorkflowState:
        current_index = station.process_steps.index(current_step)
        step_meta = self._step_profiles()
        state = self._ensure_state(operator_id, station.id)
        cycle_number = int(state.get("cycle_count", 1))
        steps: list[WorkflowStep] = []

        for index, step_code in enumerate(station.process_steps):
            if step_code in completed_steps:
                status = "done"
            elif step_code == current_step:
                status = "current"
            elif index == current_index + 1:
                status = "next"
            else:
                status = "blocked"

            instruction = {
                "done": "Шаг выполнен и зафиксирован.",
                "current": "Выполняйте этот шаг сейчас и подтвердите завершение на терминале.",
                "next": "Подготовьте инструмент и переходите сюда следующим действием.",
                "blocked": "Этот шаг откроется после завершения предыдущих операций.",
            }[status]
            requirement, worker_state, check_item, required_tool = step_meta.get(
                step_code,
                ("Выполнить шаг по технологическому регламенту.", "Состояние шага уточняется системой.", "Подтвердить завершение шага.", station.allowed_tools[0]),
            )

            steps.append(
                WorkflowStep(
                    code=step_code,
                    title=self._step_title(step_code),
                    status=status,
                    instruction=instruction,
                    requirement=requirement,
                    worker_state=worker_state,
                    check_item=check_item,
                    required_tool=required_tool,
                )
            )

        return WorkflowState(
            station_label=f"{station.line} / {station.name}",
            current_step_title=self._step_title(current_step),
            next_step_title=self._step_title(station.process_steps[min(current_index + 1, len(station.process_steps) - 1)]),
            completion_percent=round(len(completed_steps) / len(station.process_steps) * 100, 1),
            steps=steps,
            cycle_number=cycle_number,
        )

    def _build_analytics(self, operator_id: str, station_id: str, event_log: list[IncidentEvent]) -> AnalyticsState:
        state = self._ensure_state(operator_id, station_id)
        counts: dict[str, int] = {}
        for event in event_log:
            counts[event.title] = counts.get(event.title, 0) + 1
        top_incident = max(counts, key=counts.get) if counts else "Нет критичных повторов"
        return AnalyticsState(
            cycle_count=int(state.get("cycle_count", 1)) - 1,
            total_incidents=len(event_log),
            critical_incidents=sum(1 for event in event_log if event.severity == "critical"),
            recovery_actions=sum(1 for event in event_log if event.severity == "recovery"),
            top_incident=top_incident,
        )

    @staticmethod
    def _clear_cached_shift_report(state: dict[str, object]) -> None:
        state.pop("last_closed_shift_csv", None)

    def _compose_shift_csv(self, evaluation: TwinEvaluation) -> str:
        analytics = evaluation.analytics
        learning = evaluation.learning
        payroll = evaluation.payroll
        trust_delta = round(learning.trust_score - evaluation.operator.shift_start_trust_score, 2)

        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["report_generated_at", datetime.now().isoformat(timespec="seconds")])
        writer.writerow(["operator_id", evaluation.operator.id])
        writer.writerow(["operator_name", evaluation.operator.full_name])
        writer.writerow(["station_id", evaluation.station.id])
        writer.writerow(["station_name", evaluation.station.name])
        writer.writerow(["cycles_completed", analytics.cycle_count])
        writer.writerow(["total_incidents", analytics.total_incidents])
        writer.writerow(["critical_incidents", analytics.critical_incidents])
        writer.writerow(["recovery_actions", analytics.recovery_actions])
        writer.writerow(["trust_delta", trust_delta])
        writer.writerow(["projected_shift_total_rub", payroll.projected_shift_total_rub])
        writer.writerow(["incident_penalty_rub", payroll.incident_penalty_rub])
        writer.writerow([])
        writer.writerow(["event_id", "severity", "incident_code", "title", "step_code", "trust_delta", "payroll_delta_rub", "description"])
        for event in evaluation.event_log:
            writer.writerow(
                [
                    event.event_id,
                    event.severity,
                    event.incident_code,
                    event.title,
                    event.step_code,
                    event.trust_delta,
                    event.payroll_delta_rub,
                    event.description,
                ]
            )
        return buffer.getvalue()

    @staticmethod
    def _build_kind_feedback(cycle_count: int, total_incidents: int, critical_incidents: int, trust_delta: float) -> str:
        if cycle_count >= 2 and critical_incidents == 0 and trust_delta >= 0:
            return "Отличная смена: вы уверенно держали ритм, соблюдали маршрут и работали аккуратно."
        if total_incidents == 0 and trust_delta >= 0:
            return "Хороший результат: вы прошли смену без инцидентов и сохранили качество."
        if trust_delta > 0:
            return "Смена вышла непростой, но вы исправляли отклонения и показали рост по дисциплине."
        if critical_incidents > 0:
            return "Есть зоны роста: важно усилить контроль критических шагов, а база у вас уже есть."
        return "Неплохая смена: продолжаем закреплять правильный инструмент и последовательность операций."

    def close_shift(self, operator_id: str, station_id: str) -> ShiftSummary:
        evaluation = self.evaluate(operator_id, station_id)
        analytics = evaluation.analytics
        learning = evaluation.learning
        payroll = evaluation.payroll
        trust_delta = round(learning.trust_score - evaluation.operator.shift_start_trust_score, 2)
        kind_feedback = self._build_kind_feedback(
            cycle_count=analytics.cycle_count,
            total_incidents=analytics.total_incidents,
            critical_incidents=analytics.critical_incidents,
            trust_delta=trust_delta,
        )

        summary = ShiftSummary(
            operator_id=evaluation.operator.id,
            operator_name=evaluation.operator.full_name,
            station_id=evaluation.station.id,
            station_name=evaluation.station.name,
            cycle_count=analytics.cycle_count,
            total_incidents=analytics.total_incidents,
            critical_incidents=analytics.critical_incidents,
            recovery_actions=analytics.recovery_actions,
            trust_delta=trust_delta,
            projected_shift_total_rub=payroll.projected_shift_total_rub,
            incident_penalty_rub=payroll.incident_penalty_rub,
            kind_feedback=kind_feedback,
            csv_download_url=f"/api/session/{operator_id}/{station_id}/report.csv",
        )

        # Start a new shift after the summary is shown.
        state = self._ensure_state(operator_id, station_id)
        state["last_closed_shift_csv"] = self._compose_shift_csv(evaluation)
        state["event_log"] = []
        state["cycle_count"] = 1
        state["completed_steps"] = []
        state["current_step"] = self.stations[station_id].process_steps[0]

        return summary

    def build_shift_report_csv(self, operator_id: str, station_id: str) -> str:
        state = self._ensure_state(operator_id, station_id)
        cached = state.get("last_closed_shift_csv")
        if isinstance(cached, str) and cached:
            return cached
        evaluation = self.evaluate(operator_id, station_id)
        return self._compose_shift_csv(evaluation)

    def set_selected_tool(self, operator_id: str, station_id: str, tool_name: str) -> ActionResult:
        station = self.stations[station_id]
        if tool_name not in station.allowed_tools:
            return ActionResult(success=False, message=f"Инструмент '{tool_label(tool_name)}' не входит в профиль участка.")

        state = self._ensure_state(operator_id, station_id)
        self._clear_cached_shift_report(state)
        state["selected_tool"] = tool_name
        return ActionResult(success=True, message=f"Выбран инструмент '{tool_label(tool_name)}'.")

    def register_incident(self, operator_id: str, station_id: str, incident_code: str) -> ActionResult:
        self._clear_cached_shift_report(self._ensure_state(operator_id, station_id))
        operator, station, mes_task, sensor_snapshot, _ = self._get_base_context(operator_id, station_id)
        workflow = self._build_workflow(operator_id, station, mes_task.current_step, mes_task.completed_steps)
        current_step = next(step for step in workflow.steps if step.status == "current")

        incident_map = {
            "wrong_tool": ("Неверный инструмент", "incident", f"На шаге '{current_step.title}' использован инструмент '{tool_label(sensor_snapshot.tool_connected)}' вместо '{tool_label(current_step.required_tool)}'.", -1.4, -120.0),
            "skipped_check": ("Пропущена контрольная операция", "incident", f"Рабочий пропустил контрольный шаг на операции '{current_step.title}'.", -2.2, -180.0),
            "parameter_out": ("Параметр вне допуска", "defect", f"На шаге '{current_step.title}' параметр операции вышел за допустимый диапазон.", -3.4, -260.0),
            "otk_return": ("ОТК вернул узел", "critical", f"После участка '{station.name}' узел был возвращен ОТК на доработку.", -5.0, -420.0),
            "foreign_interference": ("Вмешательство на чужом участке", "critical", f"Оператор из отдела '{operator.department}' вмешался в работу участка '{station.department}' без допуска.", -4.4, -300.0),
            "mentor_fix": ("Мастер помог исправить", "recovery", f"Мастер помог вовремя скорректировать выполнение шага '{current_step.title}'.", 0.6, 40.0),
            "self_fix": ("Рабочий сам исправил ошибку", "recovery", f"Оператор самостоятельно исправил отклонение на шаге '{current_step.title}' до возникновения дефекта.", 1.0, 70.0),
        }
        if incident_code not in incident_map:
            return ActionResult(success=False, message="Неизвестный тип инцидента.")

        title, severity, description, trust_delta, payroll_delta = incident_map[incident_code]
        event = self._append_event(
            operator_id=operator_id,
            station_id=station_id,
            incident_code=incident_code,
            title=title,
            severity=severity,
            description=description,
            trust_delta=trust_delta,
            payroll_delta_rub=payroll_delta,
            step_code=current_step.code,
        )
        return ActionResult(success=True, message=f"Событие '{event.title}' зафиксировано. Влияние на Trust Score: {event.trust_delta}.")

    def complete_current_step(self, operator_id: str, station_id: str) -> ActionResult:
        self._clear_cached_shift_report(self._ensure_state(operator_id, station_id))
        operator, station, mes_task, sensor_snapshot, _ = self._get_base_context(operator_id, station_id)
        access = self._build_access(operator, station)
        if not access.allowed:
            self._append_event(
                operator_id,
                station_id,
                "foreign_station_attempt",
                "Попытка работы на чужом участке",
                "warning",
                access.message,
                -0.7,
                -40.0,
                mes_task.current_step,
                source="system",
            )
            return ActionResult(success=False, message=access.message)

        workflow = self._build_workflow(operator_id, station, mes_task.current_step, mes_task.completed_steps)
        current_step = next(step for step in workflow.steps if step.status == "current")

        if sensor_snapshot.tool_connected != current_step.required_tool:
            self._append_event(
                operator_id,
                station_id,
                "wrong_tool_attempt",
                "Попытка закрыть шаг с неверным инструментом",
                "warning",
                f"Для шага '{current_step.title}' нужен '{tool_label(current_step.required_tool)}', а выбран '{tool_label(sensor_snapshot.tool_connected)}'.",
                -0.8,
                -60.0,
                current_step.code,
                source="system",
            )
            return ActionResult(
                success=False,
                message=(
                    f"Для шага '{current_step.title}' нужен инструмент '{tool_label(current_step.required_tool)}', "
                    f"а сейчас выбран '{tool_label(sensor_snapshot.tool_connected)}'."
                ),
            )

        regulation = self.regulation_engine.evaluate(station, mes_task, sensor_snapshot)
        if not regulation.current_step_allowed or not regulation.tool_allowed:
            return ActionResult(success=False, message=regulation.violation_reason or "Нельзя завершить шаг из-за нарушения регламента.")

        state = self._ensure_state(operator_id, station_id)
        completed_steps = list(mes_task.completed_steps)
        completed_steps.append(mes_task.current_step)

        current_index = station.process_steps.index(mes_task.current_step)
        if current_index + 1 < len(station.process_steps):
            state["completed_steps"] = completed_steps
            state["current_step"] = station.process_steps[current_index + 1]
            next_title = self._step_title(station.process_steps[current_index + 1])
            return ActionResult(success=True, message=f"Шаг подтвержден. Следующий шаг: '{next_title}'.")

        # Finish cycle, reward, and restart from step one
        self._append_event(
            operator_id,
            station_id,
            "cycle_completed",
            "Производственный цикл завершен",
            "recovery",
            f"Оператор завершил полный цикл на участке '{station.name}' без остановки процесса.",
            1.8,
            160.0,
            mes_task.current_step,
            source="system",
        )
        state["completed_steps"] = []
        state["current_step"] = station.process_steps[0]
        state["cycle_count"] = int(state.get("cycle_count", 1)) + 1
        return ActionResult(success=True, message="Цикл завершен. Маршрут перезапущен, начат новый производственный проход.")

    def evaluate(self, operator_id: str, station_id: str) -> TwinEvaluation:
        operator, station, mes_task, sensor_snapshot, motivation = self._get_base_context(operator_id, station_id)
        access = self._build_access(operator, station)

        digital_trace = self.trace_service.build_trace(operator=operator, station=station, mes_task=mes_task, sensor_snapshot=sensor_snapshot)
        regulation = self.regulation_engine.evaluate(station, mes_task, sensor_snapshot)
        risk = self.risk_engine.evaluate(operator, station, digital_trace, regulation, sensor_snapshot)
        if not access.allowed:
            blocked_boost = 0.21
            adjusted_index = round(min(1.0, risk.cognitive_risk_index + blocked_boost), 3)
            risk = risk.model_copy(
                update={
                    "cognitive_risk_index": adjusted_index,
                    "level": self._risk_level_from_index(adjusted_index),
                    "top_factors": [
                        "Работа на чужом участке без допуска",
                        *risk.top_factors,
                    ],
                    "breakdown": [
                        {
                            "label": "Нарушение доступа",
                            "value": blocked_boost,
                            "explanation": "Оператор пытается работать на участке, к которому не закреплен, поэтому риск резко возрастает.",
                        },
                        *risk.breakdown,
                    ],
                }
            )
        recommendation = self.recommendation_engine.build(station, regulation, risk)
        workflow = self._build_workflow(operator_id, station, mes_task.current_step, mes_task.completed_steps)
        event_log = self._current_events(operator_id, station_id)
        learning = self.reputation_engine.update(operator.trust_score, risk, regulation, motivation, event_log)
        if not access.allowed:
            learning = learning.model_copy(
                update={
                    "trust_score": round(max(0.0, learning.trust_score - 9.5), 2),
                    "bonus_coefficient": round(max(1.0, learning.bonus_coefficient - 0.08), 3),
                    "growth_hint": "Сначала нужен допуск к своему участку и повторное закрепление маршрута.",
                    "micro_lesson": "Работа на чужом участке без допуска повышает риск дефекта и снижает доверие к оператору.",
                    "skill_progress_percent": round(max(0.0, learning.skill_progress_percent - 8.0), 2),
                    "shift_trust_delta": round(learning.shift_trust_delta - 9.5, 2),
                }
            )
        payroll = self.payroll_engine.evaluate(operator, station, risk, learning, recommendation, event_log)
        if not access.allowed:
            payroll = payroll.model_copy(
                update={
                    "earned_so_far_rub": round(max(0.0, payroll.earned_so_far_rub - 140.0), 2),
                    "projected_shift_total_rub": round(max(0.0, payroll.projected_shift_total_rub - 260.0), 2),
                    "risk_penalty_rub": round(payroll.risk_penalty_rub + 260.0, 2),
                    "incident_penalty_rub": round(payroll.incident_penalty_rub - 260.0, 2),
                    "explanation": payroll.explanation
                    + " Дополнительно учтена блокировка работы на чужом участке без допуска.",
                }
            )
        analytics = self._build_analytics(operator_id, station_id, event_log)

        current_workflow_step = next(step for step in workflow.steps if step.status == "current")
        completion_ready = access.allowed and sensor_snapshot.tool_connected == current_workflow_step.required_tool
        interaction = InteractionState(
            selected_tool=sensor_snapshot.tool_connected,
            required_tool=current_workflow_step.required_tool,
            completion_ready=completion_ready,
            hint=(
                "Можно подтверждать шаг."
                if completion_ready
                else f"Сначала выберите инструмент '{tool_label(current_workflow_step.required_tool)}'."
            ),
            progress_message=(
                f"Выполнено {len(mes_task.completed_steps)} из {len(station.process_steps)} шагов. "
                f"Текущий производственный цикл: {workflow.cycle_number}."
            ),
            available_incidents=self.incident_catalog(),
        )

        return TwinEvaluation(
            operator=operator,
            station=station,
            mes_task=mes_task,
            sensor_snapshot=sensor_snapshot,
            digital_trace=digital_trace,
            regulation=regulation,
            risk=risk,
            recommendation=recommendation,
            learning=learning,
            payroll=payroll,
            workflow=workflow,
            access=access,
            interaction=interaction,
            event_log=event_log,
            analytics=analytics,
        )
