// ---------------------------------------------------------------------
// Socratic Math Tutor — client-side app
//
// Loads the Socratic system prompt + the chapter's structured content,
// then talks directly to the Anthropic Messages API from the browser.
// The API key never leaves localStorage / the request to Anthropic.
// ---------------------------------------------------------------------

const CONTENT_URL = "../content/ch07-proportional-reasoning.json";
const PROMPT_URL = "../prompts/socratic-system-prompt.md";
const API_URL = "https://api.anthropic.com/v1/messages";
const API_VERSION = "2023-06-01";

const state = {
  systemPrompt: null,
  content: null,
  history: [],        // [{role, content}]
  solved: 0,
  attempted: 0,
  apiKey: localStorage.getItem("socratic_api_key") || "",
  model: localStorage.getItem("socratic_model") || "claude-sonnet-5",
};

const els = {
  topics: document.getElementById("topics"),
  messages: document.getElementById("messages"),
  emptyState: document.getElementById("empty-state"),
  chatScroll: document.getElementById("chat-scroll"),
  composer: document.getElementById("composer"),
  input: document.getElementById("input"),
  sendBtn: document.getElementById("send-btn"),
  settingsBtn: document.getElementById("settings-btn"),
  resetBtn: document.getElementById("reset-btn"),
  modalBackdrop: document.getElementById("modal-backdrop"),
  apiKeyInput: document.getElementById("api-key-input"),
  modelSelect: document.getElementById("model-select"),
  modalSave: document.getElementById("modal-save"),
  modalCancel: document.getElementById("modal-cancel"),
  ratioText: document.getElementById("ratio-text"),
  progressFill: document.getElementById("progress-fill"),
};

init();

async function init() {
  const [promptText, content] = await Promise.all([
    fetch(PROMPT_URL).then((r) => r.text()),
    fetch(CONTENT_URL).then((r) => r.json()),
  ]);
  state.content = content;
  state.systemPrompt =
    promptText +
    "\n\n## Knowledge base (JSON) — treat as source of truth\n\n```json\n" +
    JSON.stringify(content) +
    "\n```";

  renderSidebar(content);
  bindEvents();

  if (!state.apiKey) openModal();
}

function renderSidebar(content) {
  const groups = [
    { title: "Concepts", items: content.concepts.map((c) => ({ id: c.id, label: c.name, kind: "concept" })) },
    { title: "Worked examples", items: content.workedExamples.map((e) => ({ id: e.id, label: e.prompt.slice(0, 46) + (e.prompt.length > 46 ? "…" : ""), kind: "example" })) },
  ];
  content.problemSets.forEach((set) => {
    groups.push({
      title: set.label,
      items: set.problems.map((p) => ({ id: p.id, label: p.prompt.slice(0, 46) + (p.prompt.length > 46 ? "…" : ""), kind: "problem" })),
    });
  });

  els.topics.innerHTML = "";
  groups.forEach((g) => {
    const wrap = document.createElement("div");
    wrap.className = "topic-group";
    const title = document.createElement("div");
    title.className = "topic-group-title";
    title.textContent = g.title;
    wrap.appendChild(title);
    g.items.forEach((item) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "topic-item";
      btn.textContent = item.label;
      btn.addEventListener("click", () => startTopic(item));
      wrap.appendChild(btn);
    });
    els.topics.appendChild(wrap);
  });
}

function startTopic(item) {
  let userText;
  if (item.kind === "concept") {
    userText = `I'd like to work on the idea of "${item.label}". Can you start me off with a question rather than explaining it outright?`;
  } else {
    userText = `Let's work on this one: ${item.id}. Please pose it to me and ask your first question.`;
  }
  state.attempted += 1;
  updateProgress();
  sendUserText(userText);
}

function bindEvents() {
  els.composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = els.input.value.trim();
    if (!text) return;
    els.input.value = "";
    autoGrow();
    sendUserText(text);
  });

  els.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      els.composer.requestSubmit();
    }
  });
  els.input.addEventListener("input", autoGrow);

  els.settingsBtn.addEventListener("click", openModal);
  els.modalCancel.addEventListener("click", closeModal);
  els.modalSave.addEventListener("click", saveSettings);

  els.resetBtn.addEventListener("click", () => {
    if (!confirm("Start a new session? This clears the current conversation.")) return;
    state.history = [];
    state.solved = 0;
    state.attempted = 0;
    updateProgress();
    els.messages.innerHTML = "";
    els.emptyState.hidden = false;
  });
}

function autoGrow() {
  els.input.style.height = "auto";
  els.input.style.height = Math.min(els.input.scrollHeight, 140) + "px";
}

function openModal() {
  els.apiKeyInput.value = state.apiKey;
  els.modelSelect.value = state.model;
  els.modalBackdrop.hidden = false;
}

function closeModal() {
  els.modalBackdrop.hidden = true;
}

function saveSettings() {
  state.apiKey = els.apiKeyInput.value.trim();
  state.model = els.modelSelect.value;
  localStorage.setItem("socratic_api_key", state.apiKey);
  localStorage.setItem("socratic_model", state.model);
  closeModal();
}

function updateProgress() {
  els.ratioText.textContent = `${state.solved} : ${state.attempted}`;
  const pct = state.attempted ? Math.round((state.solved / state.attempted) * 100) : 0;
  els.progressFill.style.width = pct + "%";
}

function renderMessage(role, text, opts = {}) {
  els.emptyState.hidden = true;
  const msg = document.createElement("div");
  msg.className = `msg ${role}` + (opts.thinking ? " thinking" : "");
  const who = document.createElement("div");
  who.className = "msg-who";
  who.textContent = role === "tutor" ? "tutor" : "you";
  const body = document.createElement("div");
  body.className = "msg-body";
  body.textContent = text;
  msg.appendChild(who);
  msg.appendChild(body);
  els.messages.appendChild(msg);
  els.chatScroll.scrollTop = els.chatScroll.scrollHeight;

  if (role === "tutor" && !opts.thinking) {
    const markBtn = document.createElement("button");
    markBtn.type = "button";
    markBtn.className = "ghost-btn";
    markBtn.style.marginTop = "4px";
    markBtn.style.alignSelf = "flex-start";
    markBtn.style.fontSize = "0.75rem";
    markBtn.textContent = "I solved it ✓";
    markBtn.addEventListener("click", () => {
      state.solved += 1;
      updateProgress();
      markBtn.disabled = true;
      markBtn.textContent = "Marked solved";
    }, { once: true });
    msg.appendChild(markBtn);
  }
  return msg;
}

async function sendUserText(text) {
  if (!state.apiKey) {
    openModal();
    return;
  }
  renderMessage("student", text);
  state.history.push({ role: "user", content: text });

  const thinkingMsg = renderMessage("tutor", "…thinking", { thinking: true });
  els.sendBtn.disabled = true;

  try {
    const reply = await callClaude();
    thinkingMsg.remove();
    renderMessage("tutor", reply);
    state.history.push({ role: "assistant", content: reply });
  } catch (err) {
    thinkingMsg.remove();
    renderMessage("tutor", `Something went wrong talking to the API: ${err.message}. Check your API key under "API key & model."`);
  } finally {
    els.sendBtn.disabled = false;
  }
}

async function callClaude() {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": state.apiKey,
      "anthropic-version": API_VERSION,
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: state.model,
      max_tokens: 700,
      system: state.systemPrompt,
      messages: state.history,
    }),
  });

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(`${res.status} ${errBody.slice(0, 200)}`);
  }
  const data = await res.json();
  const textBlock = (data.content || []).find((b) => b.type === "text");
  return textBlock ? textBlock.text : "(no response text)";
}
