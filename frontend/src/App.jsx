import React, { useState, useEffect, useMemo } from 'react';
import Sidebar from './components/Sidebar.jsx';
import TopbarAndHero from './components/TopbarAndHero.jsx';
import ProblemControls from './components/ProblemControls.jsx';
import ProblemCard from './components/ProblemCard.jsx';
import WorkspacePanel from './components/WorkspacePanel.jsx';
import TutorFeedback from './components/TutorFeedback.jsx';
import {
  AVAILABLE_CHAPTERS,
  startTutorSession,
  submitTutorStep,
  resetTutorSession,
  classifyMethod,
  lockMethod
} from './api/tutorApi.js';

const EXTRACTION_NODES = new Set(['given_extraction', 'goal_extraction']);
// Verdicts the result card explains on its own (Jev's note is added underneath)
const STEP_RESULT_VERDICTS = new Set(['ACCEPT', 'CONCLUSION_RIGHT', 'WRONG_CLAIM', 'CONCLUSION_WRONG']);

// Merge a /step response into the session state
function mergeStep(prev, stepData) {
  return {
    ...prev,
    completed: stepData.completed,
    active_node_id: stepData.active_node_id,
    active_label: stepData.active_label,
    prompt: stepData.next_prompt,
    fail_streak: stepData.fail_streak,
    trail: stepData.trail || prev.trail,
    history: stepData.history || prev.history || [],
    method_id: stepData.method_id || prev.method_id,
    method_label: stepData.method_label || prev.method_label,
    is_beginning: false
  };
}

function getProblemNumber(problemId) {
  const exMatch = (problemId || '').match(/ex(\d+)/);
  if (exMatch) return exMatch[1].padStart(2, '0');
  const qMatch = (problemId || '').match(/q(\d+)/i);
  if (qMatch) return qMatch[1].padStart(2, '0');
  return '01';
}

export default function App() {
  const [selectedChapterId, setSelectedChapterId] = useState(AVAILABLE_CHAPTERS[0].id);
  const currentChapter = useMemo(
    () => AVAILABLE_CHAPTERS.find((c) => c.id === selectedChapterId) || AVAILABLE_CHAPTERS[0],
    [selectedChapterId]
  );

  const [selectedProblemId, setSelectedProblemId] = useState(
    currentChapter.problems[0]?.id || ''
  );
  const currentProblem = useMemo(
    () => currentChapter.problems.find((p) => p.id === selectedProblemId) || currentChapter.problems[0],
    [currentChapter, selectedProblemId]
  );

  const [session, setSession] = useState(null);
  const [input, setInput] = useState('');
  const [stepResult, setStepResult] = useState(null);
  const [jevMessage, setJevMessage] = useState(null);
  const [jevNote, setJevNote] = useState(null);
  const [pendingLines, setPendingLines] = useState([]);
  const [isChecking, setIsChecking] = useState(false);
  const [checkButtonText, setCheckButtonText] = useState('Check Step');
  const [isLoadingProblem, setIsLoadingProblem] = useState(false);
  const [loadError, setLoadError] = useState(null);

  // When chapter changes, auto-select first problem of that chapter
  const handleSelectChapter = (chapterId) => {
    setSelectedChapterId(chapterId);
    const ch = AVAILABLE_CHAPTERS.find((c) => c.id === chapterId);
    if (ch && ch.problems.length > 0) {
      setSelectedProblemId(ch.problems[0].id);
    }
  };

  // Load problem session
  const handleLoadProblem = async () => {
    if (!currentChapter || !currentProblem) {
      alert('Please select both a chapter and a problem.');
      return;
    }
    setIsLoadingProblem(true);
    setLoadError(null);
    setStepResult(null);
    setJevMessage(null);
    setJevNote(null);
    setPendingLines([]);
    setInput('');

    try {
      const sessionData = await startTutorSession(currentProblem.uuid);
      setSession(sessionData);
    } catch (err) {
      console.error('Error starting problem session:', err);
      setLoadError(err.message || 'Problem data unavailable.');
      setSession(null);
    } finally {
      setIsLoadingProblem(false);
    }
  };

  // Auto-load initial problem on first mount
  useEffect(() => {
    handleLoadProblem();
  }, []);

  // Reset current session
  const handleResetProblem = async () => {
    if (!session || !session.session_id) {
      handleLoadProblem();
      return;
    }
    try {
      const resetData = await resetTutorSession(session.session_id);
      setSession(resetData);
    } catch {
      handleLoadProblem();
      return;
    }
    setInput('');
    setStepResult(null);
    setJevMessage(null);
    setJevNote(null);
    setPendingLines([]);
  };

  // Jev + SymPy flow (used until Jev has identified the method).
  // Lines that several methods share (e.g. expanding a bracket) are accepted when SymPy says they are
  // correct and kept in pendingLines; each check sends ALL lines so far, so Jev can pick the method as
  // soon as a distinguishing step appears. Then the method is locked and the lines are replayed as steps.
  const checkWithJev = async (raw) => {
    const lines = [...pendingLines, raw];
    const check = await classifyMethod(currentProblem.uuid, lines);
    const method = check.method || {};
    const jevInfo = { probabilities: method.probabilities, labels: check.method_labels };

    // 1. SymPy found a maths mistake: don't keep this line
    if (check.status === 'fix_mistake') {
      setJevMessage({ label: '🔴 MISTAKE IN THIS STEP', message: check.feedback, stateClass: 'failure-state', ...jevInfo });
      return;
    }

    // 2. Jev picked a method: lock it in and replay every line through the tutor
    if (method.status === 'selected' && method.methodId) {
      const lock = await lockMethod(session.session_id, method.methodId);
      // The server has locked the method now, so record it before replaying
      setPendingLines([]);
      setInput('');
      setSession((prev) => ({
        ...prev,
        method_id: lock.method_id,
        method_label: lock.method_label,
        jev_method_id: method.methodId,
        active_node_id: lock.active_node_id,
        active_label: lock.active_label,
        prompt: lock.prompt,
        is_beginning: false
      }));

      const declared = check.declared_methods || [];
      let last = null;
      for (let i = 0; i < lines.length; i++) {
        // "mother = x" chooses the method; it is not a step the tutor can check
        if (declared[i] === method.methodId) continue;
        last = await submitTutorStep(session.session_id, lines[i]);
        const stepData = last;
        setSession((prev) => mergeStep(prev, stepData));
      }

      const note = `Jev identified: ${lock.method_label} (${Math.round(method.confidence * 100)}%)`;
      const nextPrompt = (last ? last.next_prompt : lock.prompt) || '';
      if (declared[lines.length - 1] === method.methodId) {
        setJevMessage({
          label: '🟢 GOOD APPROACH',
          message: `Good start — that is ${lock.method_label}. ${nextPrompt}`.trim(),
          stateClass: 'success-state',
          ...jevInfo
        });
      } else if (last && STEP_RESULT_VERDICTS.has(last.verdict)) {
        setStepResult(last);
        setJevNote({ text: note, ...jevInfo });
      } else {
        setJevMessage({
          label: 'METHOD SELECTED · STEP NOT VERIFIED',
          message: `Jev identified ${lock.method_label}. ${nextPrompt}`.trim(),
          stateClass: 'warn-state',
          ...jevInfo
        });
      }
      return;
    }

    // 3. Fully solved before a method was identified: let the tutor judge the final answer
    if (check.status === 'solved') {
      let last = null;
      for (const line of lines) last = await submitTutorStep(session.session_id, line);
      setPendingLines([]);
      setInput('');
      setSession((prev) => mergeStep(prev, last));
      setStepResult(last);
      return;
    }

    // 4. Correct, but Jev can't tell the method yet (shared step): keep the line and continue
    const validation = check.validation || {};
    const sympyChecked = Array.isArray(validation.lines) && validation.lines.some((l) => l.status === 'valid');
    if (sympyChecked && validation.is_valid) {
      setPendingLines(lines);
      setInput('');
      setJevMessage({
        label: '🟢 CORRECT · METHOD NOT IDENTIFIED YET',
        message: 'Correct so far. This step is shared by more than one method, so keep going — your next step will show which method you are using.',
        stateClass: 'success-state',
        ...jevInfo
      });
      return;
    }

    if (method.status === 'off_graph') {
      setJevMessage({
        label: 'METHOD NOT IN THIS GRAPH',
        message: 'Jev could not match this work to one of the supported methods. Try explaining your approach or choose another method.',
        stateClass: 'warn-state',
        ...jevInfo
      });
      return;
    }
    setJevMessage({
      label: 'METHOD UNCLEAR',
      message: check.feedback || 'Jev is not confident which method you are using. Add another line or explain your approach, then try again.',
      stateClass: 'warn-state',
      ...jevInfo
    });
  };

  // After the method is locked, a step the tutor can't place may still be a method choice or correct maths
  const explainUnplacedStep = async (raw, stepData) => {
    let check;
    try {
      check = await classifyMethod(currentProblem.uuid, [raw]);
    } catch (err) {
      console.warn('Jev check unavailable:', err);
      return false;
    }
    const declared = (check.declared_methods || [])[0];
    const labels = check.method_labels || {};
    const prompt = stepData.next_prompt || '';
    if (check.status === 'fix_mistake') {
      setJevMessage({ label: '🔴 MISTAKE IN THIS STEP', message: check.feedback, stateClass: 'failure-state' });
      return true;
    }
    if (declared && declared === session.jev_method_id) {
      setJevMessage({
        label: '🟢 YES — THAT IS YOUR METHOD',
        message: `"${raw}" is how ${labels[declared] || declared} starts. ${prompt}`.trim(),
        stateClass: 'success-state'
      });
      return true;
    }
    if (declared && session.jev_method_id) {
      setJevMessage({
        label: '🟡 THAT IS A DIFFERENT METHOD',
        message: `"${raw}" starts ${labels[declared] || declared}, but you are working with ${session.method_label || 'another method'}. ` +
          'Keep going with your current method, or press "↺ Reset Problem State" to start again with this one.',
        stateClass: 'warn-state'
      });
      return true;
    }
    const validation = check.validation || {};
    const sympyCorrect = validation.is_valid && Array.isArray(validation.lines) && validation.lines.some((l) => l.status === 'valid');
    if (sympyCorrect) {
      setJevMessage({
        label: '🟢 CORRECT MATHS · DIFFERENT STEP',
        message: `"${raw}" is mathematically correct, but it is not the step expected here. ${prompt}`.trim(),
        stateClass: 'warn-state'
      });
      return true;
    }
    return false;
  };

  // Submit step
  const handleCheckStep = async () => {
    const raw = input.trim();
    if (!raw) {
      alert('Please write your step or reasoning in the box before checking.');
      return;
    }
    if (!session || !session.session_id) {
      alert('Please load a problem first.');
      return;
    }
    if (session.completed) {
      alert('Problem already solved — press "↺ Reset Problem State" to start again.');
      return;
    }

    setIsChecking(true);
    setJevMessage(null);
    setJevNote(null);

    try {
      // Pólya extraction comes first; Jev only identifies the solution method
      // Guided problems ask one question at a time, so the answer goes straight to the tutor
      if (session.use_jev && !session.guided && !session.method_id && !EXTRACTION_NODES.has(session.active_node_id)) {
        setCheckButtonText('Identifying method...');
        await checkWithJev(raw);
      } else {
        const stepData = await submitTutorStep(session.session_id, raw);
        setInput('');
        setSession((prev) => mergeStep(prev, stepData));
        // Guided mode: at the method choice, show how Jev read the answer (and which path's hint it chose)
        if (stepData.jev) {
          setJevNote({ text: stepData.jev.note, probabilities: stepData.jev.probabilities, labels: stepData.jev.labels });
        }
        const unplaced = stepData.verdict === 'GARBAGE' || stepData.verdict === 'UNPARSED';
        if (session.use_jev && !session.guided && session.method_id && unplaced && await explainUnplacedStep(raw, stepData)) {
          setStepResult(null);
        } else {
          setStepResult(stepData);
        }
      }
    } catch (err) {
      // Sessions live in the server's memory: after a server restart the old session is gone
      if (/session not found/i.test(err.message || '')) {
        await handleLoadProblem();
        setJevMessage({
          label: 'SESSION RESTARTED',
          message: 'The tutor was restarted, so this problem has been loaded again. Please start again from the first step.',
          stateClass: 'warn-state'
        });
        return;
      }
      setJevMessage({
        label: 'CHECK FAILED',
        message: err.message || 'This step could not be checked. Please try again.',
        stateClass: 'failure-state'
      });
    } finally {
      setIsChecking(false);
      setCheckButtonText('Check Step');
    }
  };

  // Derive step UI label and placeholder
  const isCompleted = session?.completed || false;
  const isBeginning = pendingLines.length === 0 &&
    (session?.is_beginning || (!session?.trail || session.trail.length === 0));
  const stepLabel = isCompleted
    ? '✓ Solved'
    : pendingLines.length > 0
    ? `Step ${(session?.trail?.length || 0) + pendingLines.length + 1}`
    : isBeginning
    ? 'Start'
    : session?.active_label || `Step ${(session?.trail?.length || 0) + 1}`;

  const placeholder = isCompleted
    ? 'Problem solved — press "↺ Reset Problem State" to try again.'
    : session?.guided
    ? 'Type your answer…'
    : pendingLines.length > 0
    ? 'Type your next step…'
    : isBeginning
    ? session?.prompt || 'Type your first step for this problem…'
    : session?.prompt || 'Type your next step…';

  const methodIndicator = session?.method_label ? `· ${session.method_label}` : null;

  const problemBadge = session
    ? `NCERT Grade ${currentChapter.grade} · ${currentChapter.title} · Problem ${getProblemNumber(currentProblem.id)} (${session.problem_id})`
    : '';

  const problemDescription = (session?.active_node_id === 'given_extraction' || session?.active_node_id === 'goal_extraction')
    ? session.prompt
    : `${currentChapter.title} - ${currentChapter.description}`;

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        <TopbarAndHero />

        <ProblemControls
          chapters={AVAILABLE_CHAPTERS}
          selectedChapterId={selectedChapterId}
          onSelectChapter={handleSelectChapter}
          problems={currentChapter.problems}
          selectedProblemId={selectedProblemId}
          onSelectProblem={setSelectedProblemId}
          onLoadProblem={handleLoadProblem}
          problemTitle={currentProblem?.title}
          problemDescription={problemDescription}
          isLoading={isLoadingProblem}
        />

        {loadError ? (
          <section className="result-area">
            <article className="answer-card failure-state">
              <div className="answer-meta">🔴 LOADING ERROR</div>
              <h3>Problem Data Unavailable</h3>
              <div className="tutor-bubble">
                <div className="tutor-speech">{loadError}</div>
              </div>
            </article>
          </section>
        ) : (
          <>
            <ProblemCard
              badge={problemBadge}
              text={session?.problem_text}
            />

            <WorkspacePanel
              stepLabel={stepLabel}
              isCompleted={isCompleted}
              methodIndicator={methodIndicator}
              trail={session?.trail || []}
              history={session?.history || []}
              input={input}
              onInputChange={setInput}
              placeholder={placeholder}
              question={session?.guided && !isCompleted ? session.prompt : null}
              onResetProblem={handleResetProblem}
              onCheckStep={handleCheckStep}
              isChecking={isChecking}
              checkButtonText={checkButtonText}
            />

            <TutorFeedback
              result={stepResult}
              jevMessage={jevMessage}
              jevNote={jevNote}
              onStartAgain={handleResetProblem}
            />
          </>
        )}
      </main>
    </div>
  );
}

