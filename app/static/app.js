let latestEvaluation = null;

const TOOL_LABELS = {
  "welding-console": "Пульт сварки",
  "seam-gauge": "Шаблон контроля шва",
  "thermal-scanner": "Тепловизор",
  "voice-terminal": "Голосовой терминал",
  "torque-wrench": "Динамометрический ключ",
  "angle-gauge": "Датчик угла затяжки",
  scanner: "Сканер",
  "paint-gun": "Краскопульт",
  "thickness-meter": "Толщиномер",
  tablet: "Планшет",
  "hinge-aligner": "Шаблон петель",
  "gap-gauge": "Щуп зазоров",
  "camera-rig": "Камера фотофиксации",
  "pick-to-light": "Pick-to-light терминал",
};

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function toolLabel(toolCode) {
  return TOOL_LABELS[toolCode] || toolCode;
}

function fillSelect(select, items, labelKey) {
  select.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id ?? item.code ?? item;
    option.textContent = item?.[labelKey] ?? item?.label ?? toolLabel(item);
    select.appendChild(option);
  });
}

function renderList(node, items) {
  node.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    node.appendChild(li);
  });
}

function renderKv(node, entries) {
  node.className = "kv";
  node.innerHTML = entries.map(([key, value]) => `<div><span>${key}</span><strong>${value}</strong></div>`).join("");
}

function prettySegment(segment) {
  const labels = {
    welding: "Сварка",
    assembly: "Сборка",
    paint: "Покраска",
    quality: "Контроль качества",
    logistics: "Логистика",
    infrastructure: "Инфраструктура",
  };
  return labels[segment] || segment;
}

function prettyStatus(status) {
  const labels = { done: "Готово", current: "Сейчас", next: "Далее", blocked: "Позже" };
  return labels[status] || status;
}

function colorizeRisk(level) {
  const target = document.getElementById("risk-level");
  const palette = { low: "var(--good)", medium: "var(--warn)", high: "var(--bad)", critical: "var(--bad)" };
  target.style.color = palette[level] || "var(--text)";
}

function openModal(title, bodyHtml) {
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-body").innerHTML = bodyHtml;
  document.getElementById("modal").classList.add("open");
}

function closeModal() {
  document.getElementById("modal").classList.remove("open");
}

function renderWorkflow(node, workflow) {
  node.innerHTML = workflow.steps
    .map(
      (step, index) => `
        <button class="workflow-step ${step.status}" data-step-index="${index}" type="button">
          <div class="workflow-badge">${index + 1}</div>
          <div>
            <div class="workflow-title">
              <strong>${step.title}</strong>
              <span class="step-state">${prettyStatus(step.status)}</span>
            </div>
            <div class="workflow-instruction">${step.instruction}</div>
          </div>
        </button>
      `
    )
    .join("");

  node.querySelectorAll("[data-step-index]").forEach((button) => {
    button.addEventListener("click", () => {
      const step = latestEvaluation.workflow.steps[Number(button.dataset.stepIndex)];
      openModal(
        step.title,
        `
          <div class="modal-stack">
            <div><span>Статус</span><strong>${prettyStatus(step.status)}</strong></div>
            <div><span>Что требуется</span><strong>${step.requirement}</strong></div>
            <div><span>Что уже сделал рабочий</span><strong>${step.worker_state}</strong></div>
            <div><span>Что проверить</span><strong>${step.check_item}</strong></div>
            <div><span>Нужный инструмент</span><strong>${toolLabel(step.required_tool)}</strong></div>
            <div><span>Подсказка системы</span><strong>${step.instruction}</strong></div>
          </div>
        `
      );
    });
  });
}

function renderEventLog(events) {
  const container = document.getElementById("event-log");
  if (!events.length) {
    container.innerHTML = `<div class="event-empty">Инцидентов в смене пока не зафиксировано.</div>`;
    return;
  }

  container.innerHTML = events
    .slice()
    .reverse()
    .map(
      (event) => `
        <article class="event-item ${event.severity}">
          <div class="event-top">
            <strong>${event.title}</strong>
            <span>${event.event_id}</span>
          </div>
          <p>${event.description}</p>
          <div class="event-meta">
            <span>Шаг: ${event.step_code}</span>
            <span>Trust: ${event.trust_delta}</span>
            <span>Оплата: ${event.payroll_delta_rub} руб</span>
          </div>
        </article>
      `
    )
    .join("");
}

function bindRiskDetails(result) {
  document.getElementById("risk-card").onclick = () => {
    const rows = result.risk.breakdown
      .map(
        (item) => `
          <div class="modal-risk-row">
            <div>
              <strong>${item.label}</strong>
              <p>${item.explanation}</p>
            </div>
            <span>+${item.value}</span>
          </div>
        `
      )
      .join("");

    openModal(
      "Почему такой риск",
      `
        <p class="modal-intro">
          Итоговый индекс когнитивного риска: <strong>${result.risk.cognitive_risk_index}</strong>.
          Ниже показан вклад каждого фактора в расчет.
        </p>
        <div class="modal-risk-table">${rows}</div>
      `
    );
  };
}

function renderAccess(access) {
  const banner = document.getElementById("access-banner");
  banner.classList.remove("hidden", "ok", "warn");
  banner.classList.add(access.allowed ? "ok" : "warn");
  const suffix = !access.allowed && access.suggested_stations.length
    ? ` Разрешенные участки: ${access.suggested_stations.join(", ")}.`
    : "";
  banner.textContent = `${access.message}${suffix}`;
}

async function refreshEvaluation() {
  const operatorId = document.getElementById("operator-select").value;
  const stationId = document.getElementById("station-select").value;
  const result = await fetchJson(`/api/evaluate/${operatorId}/${stationId}`);
  latestEvaluation = result;

  document.getElementById("summary").textContent = result.recommendation.summary;
  document.getElementById("explanation").textContent = result.recommendation.explanation;
  renderList(document.getElementById("actions"), result.recommendation.actions);
  renderList(document.getElementById("teaching-points"), result.recommendation.teaching_points);

  document.getElementById("risk-level").textContent = result.risk.level.toUpperCase();
  document.getElementById("risk-index").textContent = `CRI: ${result.risk.cognitive_risk_index}`;
  document.getElementById("current-step").textContent = result.workflow.current_step_title;
  document.getElementById("next-step").textContent = `Следующий: ${result.workflow.next_step_title}`;
  document.getElementById("recommended-tool").textContent = toolLabel(result.recommendation.recommended_tool);
  document.getElementById("recheck-time").textContent = `Повторная проверка: ${result.recommendation.next_check_in_minutes} мин`;
  document.getElementById("projected-pay").textContent = `${result.payroll.projected_shift_total_rub} руб`;
  document.getElementById("bonus-pay").textContent = `События смены: ${result.payroll.incident_penalty_rub} руб`;
  colorizeRisk(result.risk.level);
  renderAccess(result.access);

  document.getElementById("workflow-station").textContent = result.workflow.station_label;
  document.getElementById("workflow-progress").textContent = `${result.workflow.completion_percent}%`;
  renderWorkflow(document.getElementById("workflow-steps"), result.workflow);
  renderEventLog(result.event_log);
  bindRiskDetails(result);

  fillSelect(document.getElementById("tool-select"), result.station.allowed_tools, null);
  document.getElementById("tool-select").value = result.interaction.selected_tool;
  fillSelect(document.getElementById("incident-select"), result.interaction.available_incidents, null);
  document.getElementById("tool-hint").textContent =
    `Сейчас выбран '${toolLabel(result.interaction.selected_tool)}', для шага нужен '${toolLabel(result.interaction.required_tool)}'. ${result.interaction.hint}`;
  document.getElementById("progress-hint").textContent = result.interaction.progress_message;
  document.getElementById("complete-step-btn").disabled = !result.access.allowed;

  renderKv(document.getElementById("sense"), [
    ["Отдел", result.station.department],
    ["Сегмент", prettySegment(result.station.segment)],
    ["Оборудование", result.station.equipment.join(", ")],
    ["Смена", result.digital_trace.shift_type === "night" ? "Ночная" : "Дневная"],
    ["Подключен", toolLabel(result.digital_trace.tool_connected)],
    ["Усталость", result.digital_trace.fatigue_index],
  ]);

  renderKv(document.getElementById("learn"), [
    ["Trust Score", result.learning.trust_score],
    ["Изменение за смену", result.learning.shift_trust_delta],
    ["Коэффициент K", result.learning.bonus_coefficient],
    ["Прогресс навыка", `${result.learning.skill_progress_percent}%`],
    ["Микрообучение", result.learning.micro_lesson],
    ["Следующий рост", result.learning.growth_hint],
  ]);

  renderKv(document.getElementById("payroll"), [
    ["Заработано сейчас", `${result.payroll.earned_so_far_rub} руб`],
    ["Прогноз за смену", `${result.payroll.projected_shift_total_rub} руб`],
    ["Бонус за качество", `${result.payroll.quality_bonus_rub} руб`],
    ["Удержание за риск", `${result.payroll.risk_penalty_rub} руб`],
    ["Инциденты смены", `${result.payroll.incident_penalty_rub} руб`],
    ["Наставничество", `${result.payroll.mentor_bonus_rub} руб`],
    ["Пояснение", result.payroll.explanation],
  ]);
}

async function applyTool() {
  const operatorId = document.getElementById("operator-select").value;
  const stationId = document.getElementById("station-select").value;
  const toolName = document.getElementById("tool-select").value;
  const result = await fetchJson(`/api/session/${operatorId}/${stationId}/tool`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool_name: toolName }),
  });
  document.getElementById("tool-hint").textContent = result.message;
  await refreshEvaluation();
}

async function completeStep() {
  const operatorId = document.getElementById("operator-select").value;
  const stationId = document.getElementById("station-select").value;
  const result = await fetchJson(`/api/session/${operatorId}/${stationId}/complete`, {
    method: "POST",
  });
  document.getElementById("progress-hint").textContent = result.message;
  await refreshEvaluation();
}

async function applyIncident() {
  const operatorId = document.getElementById("operator-select").value;
  const stationId = document.getElementById("station-select").value;
  const incidentCode = document.getElementById("incident-select").value;
  const result = await fetchJson(`/api/session/${operatorId}/${stationId}/incident/${incidentCode}`, {
    method: "POST",
  });
  document.getElementById("progress-hint").textContent = result.message;
  await refreshEvaluation();
}

async function finishShift() {
  const operatorId = document.getElementById("operator-select").value;
  const stationId = document.getElementById("station-select").value;
  const summary = await fetchJson(`/api/session/${operatorId}/${stationId}/close-shift`, {
    method: "POST",
  });

  openModal(
    "Итоги смены",
    `
      <div class="modal-stack">
        <div><span>Оператор</span><strong>${summary.operator_name}</strong></div>
        <div><span>Участок</span><strong>${summary.station_name}</strong></div>
        <div><span>Завершено циклов</span><strong>${summary.cycle_count}</strong></div>
        <div><span>Всего инцидентов</span><strong>${summary.total_incidents}</strong></div>
        <div><span>Критичных инцидентов</span><strong>${summary.critical_incidents}</strong></div>
        <div><span>Восстановительных действий</span><strong>${summary.recovery_actions}</strong></div>
        <div><span>Δ Trust</span><strong>${summary.trust_delta}</strong></div>
        <div><span>Прогноз оплаты</span><strong>${summary.projected_shift_total_rub} руб</strong></div>
        <div><span>Удержания за инциденты</span><strong>${summary.incident_penalty_rub} руб</strong></div>
        <div><span>Оценка</span><strong>${summary.kind_feedback}</strong></div>
      </div>
      <div style="margin-top: 14px;">
        <a href="${summary.csv_download_url}" class="csv-link">Выгрузить CSV-отчет</a>
      </div>
    `
  );

  await refreshEvaluation();
}

async function bootstrap() {
  const operatorSelect = document.getElementById("operator-select");
  const stationSelect = document.getElementById("station-select");

  const [operators, stations] = await Promise.all([
    fetchJson("/api/operators"),
    fetchJson("/api/stations"),
  ]);

  fillSelect(operatorSelect, operators, "full_name");
  fillSelect(stationSelect, stations, "name");

  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal").addEventListener("click", (event) => {
    if (event.target.id === "modal") {
      closeModal();
    }
  });
  document.getElementById("apply-tool-btn").addEventListener("click", applyTool);
  document.getElementById("apply-incident-btn").addEventListener("click", applyIncident);
  document.getElementById("complete-step-btn").addEventListener("click", completeStep);
  document.getElementById("finish-shift-btn").addEventListener("click", finishShift);
  operatorSelect.addEventListener("change", refreshEvaluation);
  stationSelect.addEventListener("change", refreshEvaluation);

  await refreshEvaluation();
}

bootstrap().catch((error) => {
  document.getElementById("summary").textContent = "Ошибка загрузки";
  document.getElementById("explanation").textContent = error.message;
});
