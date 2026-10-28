// Ainstein Math Tutor - Simple Chapter/Problem Selector
//
// Application State:
//   - currentGrade: selected grade (extracted from chapter ID)
//   - currentChapter: selected chapter identifier
//   - currentProblem: selected problem identifier
//   - currentProblemUuid: UUID of the selected problem
//   - availableChapters: chapters and their available problems

// DOM Elements
const chapterSelect = document.getElementById('chapter-select');
const problemSelect = document.getElementById('problem-select');
const loadProblemBtn = document.getElementById('load-problem');
const problemTitleEl = document.getElementById('problem-title');
const problemDescriptionEl = document.getElementById('problem-description');

// Problem Statement Elements
const problemBadge = document.getElementById('problem-badge');
const problemText = document.getElementById('problem-text');

// UI Controls
const questionInput = document.getElementById('question-input');
const solveButton = document.getElementById('solve-button');
const resetFlowBtn = document.getElementById('reset-flow-btn');
const resultArea = document.getElementById('result');
const methodIndicator = document.getElementById('method-indicator');

// Application State
let state = {
  currentGrade: null,
  currentChapter: null,
  currentProblem: null,
  currentProblemUuid: null,
  availableChapters: [
    {
      id: 'proportional-reasoning',
      title: 'Proportional Reasoning',
      grade: 8,
      description: 'Grade 8 · 14 problems',
      problems: [
        { id: 'g08-hegp107-ex001', title: 'Proportional Ratios: 3:4 and 72:96', uuid: 'g08-hegp107-ex001' },
        { id: 'g08-hegp107-ex002-lemonade', title: 'Lemonade Stand Sugar Ratios', uuid: 'g08-hegp107-ex002' },
        { id: 'g08-hegp107-ex002-ratio', title: 'Proportional Ratios: 6:8 and 72:96', uuid: 'g08-hegp107-ex002-ratio' },
        { id: 'g08-hegp107-ex003', title: 'Compound Wall Strength', uuid: 'g08-hegp107-ex003' },
        { id: 'g08-hegp107-ex004', title: 'Teacher-to-Student Ratio Comparison', uuid: 'g08-hegp107-ex004' },
        { id: 'g08-hegp107-ex005', title: 'Blackboard Width-Height Ratio', uuid: 'g08-hegp107-ex005' },
        { id: 'g08-hegp107-ex006', title: 'Age Ratios: Neelima and Her Mother', uuid: 'g08-hegp107-ex006' },
        { id: 'g08-hegp107-ex007', title: 'Ratio Fill-ins: 14:21', uuid: 'g08-hegp107-ex007' },
        { id: 'g08-hegp107-ex008', title: 'Rice for 80 Students', uuid: 'g08-hegp107-ex008' },
        { id: 'g08-hegp107-ex009', title: 'Car Travels 90 km in 150 minutes', uuid: 'g08-hegp107-ex009' },
        { id: 'g08-hegp107-ex010', title: 'Tea Cost Comparison: Himachal vs Meghalaya', uuid: 'g08-hegp107-ex010' },
        { id: 'g08-hegp107-ex011', title: 'Profit Sharing: Prashanti and Bhuvan', uuid: 'g08-hegp107-ex011' },
        { id: 'g08-hegp107-ex012', title: 'Sand and Cement Ratio Adjustment', uuid: 'g08-hegp107-ex012' },
        { id: 'g08-hegp107-p176-q1', title: 'Figure it Out p.176 Q1', uuid: 'g08-hegp107-p176-q1' },
        { id: 'g08-hegp107-p176-q2', title: 'Figure it Out p.176 Q2', uuid: 'g08-hegp107-p176-q2' },
        { id: 'g08-hegp107-p176-q3', title: 'Figure it Out p.176 Q3', uuid: 'g08-hegp107-p176-q3' }
      ]
    },
    {
      id: 'squares-and-cubes',
      title: 'Squares and Cubes',
      grade: 8,
      description: 'Grade 8 · 3 problems',
      problems: [
        { id: 'g08-hegp101-sqrt-324', title: 'Square Root of 324', uuid: 'g08-hegp101-sqrt-324' },
        { id: 'g08-hegp101-cbrt-3375', title: 'Cube Root of 3375', uuid: 'g08-hegp101-cbrt-3375' },
        { id: 'g08-hegp101-ex-p10-q6', title: 'Smallest Number for Perfect Square', uuid: 'g08-hegp101-ex-p10-q6' }
      ]
    },
    {
      id: 'power-play',
      title: 'Power Play',
      grade: 8,
      description: 'Grade 8 · 3 problems',
      problems: [
        { id: 'g08-hegp102-ex-p11-q1', title: 'Simplify 2⁻⁴ × 2⁷', uuid: 'g08-hegp102-ex-p11-q1' },
        { id: 'g08-hegp102-ex-p26-q5v', title: 'Simplify m⁵n¹²/(mn)⁹', uuid: 'g08-hegp102-ex-p26-q5v' },
        { id: 'g08-hegp102-ex-p26-q1', title: 'Units Digit of 2²²⁴ ÷ 4³²', uuid: 'g08-hegp102-ex-p26-q1' }
      ]
    },
    {
      id: 'inverse-proportion',
      title: 'Inverse Proportion',
      grade: 8,
      description: 'Grade 8 · 3 problems',
      problems: [
        { id: 'g08-hegp203-ex003', title: 'Workers and Road Laying', uuid: 'g08-hegp203-ex003' },
        { id: 'g08-hegp203-ex005', title: 'School Provisions Problem', uuid: 'g08-hegp203-ex005' },
        { id: 'g08-hegp203-ex006', title: 'Ram and Shyam Working Together', uuid: 'g08-hegp203-ex006' }
      ]
    },
    {
      id: 'percentages',
      title: 'Percentages',
      grade: 8,
      description: 'Grade 8 · 3 problems',
      problems: [
        { id: 'g08-hegp201-ex-p19-q1', title: 'Geometry Box Profit and Loss', uuid: 'g08-hegp201-ex-p19-q1' },
        { id: 'g08-hegp201-ex010', title: 'TV Depreciation Problem', uuid: 'g08-hegp201-ex010' },
        { id: 'g08-hegp201-ex-p22-q1', title: 'Simple vs Compound Interest', uuid: 'g08-hegp201-ex-p22-q1' }
      ]
    },
    {
      id: 'algebra-play',
      title: 'Algebra Play',
      grade: 8,
      description: 'Grade 8 · 3 problems',
      problems: [
        { id: 'g08-hegp206-grid-eq', title: 'Grid Intersection Points', uuid: 'g08-hegp206-grid-eq' },
        { id: 'g08-hegp206-age-q7', title: 'Mother and Daughter Age Problem', uuid: 'g08-hegp206-age-q7' },
        { id: 'g08-hegp206-heads-legs', title: 'Horses and Hens Problem', uuid: 'g08-hegp206-heads-legs' }
      ]
    },
    {
      id: 'linear-equation',
      title: 'Linear Equation',
      grade: 10,
      description: 'Grade 10 · Latest problem',
      problems: [
        { id: 'g10-quad-ex001', title: 'Quadratic Equation: x² - 5x + 6 = 0', uuid: 'g10-quad-ex001' }
      ]
    }
  ]
};

// Initialize Application
function initApp() {
  setupEventListeners();
  populateChapterSelector();
  loadInitialData();
  console.log('Ainstein Math Tutor initialized');
}

// Setup Event Listeners
function setupEventListeners() {
  // Chapter Selection
  chapterSelect.addEventListener('change', () => {
    updateProblemSelector();
  });

  // Problem Selection
  problemSelect.addEventListener('change', () => {
    // Just update UI, don't load yet
  });

  // Load Problem Button
  loadProblemBtn.addEventListener('click', loadSelectedProblem);

  // Problem Solver Controls
  resetFlowBtn.addEventListener('click', resetProblem);
  solveButton.addEventListener('click', evaluateStep);

  // Keyboard Shortcuts
  questionInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      evaluateStep();
    }
  });
}

// Populate Chapter Selector
function populateChapterSelector() {
  chapterSelect.innerHTML = '<option value="">Select a chapter...</option>';

  state.availableChapters.forEach(chapter => {
    const option = document.createElement('option');
    option.value = chapter.id;
    option.textContent = `${chapter.title} (${chapter.description})`;
    chapterSelect.appendChild(option);
  });

  chapterSelect.value = state.availableChapters[0].id;
  updateProblemSelector();
}

// Update Problem Selector based on selected chapter
function updateProblemSelector() {
  const chapterId = chapterSelect.value;
  const chapter = state.availableChapters.find(item => item.id === chapterId);
  problemSelect.innerHTML = '<option value="">Select a problem...</option>';

  if (chapter) {
    chapter.problems.forEach(problem => {
      const option = document.createElement('option');
      option.value = problem.id;
      option.textContent = problem.title;
      problemSelect.appendChild(option);
    });
  }
}

// Load Selected Problem
async function loadSelectedProblem() {
  const chapterId = chapterSelect.value;
  const problemId = problemSelect.value;

  if (!chapterId || !problemId) {
    alert('Please select both a chapter and a problem.');
    return;
  }

  // Find the problem to get its UUID
  const chapter = state.availableChapters.find(item => item.id === chapterId);
  const problem = chapter && chapter.problems.find(item => item.id === problemId);
  if (!problem) {
    alert('Problem not found.');
    return;
  }

  // Update state
  state.currentChapter = chapterId;
  state.currentProblem = problemId;
  state.currentProblemUuid = problem.uuid;
  state.currentGrade = chapter.grade;

  // Update problem info display
  updateProblemInfoDisplay();

  // Load problem session from FastAPI backend
  try {
    const res = await fetch('/api/v1/sessions/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ problem_id: state.currentProblemUuid })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Could not start problem session');
    }
    const sessionData = await res.json();
    state.session = sessionData;

    problemBadge.textContent = `NCERT Grade ${state.currentGrade} · ${chapter.title} · Problem ${getProblemNumber(state.currentProblem)} (${sessionData.problem_id})`;
    problemText.textContent = sessionData.problem_text;

    questionInput.value = '';
    resultArea.innerHTML = '';
    methodIndicator.textContent = '';
    methodIndicator.hidden = true;
    updateLatexPreview();
    updateStepUI();
  } catch (err) {
    console.error('Error starting session:', err);
    showErrorState(err.message || `Problem data not found: ${state.currentProblemUuid}`);
  }
}

// Update Problem Info Display
function updateProblemInfoDisplay() {
  const chapter = state.availableChapters.find(c => c.id === state.currentChapter);
  const problem = chapter && chapter.problems.find(p => p.id === state.currentProblem);

  if (chapter && problem) {
    problemTitleEl.textContent = problem.title;
    problemDescriptionEl.textContent = `${chapter.title} - ${chapter.description}`;
  }
}

// Helper Functions
function getProblemNumber(problemId) {
  // Extract number from problem ID like g08-hegp107-ex001 or g08-hegp107-p176-q1
  const exMatch = problemId.match(/ex(\d+)/);
  if (exMatch) return exMatch[1].padStart(2, '0');

  const qMatch = problemId.match(/q(\d+)/i);
  if (qMatch) return qMatch[1].padStart(2, '0');

  return '01';
}

// Reset Problem
async function resetProblem() {
  if (!state.session || !state.session.session_id) {
    await loadSelectedProblem();
    return;
  }
  try {
    const res = await fetch(`/api/v1/sessions/${state.session.session_id}/reset`, {
      method: 'POST'
    });
    if (res.ok) {
      const data = await res.json();
      state.session = data;
    } else {
      await loadSelectedProblem();
      return;
    }
  } catch {
    await loadSelectedProblem();
    return;
  }
  questionInput.value = '';
  resultArea.innerHTML = '';
  methodIndicator.textContent = '';
  methodIndicator.hidden = true;
  updateLatexPreview();
  updateStepUI();
}

// Update Step UI
function updateStepUI() {
  const stepIndicator = document.getElementById('step-indicator');
  const stepLabel = document.getElementById('step-label');
  const stepDotActive = document.getElementById('step-dot-1');
  const problemDescriptionEl = document.getElementById('problem-description');

  if (!state.session) return;

  const chapter = state.availableChapters.find(c => c.id === state.currentChapter);
  const problem = chapter && chapter.problems.find(p => p.id === state.currentProblem);

  if (state.session.completed) {
    stepLabel.textContent = '✓ Solved';
    stepDotActive.className = 'step-dot-done';
    questionInput.placeholder = 'Problem solved — press "↺ Reset Problem State" to try again.';
    if (chapter && problem) {
      problemDescriptionEl.textContent = `${chapter.title} - ${chapter.description}`;
    }
    return;
  }

  const isBeginning = state.session.is_beginning || (!state.session.trail || state.session.trail.length === 0);

  if (isBeginning) {
    stepLabel.textContent = 'Start';
    stepDotActive.className = 'step-dot-active';
    questionInput.placeholder = state.session.prompt || 'Type your first step for this problem…';
    if (chapter && problem) {
      problemDescriptionEl.textContent = `${chapter.title} - ${chapter.description}`;
    }
    return;
  }

  if (state.session.active_label) {
    stepLabel.textContent = state.session.active_label;
  } else {
    const stepCount = (state.session.trail || []).length;
    stepLabel.textContent = `Step ${stepCount + 1}`;
  }

  stepDotActive.className = 'step-dot-active';

  if (state.session.prompt) {
    questionInput.placeholder = state.session.prompt;
    if (state.session.active_node_id === 'given_extraction' || state.session.active_node_id === 'goal_extraction') {
      problemDescriptionEl.textContent = state.session.prompt;
    } else if (chapter && problem) {
      problemDescriptionEl.textContent = `${chapter.title} - ${chapter.description}`;
    }
  } else {
    questionInput.placeholder = 'Type your next step…';
    if (chapter && problem) {
      problemDescriptionEl.textContent = `${chapter.title} - ${chapter.description}`;
    }
  }
}

// Update LaTeX Preview
function formatLatexString(raw) {
  let text = raw.trim();
  if (!text) return '';
  text = text.replace(/\*/g, ' \\times ')
             .replace(/x(?=\s*\d)/g, ' \\times ')
             .replace(/==/g, ' = ');
  return text;
}

function updateLatexPreview() {
  const raw = questionInput.value.trim();
  const previewEl = document.getElementById('latex-preview');

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
    const start = questionInput.selectionStart || 0;
    const end = questionInput.selectionEnd || 0;
    const current = questionInput.value;
    questionInput.value = current.substring(0, start) + insertText + current.substring(end);
    questionInput.focus();
    questionInput.setSelectionRange(start + insertText.length, start + insertText.length);
    updateLatexPreview();
  });
});

// Apply step result updates to state
function applyStepResult(result) {
  state.session.is_beginning = false;
  state.session.completed = result.completed;
  state.session.active_node_id = result.active_node_id;
  state.session.active_label = result.active_label;
  state.session.prompt = result.next_prompt;
  state.session.fail_streak = result.fail_streak;
  if (result.trail) {
    state.session.trail = result.trail;
  }
  if (result.method_id) {
    state.session.method_id = result.method_id;
    if (result.method_label) {
      methodIndicator.textContent = `· ${result.method_label}`;
      methodIndicator.hidden = false;
    }
  }
}

// Main evaluation
async function evaluateStep() {
  const rawInput = questionInput.value.trim();
  if (!rawInput) {
    alert('Please write your step or reasoning in the box before checking.');
    return;
  }
  if (!state.session || !state.session.session_id) {
    alert('Please load a problem first.');
    return;
  }
  if (state.session.completed) {
    alert('Problem already solved — press "↺ Reset Problem State" to start again.');
    return;
  }

  const buttonMarkup = solveButton.innerHTML;
  solveButton.disabled = true;

  try {
    if (state.currentProblemUuid === 'g10-quad-ex001' && !state.session.method_id) {
      solveButton.textContent = 'Identifying method...';
      await evaluateWithJev(rawInput);
    } else {
      const res = await fetch(`/api/v1/sessions/${state.session.session_id}/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_input: rawInput })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Step evaluation failed.');
      }
      const result = await res.json();
      applyStepResult(result);
      renderResult(result);
    }
  } catch (error) {
    renderJevMessage('JEV REQUEST FAILED', error.message || 'Jev could not classify this response. Please try again.', 'failure-state');
  } finally {
    solveButton.disabled = false;
    solveButton.innerHTML = buttonMarkup;
    updateStepUI();
  }
}

async function evaluateWithJev(rawInput) {
  const response = await fetch('/api/jev/method', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problemId: state.currentProblemUuid, studentWork: rawInput })
  });
  const classification = await response.json();

  if (!response.ok) {
    throw new Error(classification.message || 'Jev could not classify this response. Please try again.');
  }

  if (classification.status === 'off_graph') {
    renderJevMessage('METHOD NOT IN THIS GRAPH', 'Jev could not match this work to one of the supported methods. Try explaining your approach or choose another method.');
    return;
  }

  if (classification.status !== 'selected') {
    renderJevMessage('METHOD UNCLEAR', 'Jev is not confident which method you are using. Add another line or explain your approach, then try again.');
    return;
  }

  state.session.method_id = classification.methodId;
  const methodNames = {
    m1_factor: 'Factoring',
    m2_formula: 'Quadratic Formula',
    m3_square: 'Completing the Square',
    m4_graph: 'Graphical Method',
    m5_vieta: 'Sum and Product of Roots',
    m6_trial: 'Trial and Factor Theorem'
  };
  const label = methodNames[classification.methodId] || classification.methodKey || 'Selected Method';
  methodIndicator.textContent = `· ${label}`;
  methodIndicator.hidden = false;

  const stepRes = await fetch(`/api/v1/sessions/${state.session.session_id}/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_input: rawInput })
  });
  if (!stepRes.ok) {
    const err = await stepRes.json().catch(() => ({}));
    throw new Error(err.detail || 'Could not verify step.');
  }
  const result = await stepRes.json();
  applyStepResult(result);

  if (result.verdict === 'GARBAGE' || result.verdict === 'UNPARSED') {
    renderJevMessage('METHOD SELECTED · STEP NOT VERIFIED', `Jev identified ${label.toLowerCase()}, but the tutor could not verify that line as a correct step. ${result.next_prompt || ''}`);
    return;
  }

  renderResult(result);
}

function renderJevMessage(label, message, stateClass = 'warn-state') {
  resultArea.innerHTML = `
    <article class="answer-card ${stateClass}">
      <div class="answer-meta">${escapeHtml(label)}</div>
      <div class="tutor-bubble">
        <div class="tutor-speech">${escapeHtml(message)}</div>
      </div>
    </article>`;
  resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Render Result
function renderResult(result) {
  if (!state.session) return;

  const v = result.verdict;
  const questionText = result.parsed_input || questionInput.value.trim();
  const conclusionPrompt = result.conclusion_prompt || 'State your conclusion';
  const conclusionDesc = result.conclusion_description || 'Problem solved';

  if (v === 'ACCEPT') {
    if (result.approach_only) {
      resultArea.innerHTML = `
        <article class="answer-card success-state">
          <div class="answer-meta">🟢 GOOD APPROACH</div>
          <h3>Good approach!</h3>
          <div class="tutor-bubble">
            <div class="tutor-speech">"Great — now show me your first step. Work it out one calculation at a time."</div>
          </div>
          <p class="retry-prompt">Type your first calculation above.</p>
        </article>`;
    } else {
      resultArea.innerHTML = `
        <article class="answer-card success-state">
          <div class="answer-meta">🟢 STEP VERIFIED</div>
          <h3>${praiseText()}</h3>
          <div class="tutor-bubble">
            <div class="tutor-speech">"${escapeHtml(result.parsed_input)}" — that's correct.</div>
          </div>
          <p>${result.next_is_conclusion
            ? `Now give your final conclusion: <strong>${escapeHtml(conclusionPrompt)}</strong>`
            : "What's your next step?"}</p>
        </article>`;
    }
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'CONCLUSION_RIGHT') {
    const emptyNote = (result.trail || []).length <= 1
      ? '<p class="answer-note">You stated the conclusion directly — for practice, try showing the steps too!</p>'
      : '';
    resultArea.innerHTML = `
      <article class="answer-card success-state">
        <div class="answer-meta">🟢 PROBLEM COMPLETED · VALID SOLUTION</div>
        <h3>Excellent — solved!</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">${escapeHtml(result.feedback_message || conclusionDesc)} Your solution is complete.</div>
        </div>
        ${renderTrailSummary()}
        ${emptyNote}
        <div style="margin-top:14px;">
          <button type="button" class="preset-chip" onclick="document.querySelector('#reset-flow-btn').click();">
            ↺ Start Again
          </button>
        </div>
      </article>`;
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'CONCLUSION_WRONG') {
    const hint = result.hint || 'Review the quantities and compare them once more.';
    resultArea.innerHTML = `
      <article class="answer-card failure-state">
        <div class="answer-meta">🔴 CONCLUSION DOESN'T HOLD</div>
        <h3>That conclusion isn't right.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">Your conclusion does not match this problem. Recheck your reasoning and try again.</div>
        </div>
        <p class="tutor-hint-text">Hint: ${escapeHtml(hint)}</p>
        <p class="retry-prompt">Recheck your steps above, then state your conclusion again.</p>
      </article>`;
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'WRONG_CLAIM') {
    const explanation = result.explanation || 'This step contains an error.';
    const hint = result.hint;
    resultArea.innerHTML = `
      <article class="answer-card failure-state">
        <div class="answer-meta">🔴 MISTAKE IN THIS STEP</div>
        <h3>This step has a mistake.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"🔴 ${escapeHtml(explanation)} Fix this step and try it again."</div>
        </div>
        ${hint ? `<p class="tutor-hint-text">Hint: ${escapeHtml(hint)}</p>` : ''}
        <p class="retry-prompt">Correct this step — the tutor will continue from here.</p>
      </article>`;
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'IRRELEVANT_TRUE') {
    resultArea.innerHTML = `
      <article class="answer-card warn-state">
        <div class="answer-meta">🟡 TRUE — BUT NOT WHAT WE NEED</div>
        <h3>That's correct math, but it doesn't answer the question.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"${escapeHtml(result.parsed_input)} is true, but it does not yet help answer this question. Connect your step to the quantities in the problem."</div>
        </div>
        <p class="retry-prompt">Return to the question: ${escapeHtml(questionText)}</p>
      </article>`;
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'GARBAGE') {
    resultArea.innerHTML = `
      <article class="answer-card failure-state">
        <div class="answer-meta">🔴 NOT A MATH STEP</div>
        <h3>I need an actual math step.</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">"That does not look related to this problem. Try a calculation or explain a method for the question above."</div>
        </div>
        <p class="retry-prompt">Type a calculation or an approach above.</p>
      </article>`;
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  // UNPARSED
  resultArea.innerHTML = `
    <article class="answer-card warn-state">
      <div class="answer-meta">🟡 COULDN'T FOLLOW THAT</div>
      <h3>I couldn't follow that as a math step.</h3>
      <div class="tutor-bubble">
        <div class="tutor-speech">"Try writing a calculation or mathematical relationship that helps answer this question."</div>
      </div>
      <p class="retry-prompt">Type your step as a calculation above.</p>
    </article>`;
  resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Helper Functions for Feedback
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
  if (!state.session || !state.session.trail || state.session.trail.length === 0) return '';
  const items = state.session.trail.map(t =>
    `<div class="step"><b>✓</b>${escapeHtml(t.input)}</div>`
  ).join('');
  return `<div class="steps">${items}</div>`;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Load Initial Data
function loadInitialData() {
  // For now, we use the hardcoded data in state
  // In future, this could fetch from a backend API
  console.log('Initial data loaded');
}

// Show Error State
function showErrorState(message) {
  problemTitleEl.textContent = 'Error Loading Problem';
  problemDescriptionEl.textContent = message;
  problemBadge.textContent = '';
  problemText.textContent = 'Unable to load problem data. Please check your selection and try again.';
  resultArea.innerHTML = `
    <article class="answer-card failure-state">
      <div class="answer-meta">🔴 LOADING ERROR</div>
      <h3>Problem Data Unavailable</h3>
      <div class="tutor-bubble">
        <div class="tutor-speech">We couldn't load the data for this problem. Please try selecting a different problem or refresh the page.</div>
      </div>
    </article>`;
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);