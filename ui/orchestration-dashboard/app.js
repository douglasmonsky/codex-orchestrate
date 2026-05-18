const state = {
  ledgers: [],
  selectedId: null,
  commands: {},
  runtime: null,
  validate: false,
};

const el = {
  validateToggle: document.querySelector("#validate-toggle"),
  refreshButton: document.querySelector("#refresh-button"),
  search: document.querySelector("#ledger-search"),
  sourceFilter: document.querySelector("#source-filter"),
  ledgerCount: document.querySelector("#ledger-count"),
  ledgerList: document.querySelector("#ledger-list"),
  statusPanel: document.querySelector("#status-panel"),
  verdictAnswer: document.querySelector("#verdict-answer"),
  verdictRationale: document.querySelector("#verdict-rationale"),
  runtimeStatus: document.querySelector("#runtime-status"),
  runtimeDetail: document.querySelector("#runtime-detail"),
  validationScore: document.querySelector("#validation-score"),
  validationDetail: document.querySelector("#validation-detail"),
  selectedLedgerId: document.querySelector("#selected-ledger-id"),
  taskDetails: document.querySelector("#task-details"),
  modelList: document.querySelector("#model-list"),
  routingTimeline: document.querySelector("#routing-timeline"),
  lifecycleDetails: document.querySelector("#lifecycle-details"),
  lifecycleEvents: document.querySelector("#lifecycle-events"),
  validationEntries: document.querySelector("#validation-entries"),
  escalationList: document.querySelector("#escalation-list"),
  finalReview: document.querySelector("#final-review"),
  residualRisks: document.querySelector("#residual-risks"),
  commandsList: document.querySelector("#commands-list"),
};

function setStatus(message, isError = false) {
  el.statusPanel.textContent = message;
  el.statusPanel.classList.toggle("error", isError);
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  const payload = await response.json();
  if (!response.ok || payload.status === "error") {
    throw new Error(payload.error || `Request failed: ${url}`);
  }
  return payload;
}

function text(value, fallback = "Not recorded") {
  if (value === undefined || value === null || value === "") return fallback;
  if (Array.isArray(value)) return value.length ? value.join(", ") : fallback;
  if (typeof value === "object") {
    const entries = Object.entries(value)
      .filter(([, item]) => item !== undefined && item !== null && item !== "")
      .map(([key, item]) => `${key}: ${text(item, "none")}`);
    return entries.length ? entries.join(", ") : fallback;
  }
  return String(value);
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function appendDetails(node, rows) {
  clear(node);
  rows.forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = text(value);
    node.append(dt, dd);
  });
}

function tag(label, variant = "") {
  const span = document.createElement("span");
  span.className = `tag${variant ? ` ${variant}` : ""}`;
  span.textContent = label;
  return span;
}

function appendEmpty(node, message) {
  clear(node);
  const empty = document.createElement("p");
  empty.className = "empty-state";
  empty.textContent = message;
  node.append(empty);
}

function appendEvidenceList(node, items, renderItem, emptyMessage = "None recorded.") {
  clear(node);
  if (!items || !items.length) {
    appendEmpty(node, emptyMessage);
    return;
  }
  items.forEach((item) => node.append(renderItem(item)));
}

function evidenceItem(title, rows = []) {
  const section = document.createElement("section");
  section.className = "evidence-item";
  const heading = document.createElement("h3");
  heading.textContent = title;
  section.append(heading);
  rows
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .forEach(([label, value]) => {
      const p = document.createElement("p");
      p.textContent = `${label}: ${text(value)}`;
      section.append(p);
    });
  return section;
}

function filteredLedgers() {
  const query = el.search.value.trim().toLowerCase();
  const source = el.sourceFilter.value;
  return state.ledgers.filter((ledger) => {
    if (source !== "all" && ledger.source !== source) return false;
    if (!query) return true;
    const haystack = [
      ledger.name,
      ledger.task_summary,
      ledger.scenario_id,
      ...(ledger.tier_history || []),
      ...(ledger.agent_roles || []),
      ...(ledger.models_used || []),
      ledger.orchestration_value?.answer,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

function renderLedgerList() {
  const ledgers = filteredLedgers();
  el.ledgerCount.textContent = String(ledgers.length);
  clear(el.ledgerList);
  if (!ledgers.length) {
    const empty = document.createElement("div");
    empty.className = "ledger-item";
    empty.textContent = "No ledgers match the current filters.";
    el.ledgerList.append(empty);
    return;
  }
  ledgers.forEach((ledger) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `ledger-item${ledger.id === state.selectedId ? " active" : ""}`;
    button.setAttribute("aria-pressed", ledger.id === state.selectedId ? "true" : "false");
    button.addEventListener("click", () => selectLedger(ledger.id));

    const title = document.createElement("div");
    title.className = "ledger-title";
    title.textContent = ledger.task_summary || ledger.name;

    const meta = document.createElement("div");
    meta.className = "ledger-meta";
    meta.textContent = `${ledger.source} · ${ledger.scenario_id || "ad hoc"}`;

    const tags = document.createElement("div");
    tags.className = "ledger-tags";
    const failed = ledger.validation?.failed || 0;
    const risks = ledger.residual_risk_count || 0;
    const verdict = ledger.orchestration_value?.answer || "unknown";
    tags.append(
      tag((ledger.tier_history || []).join(", ") || "No tier"),
      tag(verdict, `verdict-tag ${verdict}`),
      tag(`${failed} failed`, failed ? "bad" : "good"),
      tag(`${risks} risks`, risks ? "warn" : "good")
    );

    button.append(title, meta, tags);
    el.ledgerList.append(button);
  });
}

function renderRuntime() {
  if (!state.runtime) return;
  el.runtimeStatus.textContent = state.runtime.status || "unknown";
  const missing = state.runtime.missing_models || [];
  const expected = state.runtime.expected_models || [];
  el.runtimeDetail.textContent = missing.length
    ? `Missing pinned models: ${missing.join(", ")}`
    : `Pinned models available: ${expected.join(", ")}`;
}

function renderCommands() {
  clear(el.commandsList);
  Object.entries(state.commands).forEach(([label, command]) => {
    const row = document.createElement("div");
    row.className = "command-row";
    const code = document.createElement("code");
    code.className = "command";
    code.textContent = `${label}: ${command}`;
    const button = document.createElement("button");
    button.className = "copy-button";
    button.type = "button";
    button.textContent = "Copy";
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(command);
        button.textContent = "Copied";
        window.setTimeout(() => {
          button.textContent = "Copy";
        }, 1200);
      } catch (_error) {
        button.textContent = "Unavailable";
      }
    });
    row.append(code, button);
    el.commandsList.append(row);
  });
}

function renderReport(payload) {
  const report = payload.reports?.[0];
  if (!report) {
    setStatus("Report response did not contain a report.", true);
    return;
  }
  const value = report.orchestration_value || {};
  el.verdictAnswer.textContent = value.answer || "unclear";
  el.verdictRationale.textContent = value.rationale || "No rationale recorded.";
  el.verdictAnswer.closest(".summary-panel").className = `summary-panel verdict-panel verdict-${value.answer || "unclear"}`;

  const validation = report.validation || {};
  el.validationScore.textContent = `${validation.passed || 0} passed / ${validation.failed || 0} failed`;
  if (payload.validation) {
    el.validationDetail.textContent = `Validator status: ${payload.validation.status}`;
  } else {
    el.validationDetail.textContent = `${validation.skipped || 0} skipped. Enable validation to run check scripts.`;
  }

  el.selectedLedgerId.textContent = payload.ledger_id || report.path;
  appendDetails(el.taskDetails, [
    ["Task", report.task?.summary],
    ["Scenario", report.task?.scenario_id],
    ["Repo", report.task?.repo_state],
    ["Started", report.task?.started_at],
    ["Finished", report.task?.finished_at],
    ["Root", report.task?.root],
    ["Tier history", report.tier_history],
  ]);

  appendEvidenceList(
    el.modelList,
    report.routing_decisions || [],
    (decision) => {
      const fallback = decision.intended_model !== decision.actual_model;
      return evidenceItem(`${decision.agent_role || "unknown role"}`, [
        ["route", `${decision.intended_model || "unknown"} -> ${decision.actual_model || "unknown"}`],
        ["effort", decision.reasoning_effort],
        ["runtime", decision.runtime_type],
        ["fallback", fallback ? decision.fallback_notes : "none"],
        ["sufficient", decision.why_model_is_sufficient],
      ]);
    },
    "No model route entries recorded."
  );

  clear(el.routingTimeline);
  const routingDecisions = report.routing_decisions || [];
  if (!routingDecisions.length) {
    appendEmpty(el.routingTimeline, "No routing decisions recorded.");
  }
  routingDecisions.forEach((decision, index) => {
    const item = document.createElement("section");
    item.className = "timeline-item";
    const heading = document.createElement("h3");
    heading.textContent = `${index + 1}. ${decision.agent_role || "unknown role"} · ${decision.tier || "unknown tier"}`;
    const step = document.createElement("p");
    step.textContent = decision.step || "No step recorded.";
    const model = document.createElement("p");
    model.textContent = `Model: ${decision.intended_model || "unknown"} -> ${decision.actual_model || "unknown"} (${decision.reasoning_effort || "unknown"})`;
    const packet = document.createElement("p");
    packet.textContent = `Packet: ${decision.packet_id || "not linked"}`;
    const evidence = document.createElement("p");
    evidence.textContent = `Evidence: ${text(decision.evidence, "None recorded")}`;
    const risks = document.createElement("p");
    risks.textContent = `Open risks: ${text(decision.open_risks, "None recorded")}`;
    const next = document.createElement("p");
    next.textContent = `Next decision: ${decision.next_decision || "None recorded"}`;
    item.append(heading, step, model, packet, evidence, risks, next);
    el.routingTimeline.append(item);
  });

  const lifecycle = report.subagents?.lifecycle || {};
  appendDetails(el.lifecycleDetails, [
    ["Packet IDs", lifecycle.packet_ids],
    ["Events", lifecycle.event_count],
    ["Terminal exits", lifecycle.terminal_packet_ids],
    ["Missing exits", lifecycle.missing_terminal_packet_ids],
    ["Context requests", lifecycle.context_requests?.length || 0],
    ["Packet repairs", lifecycle.packet_repairs?.length || 0],
  ]);
  const lifecycleItems = [
    ...(lifecycle.context_requests || []).map((item) => ({ ...item, _kind: "Context request" })),
    ...(lifecycle.packet_repairs || []).map((item) => ({ ...item, _kind: "Packet repair" })),
  ];
  appendEvidenceList(
    el.lifecycleEvents,
    lifecycleItems,
    (item) => {
      const request = item.context_request || {};
      return evidenceItem(`${item._kind} · ${item.packet_id || "unknown packet"}`, [
        ["role", item.role],
        ["reason", request.reason || item.reason],
        ["requested", request.requested_handle || item.requested_handle],
        ["impact", request.decision_impact || item.decision_impact],
        ["root decision", item.root_decision],
        ["evidence", item.evidence],
      ]);
    },
    "No context requests or packet repairs recorded."
  );

  appendEvidenceList(
    el.validationEntries,
    validation.entries || [],
    (entry) =>
      evidenceItem(entry.command || "Validation command", [
        ["result", entry.result],
        ["evidence", entry.evidence],
      ]),
    "No validation entries recorded."
  );

  appendEvidenceList(
    el.escalationList,
    report.escalations || [],
    (entry) =>
      evidenceItem(`${entry.from_role || "unknown"} -> ${entry.to_role || "unknown"}`, [
        ["reason", entry.reason],
        ["result", entry.result],
      ]),
    "No escalations recorded."
  );

  const finalReview = report.final_review || {};
  el.finalReview.innerHTML = "";
  ["status", "reviewer", "evidence", "blockers"].forEach((key) => {
    const p = document.createElement("p");
    p.textContent = `${key}: ${text(finalReview[key], "None recorded")}`;
    el.finalReview.append(p);
  });

  clear(el.residualRisks);
  const risks = report.residual_risks || [];
  if (!risks.length) {
    const p = document.createElement("p");
    p.textContent = "None recorded.";
    el.residualRisks.append(p);
  } else {
    risks.forEach((risk) => {
      const p = document.createElement("p");
      p.textContent = risk;
      el.residualRisks.append(p);
    });
  }
}

async function selectLedger(id) {
  state.selectedId = id;
  renderLedgerList();
  setStatus(`Loading ${id}...`);
  try {
    const validate = state.validate ? "1" : "0";
    const payload = await fetchJson(`/api/report?id=${encodeURIComponent(id)}&validate=${validate}`);
    renderReport(payload);
    setStatus(`Loaded ${id}.`);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function loadAll() {
  setStatus("Loading dashboard data...");
  try {
    const [ledgersPayload, runtimePayload, commandsPayload] = await Promise.all([
      fetchJson("/api/ledgers"),
      fetchJson("/api/runtime"),
      fetchJson("/api/commands"),
    ]);
    state.ledgers = ledgersPayload.ledgers || [];
    state.runtime = runtimePayload;
    state.commands = commandsPayload.commands || {};
    renderLedgerList();
    renderRuntime();
    renderCommands();
    const first = state.selectedId || state.ledgers.find((ledger) => !ledger.error)?.id;
    if (first) {
      await selectLedger(first);
    } else {
      setStatus("No valid ledgers found.", true);
    }
  } catch (error) {
    setStatus(error.message, true);
  }
}

el.validateToggle.addEventListener("change", () => {
  state.validate = el.validateToggle.checked;
  if (state.selectedId) selectLedger(state.selectedId);
});
el.refreshButton.addEventListener("click", loadAll);
el.search.addEventListener("input", renderLedgerList);
el.sourceFilter.addEventListener("change", renderLedgerList);

loadAll();
