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
  classifyJevMethod
} from './api/tutorApi.js';

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

    try {
      if (currentProblem.uuid === 'g10-quad-ex001' && !session.method_id) {
        setCheckButtonText('Identifying method...');
        const classification = await classifyJevMethod(currentProblem.uuid, raw);

        if (classification.status === 'off_graph') {
          setJevMessage({
            label: 'METHOD NOT IN THIS GRAPH',
            message: 'Jev could not match this work to one of the supported methods. Try explaining your approach or choose another method.',
            stateClass: 'warn-state'
          });
          return;
        }

        if (classification.status !== 'selected') {
          setJevMessage({
            label: 'METHOD UNCLEAR',
            message: 'Jev is not confident which method you are using. Add another line or explain your approach, then try again.',
            stateClass: 'warn-state'
          });
          return;
        }

        const methodNames = {
          m1_factor: 'Factoring',
          m2_formula: 'Quadratic Formula',
          m3_square: 'Completing the Square',
          m4_graph: 'Graphical Method',
          m5_vieta: 'Sum and Product of Roots',
          m6_trial: 'Trial and Factor Theorem'
        };
        const label = methodNames[classification.methodId] || classification.methodKey || 'Selected Method';

        const stepData = await submitTutorStep(session.session_id, raw);
        setSession((prev) => ({
          ...prev,
          completed: stepData.completed,
          active_node_id: stepData.active_node_id,
          active_label: stepData.active_label,
          prompt: stepData.next_prompt,
          fail_streak: stepData.fail_streak,
          trail: stepData.trail || prev.trail,
          history: stepData.history || prev.history || [],
          method_id: classification.methodId,
          method_label: label,
          is_beginning: false
        }));

        if (stepData.verdict === 'GARBAGE' || stepData.verdict === 'UNPARSED') {
          setJevMessage({
            label: 'METHOD SELECTED · STEP NOT VERIFIED',
            message: `Jev identified ${label.toLowerCase()}, but the tutor could not verify that line as a correct step. ${stepData.next_prompt || ''}`,
            stateClass: 'warn-state'
          });
          setInput('');
          return;
        }

        setStepResult(stepData);
        setInput('');
      } else {
        const stepData = await submitTutorStep(session.session_id, raw);
        setInput('');
        setSession((prev) => ({
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
        }));
        setStepResult(stepData);
      }
    } catch (err) {
      setJevMessage({
        label: 'JEV REQUEST FAILED',
        message: err.message || 'Jev could not classify this response. Please try again.',
        stateClass: 'failure-state'
      });
    } finally {
      setIsChecking(false);
      setCheckButtonText('Check Step');
    }
  };

  // Derive step UI label and placeholder
  const isCompleted = session?.completed || false;
  const isBeginning = session?.is_beginning || (!session?.trail || session.trail.length === 0);
  const stepLabel = isCompleted
    ? '✓ Solved'
    : isBeginning
    ? 'Start'
    : session?.active_label || `Step ${(session?.trail?.length || 0) + 1}`;

  const placeholder = isCompleted
    ? 'Problem solved — press "↺ Reset Problem State" to try again.'
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
              onResetProblem={handleResetProblem}
              onCheckStep={handleCheckStep}
              isChecking={isChecking}
              checkButtonText={checkButtonText}
            />

            <TutorFeedback
              result={stepResult}
              jevMessage={jevMessage}
              onStartAgain={handleResetProblem}
            />
          </>
        )}
      </main>
    </div>
  );
}

