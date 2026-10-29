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
      id: 'linear-equations-one-variable',
      title: 'Linear Equations in One Variable',
      grade: 8,
      description: 'Grade 8 · 1 problem · Jev + SymPy',
      problems: [
        { id: 'g08-lin-ex003', title: 'Solve 3(x − 2) + 5 = 2x + 4', uuid: 'g08-lin-ex003' }
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
function loadSelectedProblem() {
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

  // Load the problem's solution graph
  loadSolutionGraph(state.currentProblemUuid);
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

// Load Solution Graph (similar to original but simplified)
function loadSolutionGraph(problemUuid) {
  // Find the graph data from already loaded scripts
  // The graph data should be available in window.SOLUTION_GRAPHS
  // after all the graph.js files have been loaded

  const problemGraphs = Object.values(window.SOLUTION_GRAPHS || {});
  const activeGraph = problemGraphs.find(graph => graph.graph_meta.problem_uuid === problemUuid);

  if (!activeGraph) {
    console.error(`No solution graph found for problem ${problemUuid}`);
    showErrorState(`Problem data not found: ${problemUuid}`);
    return;
  }

  // Initialize the tutor engine with this graph
  state.activeGraph = activeGraph;
  TutorEngine.init(activeGraph);

  // Update problem statement
  const chapter = state.availableChapters.find(item => item.id === state.currentChapter);
  problemBadge.textContent = `NCERT Grade ${state.currentGrade} · ${chapter.title} · Problem ${getProblemNumber(state.currentProblem)} (${activeGraph.graph_meta.problem_uuid})`;
  problemText.textContent = activeGraph.graph_meta.problem_text;

  // Reset session and UI
  resetProblem();
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
function resetProblem() {
  state.session = TutorEngine.newSession();
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

  if (!state.session) return;

  if (state.session.completed) {
    stepLabel.textContent = '✓ Solved';
    stepDotActive.className = 'step-dot-done';
    questionInput.placeholder = 'Problem solved — press "↺ Reset Problem State" to try again.';
  } else if (state.session.trail.length === 0 && !state.session.methodId && !(state.session.pendingLines || []).length) {
    stepLabel.textContent = 'Step 1';
    stepDotActive.className = 'step-dot-active';
    questionInput.placeholder = 'Type your first step for this problem…';
  } else {
    stepLabel.textContent = `Step ${state.session.trail.length + (state.session.pendingLines || []).length + 1}`;
    stepDotActive.className = 'step-dot-active';
    questionInput.placeholder = 'Type your next step…';
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

// Main evaluation
async function evaluateStep() {
  const rawInput = questionInput.value.trim();
  if (!rawInput) {
    alert('Please write your step or reasoning in the box before checking.');
    return;
  }
  if (!state.session) {
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
    const usesJev = state.activeGraph && state.activeGraph.graph_meta && state.activeGraph.graph_meta.use_jev;
    if (usesJev && !state.session.methodId) {
      solveButton.textContent = 'Identifying method...';
      await evaluateWithJev(rawInput);
    } else if (usesJev) {
      await evaluateWithSympyAndGraph(rawInput);
    } else {
      const result = TutorEngine.processStep(rawInput, state.session);
      TutorEngine.applyResult(state.session, result);
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

// Jev + SymPy flow (used until Jev has identified the method).
// Lines that several methods share (e.g. expanding a bracket) are accepted when SymPy says they are
// correct and kept in session.pendingLines; each check sends ALL lines so far to Jev, so Jev can pick
// the method as soon as a distinguishing step appears. Then the lines are replayed into the tutor engine.
async function evaluateWithJev(rawInput) {
  const lines = [...(state.session.pendingLines || []), rawInput];
  const response = await fetch('/api/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problemId: state.currentProblemUuid, studentWork: lines.join('\n') })
  });
  const result = await response.json();
  if (!response.ok && result.status !== 'unavailable') {
    throw new Error(result.message || 'Could not check this step. Please try again.');
  }

  const method = result.method || {};
  const probabilities = method.probabilities;

  // 1. SymPy found a maths mistake: don't keep this line
  if (result.status === 'fix_mistake') {
    renderJevMessage('🔴 MISTAKE IN THIS STEP', result.feedback, 'failure-state', probabilities);
    return;
  }

  // 2. Jev picked a method: lock it in and replay every line through the tutor engine
  if (method.status === 'selected' && method.methodId) {
    if (!TutorEngine.beginMethod(state.session, method.methodId)) {
      throw new Error('The selected method is not available in this problem graph.');
    }
    // Method ids like "method1" don't carry the m1_ prefix the engine groups steps by,
    // so take it from the first step id (e.g. "m1_step1" -> "m1").
    if (!state.session.methodId) {
      const prefix = String(state.session.currentNodeId || '').match(/^(m\d+)_/);
      if (prefix) state.session.methodId = prefix[1];
    }
    state.session.jevMethodId = method.methodId;
    const methodNode = TutorEngine.getNode(method.methodId);
    methodIndicator.textContent = `· ${methodNode.label}`;
    methodIndicator.hidden = false;

    let last = null;
    for (const line of lines) {
      last = TutorEngine.processStep(line, state.session);
      if (last.verdict === 'ACCEPT' || last.verdict === 'CONCLUSION_RIGHT') {
        TutorEngine.applyResult(state.session, last);
      }
    }
    state.session.pendingLines = [];

    if (last && (last.verdict === 'ACCEPT' || last.verdict === 'CONCLUSION_RIGHT')) {
      renderResult(last);
      prependJevNote(`Jev identified: ${methodNode.label} (${Math.round(method.confidence * 100)}%)`, probabilities);
    } else if (last && (last.verdict === 'WRONG_CLAIM' || last.verdict === 'CONCLUSION_WRONG')) {
      // The tutor engine found a mistake (e.g. "daughter = x/6") — show it as an error
      TutorEngine.applyResult(state.session, last);
      renderResult(last);
      prependJevNote(`Jev identified: ${methodNode.label} (${Math.round(method.confidence * 100)}%)`, probabilities);
    } else if (methodDeclaredBy(lines[lines.length - 1]) === method.methodId) {
      const nextNode = TutorEngine.getNode(state.session.currentNodeId);
      renderJevMessage('🟢 GOOD APPROACH',
        `Good start — that is ${methodNode.label}. ${nextNode && nextNode.prompt ? nextNode.prompt : ''}`.trim(),
        'success-state', probabilities);
    } else {
      const nextNode = TutorEngine.getNode(state.session.currentNodeId);
      renderJevMessage('METHOD SELECTED · STEP NOT VERIFIED',
        `Jev identified ${methodNode.label}. ${nextNode ? nextNode.prompt : ''}`, 'warn-state', probabilities);
    }
    return;
  }

  // 3. Fully solved before a method was identified
  if (result.status === 'solved') {
    state.session.completed = true;
    renderJevMessage('🟢 PROBLEM COMPLETED', result.feedback, 'success-state', probabilities);
    return;
  }

  // 4. Correct, but Jev can't tell the method yet (shared step): keep the line and continue
  const validation = result.validation || {};
  const sympyChecked = Array.isArray(validation.lines) && validation.lines.some(l => l.status === 'valid');
  if (sympyChecked && validation.is_valid) {
    state.session.pendingLines = lines;
    renderJevMessage('🟢 CORRECT · METHOD NOT IDENTIFIED YET',
      'Correct so far. This step is shared by more than one method, so keep going — your next step will show which method you are using.',
      'success-state', probabilities);
    return;
  }

  if (method.status === 'off_graph') {
    renderJevMessage('METHOD NOT IN THIS GRAPH', 'Jev could not match this work to one of the supported methods. Try explaining your approach or choose another method.', 'warn-state', probabilities);
    return;
  }
  renderJevMessage('METHOD UNCLEAR', result.feedback || 'Jev is not confident which method you are using. Add another line or explain your approach, then try again.', 'warn-state', probabilities);
}

// After the method is known: SymPy checks the maths, the graph decides the next step.
async function evaluateWithSympyAndGraph(rawInput) {
  let sym = null;
  try {
    const response = await fetch('/api/sympy/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ problemId: state.currentProblemUuid, studentWork: rawInput, methodId: state.session.jevMethodId || null })
    });
    if (response.ok) sym = await response.json();
  } catch (error) {
    console.warn('SymPy check unavailable:', error);
  }

  // 1. SymPy found a maths mistake
  if (sym && Array.isArray(sym.errors) && sym.errors.length) {
    const e = sym.errors[0];
    renderJevMessage('🔴 MISTAKE IN THIS STEP', `There is a mistake in "${e.statement}". ${e.message || ''}`.trim(), 'failure-state');
    return;
  }

  // 2. The graph decides whether this is the expected step
  const result = TutorEngine.processStep(rawInput, state.session);
  if (result.verdict === 'GARBAGE' || result.verdict === 'UNPARSED') {
    const declared = methodDeclaredBy(rawInput);
    const current = TutorEngine.getNode(state.session.currentNodeId);
    const prompt = current && current.prompt ? current.prompt : '';
    if (declared && declared === state.session.jevMethodId) {
      renderJevMessage('🟢 YES — THAT IS YOUR METHOD',
        `"${rawInput}" is how ${TutorEngine.getNode(declared).label} starts. ${prompt}`.trim(), 'success-state');
      return;
    }
    if (declared) {
      const locked = TutorEngine.getNode(state.session.jevMethodId);
      renderJevMessage('🟡 THAT IS A DIFFERENT METHOD',
        `"${rawInput}" starts ${TutorEngine.getNode(declared).label}, but you are working with ${locked ? locked.label : 'another method'}. ` +
        'Keep going with your current method, or press "↺ Reset Problem State" to start again with this one.', 'warn-state');
      return;
    }
  }
  const sympyCorrect = sym && sym.is_valid && Array.isArray(sym.lines) && sym.lines.some(l => l.status === 'valid');
  if ((result.verdict === 'GARBAGE' || result.verdict === 'UNPARSED') && sympyCorrect) {
    const next = TutorEngine.getNode(state.session.currentNodeId);
    renderJevMessage('🟢 CORRECT MATHS · DIFFERENT STEP',
      `"${rawInput}" is mathematically correct, but it is not the step expected here. ${next && next.prompt ? next.prompt : ''}`.trim(),
      'warn-state');
    return;
  }
  TutorEngine.applyResult(state.session, result);
  renderResult(result);
}

// "mother = x", "let daughter be x" … are method choices (listed in a METHOD node's accept list),
// not calculations, so neither SymPy nor the step matcher can check them.
function methodDeclaredBy(rawInput) {
  const nodes = (state.activeGraph && state.activeGraph.nodes) || [];
  const method = nodes.find(n => n.type === 'method' &&
    (n.accept || []).some(a => TutorEngine.matchesAccept(rawInput, a)));
  return method ? method.id : null;
}

// Small bar chart of Jev's probability for each method
function renderProbabilities(probabilities) {
  if (!probabilities || !Object.keys(probabilities).length) return '';
  const rows = Object.entries(probabilities)
    .sort((a, b) => b[1] - a[1])
    .map(([id, p]) => {
      const node = TutorEngine.getNode(id);
      const label = node ? node.label.replace(/^Method \d+:\s*/, '') : id;
      const pct = Math.round(Number(p) * 100);
      return `<div style="display:flex;align-items:center;gap:8px;margin:4px 0;font-size:13px;">
          <span style="flex:0 0 150px;">${escapeHtml(label)}</span>
          <span style="flex:1;height:8px;background:rgba(127,127,127,.2);border-radius:4px;overflow:hidden;">
            <span style="display:block;height:100%;width:${pct}%;background:currentColor;opacity:.6;"></span>
          </span>
          <span style="flex:0 0 40px;text-align:right;">${pct}%</span>
        </div>`;
    }).join('');
  return `<div class="jev-probabilities" style="margin-top:12px;"><div class="answer-meta">JEV · METHOD PROBABILITIES</div>${rows}</div>`;
}

function prependJevNote(text, probabilities) {
  const card = resultArea.querySelector('.answer-card');
  if (!card) return;
  card.insertAdjacentHTML('beforeend', `<p class="answer-note">${escapeHtml(text)}</p>${renderProbabilities(probabilities)}`);
}

function renderJevMessage(label, message, stateClass = 'warn-state', probabilities = null) {
  resultArea.innerHTML = `
    <article class="answer-card ${stateClass}">
      <div class="answer-meta">${escapeHtml(label)}</div>
      <div class="tutor-bubble">
        <div class="tutor-speech">${escapeHtml(message)}</div>
      </div>
      ${renderProbabilities(probabilities)}
    </article>`;
  resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Render Result (simplified from original)
function renderResult(result) {
  if (!state.session) return;

  const v = result.verdict;
  const questionText = state.session.rawInput;
  const conclusionNodeId = state.session.conclusion_node || 'conclusion';
  const conclusion = typeof TutorEngine.getNode === 'function' ?
    TutorEngine.getNode(state.session.conclusion_node || 'conclusion') :
    { prompt: 'State your conclusion', description: 'Problem solved' };

  if (v === 'ACCEPT') {
    if (result.approachOnly) {
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
      const nextIsConclusion = state.session.currentNodeId === conclusionNodeId;
      resultArea.innerHTML = `
        <article class="answer-card success-state">
          <div class="answer-meta">🟢 STEP VERIFIED</div>
          <h3>${praiseText()}</h3>
          <div class="tutor-bubble">
            <div class="tutor-speech">"${escapeHtml(result.parsed.raw)}" — that's correct.</div>
          </div>
          <p>${nextIsConclusion
            ? `Now give your final conclusion: <strong>${escapeHtml(conclusion.prompt)}</strong>`
            : 'What\'s your next step?'}</p>
        </article>`;
    }
    resultArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    return;
  }

  if (v === 'CONCLUSION_RIGHT') {
    const emptyNote = state.session.trail.length === 0
      ? '<p class="answer-note">You stated the conclusion directly — for practice, try showing the steps too!</p>'
      : '';
    resultArea.innerHTML = `
      <article class="answer-card success-state">
        <div class="answer-meta">🟢 PROBLEM COMPLETED · VALID SOLUTION</div>
        <h3>Excellent — solved!</h3>
        <div class="tutor-bubble">
          <div class="tutor-speech">${escapeHtml(conclusion.description)} Your solution is complete.</div>
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
    const hint = typeof TutorEngine.hintFor === 'function' ?
      (TutorEngine.hintFor(state.session, conclusionNodeId) || 'Review the quantities and compare them once more.') :
      'Review your conclusion.';
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
    const explanation = typeof TutorEngine.explainClaim === 'function' ?
      TutorEngine.explainClaim(result.claim) : 'This step contains an error.';
    const hint = typeof TutorEngine.hintFor === 'function' ?
      TutorEngine.hintFor(state.session, result.nodeId) : null;
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
          <div class="tutor-speech">"${escapeHtml(result.parsed.raw)} is true, but it does not yet help answer this question. Connect your step to the quantities in the problem."</div>
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