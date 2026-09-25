// Ainstein Socratic Tutor - Problem 1
// Target: NCERT Grade 8 Chapter 7 Example 1 (g08-hegp107-ex001)
//
// ─── FREE-FLOW TUTOR LOOP ───
// The student types math steps freely. The tutor-engine (tutor-engine.js)
// silently infers the method, verifies every step's mathematical truth,
// corrects mistakes immediately, and decides on its own when the problem
// is solved. The method is NEVER announced to the student.

const inputEl = document.querySelector('#question-input');
const resultEl = document.querySelector('#result');
const solveBtn = document.querySelector('#solve-button');
const previewEl = document.querySelector('#latex-preview');
const resetBtn = document.querySelector('#reset-flow-btn');
const stepIndicatorLabel = document.querySelector('#step-label');
const stepDot1 = document.querySelector('#step-dot-1');

// ─── Engine init (graph loaded from solution_graph/*.solution-graph.js) ───
TutorEngine.init(SOLUTION_GRAPH);

// Session state (managed by the engine's applyResult)
let session = TutorEngine.newSession();

// ─── UI Update ───
function updateStepUI() {
  if (session.completed) {
    stepIndicatorLabel.textContent = '✓ Solved';
    stepDot1.className = 'step-dot-done';
    inputEl.placeholder = 'Problem solved — press "↺ Reset Problem State" to try again.';
  } else if (session.trail.length === 0 && !session.methodId) {
    stepIndicatorLabel.textContent = 'Step 1';
    stepDot1.className = 'step-dot-active';
    inputEl.placeholder = 'Type your first step… e.g., 72÷24 = 3 and 96÷24 = 4';
  } else {
    stepIndicatorLabel.textContent = 'Step ' + (session.trail.length + 1);
    stepDot1.className = 'step-dot-active';
    inputEl.placeholder = 'Type your next step…';
  }
}

// ─── LaTeX preview (unchanged) ───
function formatLatexString(raw) {
  let text = raw.trim();
  if (!text) return '';
  text = text.replace(/\*/g, ' \\times ')
             .replace(/x(?=\s*\d)/g, ' \\times ')
             .replace(/==/g, ' = ');
  return text;
}

function updateLatexPreview() {
  const raw = inputEl.value.trim();
  if (!raw) {
    previewEl.className = 'latex-preview-body empty';
    previewEl.textContent = 'Type math above to see rendered LaTeX here...';
    return;
  }
  const latex = formatLatexString(raw);
  previewEl.className = 'latex-preview-body';
  try {
    if (window.katex) {
      window.katex.render(latex, previewEl, { throwOnError: false, displayMode: true });
    } else {
      previewEl.textContent = latex;
    }
  } catch (err) {
    previewEl.textContent = latex;
  }
}

// Math palette insert helper
document.querySelectorAll('.math-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const insertText = btn.dataset.insert;
    const start = inputEl.selectionStart || 0;
    const end = inputEl.selectionEnd || 0;
    const current = inputEl.value;
    inputEl.value = current.substring(0, start) + insertText + current.substring(end);
    inputEl.focus();
    inputEl.setSelectionRange(start + insertText.length, start + insertText.length);
    updateLatexPreview();
  });
});

// ─── Reset ───
function resetProblem() {
  session = TutorEngine.newSession();
  inputEl.value = '';
  resultEl.innerHTML = '';
  updateLatexPreview();
  updateStepUI();
}

resetBtn.addEventListener('click', resetProblem);

// ─── Feedback rendering ───
const PRAISE = [
  'Right step!',
  'Correct — keep going!',
  "Nice, that's right!",
  'Well done — next one!'
];

function praiseText() {
  return PRAISE[Math.floor(Math.random() * PRAISE.length)];
}

function renderTrailSummary() {
  if (session.trail.length === 0) return '';
  const items = session.trail.map(t =>
    `<div class="step"><b>✓</b>${escapeHtml(t.input)}</div>`
  ).join('');
  return `<div class="steps">${items}</div>`;
}

function escapeHtml(s) {
  // \u0026 is "&" — keeps entity names intact regardless of source formatting
  return String(s)
    .replace(/&/g, '\u0026amp;')
    .replace(/</g, '\u0026lt;')
    .replace(/>/g, '\u0026gt;')
    .replace(/"/g, '\u0026quot;');
}

function renderResult(result) {
  const v = result.verdict;

  if (v === 'ACCEPT') {
    if (result.approachOnly) {
      // Silent method lock-in — never announce the method name.
      resultEl.innerHTML = `
        <article class="answer-card success-state">
          <div class="answer-meta">🟢 GOOD APPROACH</div>
          <h3>Good approach!</h3>
          <div class="tutor-bubble">
            <div class="tutor-speech">"Great — now show me your first step. Work it out one calculation at a time."</div>
          </div>
          <p class="retry-prompt">Type your first calculation above.</p>
        </article>`;
    } else {
      const nextIsConclusion = session.currentNodeId === 'conclusion';
      resultEl.innerHTML = `
        <article class="answer-card success-state">
          <div class="answer-meta">🟢 STEP VERIFIED</div>
          <h3>${praiseText()}</h3>
          <div class="tutor-bubble">
            <div class="tutor-speech">"${escapeHtml(result.parsed.raw)}" — that's correct.</div>
          </div>
          <p>${nextIsConclusion
            ? 'Now give your final conclusion: <strong>are 3 : 4 and 72 : 96 proportional?</strong>'
            : 'What\'s your next step?'}</p>
        </article>`;
    }
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'CONCLUSION_RIGHT') {
    const emptyNote = session.trail.length === 0
      ? '<p class="answer-note">You stated the conclusion directly — for practice, try showing the steps too!</p>'
      : '';
    resultEl.innerHTML = `
      <article class="answer-card success-state">
        <div class="answer-meta">🟢 PROBLEM COMPLETED · VALID SOLUTION</div>
        <h3>Excellent — solved!</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"🟢 3 : 4 and 72 : 96 express the same relationship (3 × 96 = 4 × 72 = 288), so they are proportional. Every step you showed checked out."</div>
        </div>
        ${renderTrailSummary()}
        ${emptyNote}
        <div style="margin-top:14px;">
          <button type="button" class="preset-chip" onclick="document.querySelector('#reset-flow-btn').click();">
            ↺ Start Again
          </button>
        </div>
      </article>`;
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'CONCLUSION_WRONG') {
    const hint = TutorEngine.hintFor(session, 'conclusion') || 'Compare the two ratios once more.';
    resultEl.innerHTML = `
      <article class="answer-card failure-state">
        <div class="answer-meta">🔴 CONCLUSION DOESN'T HOLD</div>
        <h3>That conclusion isn't right.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"🔴 3 : 4 and 72 : 96 ARE proportional — check: 3 × 96 = 288 and 4 × 72 = 288. Recheck your reasoning and give the conclusion again."</div>
        </div>
        <p class="tutor-hint-text">Hint: ${escapeHtml(hint)}</p>
        <p class="retry-prompt">Recheck your steps above, then state your conclusion again.</p>
      </article>`;
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'WRONG_CLAIM') {
    const explanation = TutorEngine.explainClaim(result.claim);
    const hint = TutorEngine.hintFor(session, result.nodeId);
    resultEl.innerHTML = `
      <article class="answer-card failure-state">
        <div class="answer-meta">🔴 MISTAKE IN THIS STEP</div>
        <h3>This step has a mistake.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"🔴 ${escapeHtml(explanation)} Fix this step and try it again."</div>
        </div>
        ${hint ? `<p class="tutor-hint-text">Hint: ${escapeHtml(hint)}</p>` : ''}
        <p class="retry-prompt">Correct this step — the tutor will continue from here.</p>
      </article>`;
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'IRRELEVANT_TRUE') {
    resultEl.innerHTML = `
      <article class="answer-card warn-state">
        <div class="answer-meta">🟡 TRUE — BUT NOT WHAT WE NEED</div>
        <h3>That's correct math, but it doesn't answer the question.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"🟡 ${escapeHtml(result.parsed.raw)} is true, but it doesn't help decide whether 3 : 4 and 72 : 96 are proportional. Show me a step that compares the two ratios."</div>
        </div>
        <p class="retry-prompt">Try a step like 72÷24 = 3, or 3 × 96 = 288.</p>
      </article>`;
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'GARBAGE') {
    resultEl.innerHTML = `
      <article class="answer-card failure-state">
        <div class="answer-meta">🔴 NOT A MATH STEP</div>
        <h3>I need an actual math step.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"🔴 That doesn't look like math related to this problem. Write a step like 72÷24 = 3, or tell me your approach (simplify, cross multiply…)."</div>
        </div>
        <p class="retry-prompt">Type a calculation or an approach above.</p>
      </article>`;
    resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  // UNPARSED
  resultEl.innerHTML = `
    <article class="answer-card warn-state">
      <div class="answer-meta">🟡 COULDN'T FOLLOW THAT</div>
      <h3>I couldn't follow that as a math step.</h3>
      <div class="tutor-bubble">
        <div class="tutor-speech">"🟡 Write it as an equation — e.g., 72÷24 = 3, 3 × 96 = 288, or 3:4 = 72:96 — and I'll check it."</div>
      </div>
      <p class="retry-prompt">Type your step as a calculation above.</p>
    </article>`;
  resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ─── Main evaluation ───
function evaluateStep() {
  const rawInput = inputEl.value.trim();
  if (!rawInput) {
    alert('Please write your step or reasoning in the box before checking.');
    return;
  }
  if (session.completed) {
    alert('Problem already solved — press "↺ Reset Problem State" to start again.');
    return;
  }

  const result = TutorEngine.processStep(rawInput, session);
  TutorEngine.applyResult(session, result);
  renderResult(result);
  updateStepUI();
}

// ─── Event Listeners ───
inputEl.addEventListener('input', updateLatexPreview);
solveBtn.addEventListener('click', evaluateStep);
inputEl.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    evaluateStep();
  }
});

window.addEventListener('load', () => {
  resetProblem();
  updateLatexPreview();
});