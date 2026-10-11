"use strict";
let snapshot = null;
let selectedTicket = "DEMO-101";
let currentStep = 0;
const byId = id => document.getElementById(id);
const text = (id, value) => { byId(id).textContent = value; };
const node = (tag, value, className = "") => {
  const element = document.createElement(tag);
  element.textContent = value;
  element.className = className;
  return element;
};
const when = value => value ? `${new Date(value).toISOString().slice(0, 19).replace("T", " ")} UTC` : "Timestamp unavailable";
const walkthrough = [
  {title:"The question was blocked", hint:"Show the recorded question and actual Strands decision. This is executed history, not a fresh generation run.", time:"0:00–0:30", target:"question-card"},
  {title:"A restricted connector passed real checks", hint:"Inspect the generated GET manifest and measured validation report. No arbitrary host, executable code, or write operation is generated.", time:"0:30–1:05", target:"manifest-details"},
  {title:"A human approved the exact tested version", hint:"Show the recorded administrator and approval time. Source inspection and connector activation have separate permission checks.", time:"1:05–1:25", target:"approval-record"},
  {title:"The same capability can be reused", hint:"Copy a prompt, run it live in Computer, then refresh here for the new receipt. Select DEMO-102 to inspect the second record.", time:"1:25–2:25", target:"execution-panel", ticket:"DEMO-101"},
  {title:"Approval does not override source permissions", hint:"Inspect the actual source HTTP 403. No records are returned. Clearly label the synthetic data and explain hosting/data integration still pending.", time:"2:25–3:00", target:"execution-panel", ticket:"DEMO-403"}
];

function stage(title, description, timestamp) {
  const item = document.createElement("li");
  item.append(node("strong", title), node("p", description, "muted"));
  if (timestamp) item.append(node("time", when(timestamp)));
  return item;
}

function renderWorkflow() {
  const proposal = snapshot.proposal;
  text("question", proposal?.question || "No recorded Strands proposal is available for this candidate.");
  text("registry-status", snapshot.approval_verified ? "Approved · evidence verified" : `${snapshot.registry_status} · review required`);
  text("capability-id", snapshot.capability_id);
  text("dataset", snapshot.dataset);
  text("manifest", JSON.stringify(snapshot.manifest, null, 2));
  const validation = snapshot.validation;
  text("checks-summary", `${validation.tests.length} measured checks · ${validation.verified ? "PASS" : "unverified"}`);
  byId("checks").replaceChildren(...validation.tests.map(check => {
    const row = document.createElement("tr");
    row.append(node("td", check.name.replaceAll("_", " ")), node("td", check.status, check.status === "PASS" ? "success" : "denied"));
    return row;
  }));
  const stages = [
    stage("Question blocked", proposal ? `Original inventory result: ${proposal.initial_status}. This is the recorded baseline.` : "No baseline receipt available.", proposal?.recorded_at),
    stage("Strands discovered the gap", proposal ? `${proposal.gap_action === "propose_new_connector" ? "Proposed a new connector" : proposal.gap_action} · ${proposal.entry_point} run ${proposal.run_id}` : "No model execution receipt available.", proposal?.recorded_at),
    stage("Restricted connector validated", `${snapshot.manifest.method} ${snapshot.manifest.path_template} · ${validation.tests.length} checks · ${validation.verified ? "PASS" : "unverified"}`, validation.tested_at),
    stage("Human approved the tested version", snapshot.approval_verified ? `${snapshot.approval.approved_by} · manifest, source, and passing report match the approval event.` : "Approval is absent or cannot be verified. No activation is performed here.", snapshot.approval?.approved_at)
  ];
  stages[3].id = "approval-record";
  byId("journey").replaceChildren(...stages);
  renderExecution();
  highlightStep();
}

function renderExecution() {
  if (!snapshot) return;
  const result = snapshot.executions[selectedTicket];
  const panel = byId("result");
  panel.replaceChildren();
  text("copy-status", "");
  const verified = result && (result.response_verified || result.denial_verified);
  text("result-badge", result ? `${verified ? "" : "Unverified · "}${result.status}${result.http_status ? ` · HTTP ${result.http_status}` : ""}` : "Not executed");
  text("receipt-json", result ? JSON.stringify(result, null, 2) : "No execution receipt is recorded for this input.");
  if (!result) {
    panel.append(node("p", "No MCP execution receipt is available for this input. Run the prompt below in Computer.", "notice"));
  } else {
    panel.append(node("p", `Latest receipt · ${when(result.recorded_at)}`, "trace"));
    if (result.status === "ok" && result.response_verified) {
      panel.append(node("h3", "Question answered with source evidence", "result-title success"));
      for (const issue of result.data.related_issues) {
        const record = document.createElement("div");
        record.className = "record";
        record.append(node("strong", issue.id), node("p", issue.title));
        panel.append(record);
      }
      panel.append(node("strong", "Verified source references", "small"));
      const refs = document.createElement("ul");
      refs.className = "refs";
      for (const ref of result.data.source_refs) refs.append(node("li", ref));
      panel.append(refs, node("p", "Exact source-response hash and returned IDs/references match the synthetic fixture.", "trace"));
    } else if (result.status === "forbidden" && result.denial_verified) {
      panel.append(node("h3", "Access denied by the source", "result-title denied"), node("p", "The receipt reports forbidden. No records are displayed; connector approval does not grant missing source access."));
    } else {
      panel.append(node("h3", "Result requires attention", "result-title denied"), node("p", `Observed status: ${result.status}. No verified source-backed answer is displayed.`));
    }
    panel.append(node("p", `${result.transport || "No outbound request"} · ${result.method || "—"} ${result.path || ""}`, "trace"), node("p", result.receipt, "trace"));
  }
  byId("prompt").value = `Use ContextForge Workflow. Call RunCapability with capability_id ${snapshot.capability_id} and inputs {"ticket_id":"${selectedTicket}"}. Show the actual tool response, dataset label, engineering issues, and source references. Do not generate a new connector or modify approval.`;
}

function selectTicket(ticket) {
  selectedTicket = ticket;
  document.querySelectorAll("[data-ticket]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.ticket === ticket)));
  renderExecution();
}

function highlightStep() {
  document.querySelectorAll(".evidence-focus").forEach(element => element.classList.remove("evidence-focus"));
  byId(walkthrough[currentStep].target)?.classList.add("evidence-focus");
}

function setStep(index) {
  currentStep = index;
  const step = walkthrough[index];
  text("walkthrough-counter", `Three-minute walkthrough · ${index + 1} of ${walkthrough.length}`);
  text("walkthrough-title", step.title);
  text("walkthrough-hint", step.hint);
  text("walkthrough-time", `Suggested: ${step.time}`);
  byId("previous-step").disabled = index === 0;
  text("next-step", index === walkthrough.length - 1 ? "Start again" : "Next step");
  document.querySelectorAll("[data-step]").forEach(button => button.setAttribute("aria-pressed", String(Number(button.dataset.step) === index)));
  byId("manifest-details").open = index === 1;
  byId("validation-details").open = index === 1;
  if (step.ticket) selectTicket(step.ticket);
  highlightStep();
  byId(step.target)?.scrollIntoView({block:"start"});
}

async function refresh() {
  byId("refresh").disabled = true;
  text("connection", "Reading local registry and saved execution receipts…");
  byId("connection").classList.remove("error");
  try {
    const response = await fetch("/api/evidence", {cache: "no-store", signal: AbortSignal.timeout(5000)});
    const data = await response.json();
    if (!response.ok || data.status !== "ok") throw new Error(data.message || "No proof evidence is available yet.");
    snapshot = data;
    renderWorkflow();
    byId("content").hidden = false;
    text("connection", `Evidence refreshed ${new Date().toLocaleTimeString()}. Saved proof only; a refresh does not execute tools. ${data.source_current ? "Source revision matches." : "Source revision changed; review required."}`);
  } catch (error) {
    byId("content").hidden = true;
    byId("connection").classList.add("error");
    text("connection", error instanceof TypeError ? "Could not read the local demo service. Start demo_view.py and refresh." : error.message);
  } finally {
    byId("refresh").disabled = false;
  }
}

document.querySelectorAll("[data-ticket]").forEach(button => {
  button.addEventListener("click", () => selectTicket(button.dataset.ticket));
});
document.querySelectorAll("[data-step]").forEach(button => button.addEventListener("click", () => setStep(Number(button.dataset.step))));
byId("previous-step").addEventListener("click", () => setStep(Math.max(0, currentStep - 1)));
byId("next-step").addEventListener("click", () => setStep((currentStep + 1) % walkthrough.length));
byId("copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(byId("prompt").value);
    text("copy-status", "Copied. Paste into your authorized Computer session.");
  } catch {
    byId("prompt").focus();
    byId("prompt").select();
    text("copy-status", "Select and copy the prompt manually.");
  }
});
byId("refresh").addEventListener("click", refresh);
refresh();
