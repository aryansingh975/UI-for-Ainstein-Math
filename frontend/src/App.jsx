import React, { useState, useEffect, useMemo } from 'react';
import SocraticChatStream from './components/SocraticChatStream.jsx';
import VictoryCelebrationView from './components/VictoryCelebrationView.jsx';
import CurriculumHubView from './components/CurriculumHubView.jsx';
import ProblemRoadmapPanel from './components/ProblemRoadmapPanel.jsx';
import LiveSolutionNotebook from './components/LiveSolutionNotebook.jsx';
import {
  AVAILABLE_CHAPTERS,
  startTutorSession,
  submitTutorStep,
  resetTutorSession,
  classifyJevMethod
} from './api/tutorApi.js';

export default function App() {
  const [currentView, setCurrentView] = useState('workspace'); // 'workspace' | 'curriculum'
  const [isReviewingSteps, setIsReviewingSteps] = useState(false);
  const [selectedChapterId, setSelectedChapterId] = useState(AVAILABLE_CHAPTERS[0].id);
  const [showHint, setShowHint] = useState(false);
  const [showFormulas, setShowFormulas] = useState(false);
  
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

  const currentProblemIndex = useMemo(() => {
    const idx = currentChapter.problems.findIndex((p) => p.id === selectedProblemId);
    return idx >= 0 ? idx : 0;
  }, [currentChapter, selectedProblemId]);

  const totalProblems = currentChapter.problems.length;

  const [session, setSession] = useState(null);
  const [input, setInput] = useState('');
  const [stepResult, setStepResult] = useState(null);
  const [jevMessage, setJevMessage] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const [checkButtonText, setCheckButtonText] = useState('Check Step');
  const [isLoadingProblem, setIsLoadingProblem] = useState(false);
  const [loadError, setLoadError] = useState(null);

  // Solved problems set (stored in localStorage)
  const [solvedProblems, setSolvedProblems] = useState(() => {
    try {
      const saved = localStorage.getItem('ainstein_solved_uuids');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch {
      return new Set();
    }
  });

  const markProblemSolved = (uuid) => {
    if (!uuid) return;
    setSolvedProblems((prev) => {
      const next = new Set(prev);
      next.add(uuid);
      try {
        localStorage.setItem('ainstein_solved_uuids', JSON.stringify([...next]));
      } catch {}
      return next;
    });
  };

  // Load problem session
  const handleLoadProblem = async (problemUuidToLoad) => {
    const targetUuid = problemUuidToLoad || currentProblem?.uuid;
    if (!targetUuid) return;

    setIsLoadingProblem(true);
    setLoadError(null);
    setStepResult(null);
    setJevMessage(null);
    setInput('');
    setIsReviewingSteps(false);
    setShowHint(false);

    try {
      const sessionData = await startTutorSession(targetUuid);
      setSession(sessionData);
    } catch (err) {
      console.error('Error starting problem session:', err);
      setLoadError(err.message || 'Problem data unavailable.');
      setSession(null);
    } finally {
      setIsLoadingProblem(false);
    }
  };

  // Select problem from Curriculum Hub
  const handleSelectProblemFromHub = (chapterId, problemId) => {
    setSelectedChapterId(chapterId);
    setSelectedProblemId(problemId);
    setCurrentView('workspace');
    setIsReviewingSteps(false);
    setShowHint(false);

    const ch = AVAILABLE_CHAPTERS.find((c) => c.id === chapterId);
    const prob = ch?.problems.find((p) => p.id === problemId);
    if (prob) {
      handleLoadProblem(prob.uuid);
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
    setIsReviewingSteps(false);
    setShowHint(false);
  };

  // Next Problem handler
  const handleNextProblem = () => {
    setIsReviewingSteps(false);
    setShowHint(false);
    const pList = currentChapter.problems;
    const currentIndex = pList.findIndex((p) => p.id === selectedProblemId);
    if (currentIndex >= 0 && currentIndex + 1 < pList.length) {
      const nextP = pList[currentIndex + 1];
      setSelectedProblemId(nextP.id);
      handleLoadProblem(nextP.uuid);
    } else {
      // Completed all in this chapter -> open curriculum hub to pick next chapter!
      setCurrentView('curriculum');
    }
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
      alert('Problem already solved — press "↺ Reset Problem" to start again.');
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
        if (stepData.completed) {
          markProblemSolved(currentProblem.uuid);
          setIsReviewingSteps(false);
        }
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
        if (stepData.completed) {
          markProblemSolved(currentProblem.uuid);
          setIsReviewingSteps(false);
        }
      }
    } catch (err) {
      setJevMessage({
        label: 'TUTOR REQUEST FAILED',
        message: err.message || 'Could not verify step with the tutor backend.',
        stateClass: 'failure-state'
      });
    } finally {
      setIsChecking(false);
      setCheckButtonText('Check Step');
    }
  };

  // Toggle and scroll to formula cheat sheet
  const handleScrollToFormulas = () => {
    if (currentView !== 'workspace') {
      setCurrentView('workspace');
    }
    setShowFormulas((prev) => !prev);
    setTimeout(() => {
      const el = document.getElementById('formula-card');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        el.classList.add('ring-2', 'ring-indigo-400');
        setTimeout(() => el.classList.remove('ring-2', 'ring-indigo-400'), 1500);
      }
    }, 50);
  };

  const isCompleted = session?.completed || false;

  return (
    <div className="bg-slate-100/70 text-slate-800 antialiased font-sans lg:h-screen lg:overflow-hidden min-h-screen flex flex-col">
      
      {/* ============================================================== */}
      {/* TOP NAVIGATION HEADER (Studio Style)                           */}
      {/* ============================================================== */}
      <header className="bg-white/95 backdrop-blur-md border-b border-slate-200 shrink-0 sticky top-0 z-30 px-4 sm:px-8 py-2.5 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-4">
          
          {/* App Brand & Grade Badge */}
          <div
            onClick={() => setCurrentView('curriculum')}
            className="flex items-center gap-2.5 cursor-pointer group"
            title="Open Curriculum Hub / Main Menu"
          >
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-700 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-lg font-extrabold tracking-tight bg-gradient-to-r from-indigo-900 to-indigo-700 bg-clip-text text-transparent">
                  AInstein
                </span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                  {currentChapter.grade ? `Class ${currentChapter.grade}` : 'Class 8'}
                </span>
              </div>
              <p className="text-[11px] font-medium text-slate-400">Think · Explore · Understand</p>
            </div>
          </div>

          {/* Breadcrumbs */}
          <nav className="hidden md:flex items-center gap-2 text-xs text-slate-500 pl-4 border-l border-slate-200">
            <button
              type="button"
              onClick={() => setCurrentView('curriculum')}
              className="hover:text-indigo-600 font-semibold cursor-pointer transition-colors"
            >
              Mathematics
            </button>
            <span>›</span>
            <button
              type="button"
              onClick={() => setCurrentView('curriculum')}
              className="hover:text-indigo-600 cursor-pointer transition-colors max-w-[180px] truncate"
            >
              {currentChapter.title}
            </button>
            <span>›</span>
            <span className="font-semibold text-indigo-900 bg-indigo-50/70 px-2.5 py-1 rounded-lg border border-indigo-100 max-w-[220px] truncate">
              {currentProblem.title}
            </span>
            {isCompleted && (
              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <span>✓</span> Solved
              </span>
            )}
          </nav>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setShowHint((prev) => !prev)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all shadow-xs cursor-pointer ${
              showHint
                ? 'bg-amber-500 text-white font-bold ring-2 ring-amber-300'
                : 'bg-amber-50 text-amber-800 border border-amber-200/80 hover:bg-amber-100'
            }`}
            title="Toggle Socratic Hint"
          >
            <span>💡</span>
            <span className="hidden sm:inline">Hints</span>
            <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
              showHint ? 'bg-white text-amber-600' : 'bg-amber-500 text-white'
            }`}>
              1
            </span>
          </button>

          <button
            type="button"
            onClick={handleScrollToFormulas}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/80 hover:bg-indigo-100 transition-all shadow-xs cursor-pointer"
            title="Jump to Useful Formulas"
          >
            <span>📖</span>
            <span className="hidden sm:inline">Formulas</span>
          </button>

          <button
            type="button"
            onClick={() => setCurrentView(currentView === 'curriculum' ? 'workspace' : 'curriculum')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all shadow-xs cursor-pointer ${
              currentView === 'curriculum'
                ? 'bg-indigo-600 text-white font-bold ring-2 ring-indigo-300'
                : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <span>📚</span>
            <span className="hidden md:inline">
              {currentView === 'curriculum' ? 'Back to Problem' : 'All Chapters'}
            </span>
          </button>

          <div className="h-6 w-px bg-slate-200 mx-1"></div>

          {/* User Profile Badge */}
          <div className="flex items-center gap-2 pl-1">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow-xs">
              S
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-xs font-bold text-slate-800 leading-tight">Student</p>
              <p className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Socratic Mode
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* ============================================================== */}
      {/* VIEW 1: FULL-PAGE CURRICULUM HUB (MAIN MENU)                   */}
      {/* ============================================================== */}
      {currentView === 'curriculum' && (
        <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6">
          <CurriculumHubView
            chapters={AVAILABLE_CHAPTERS}
            solvedProblems={solvedProblems}
            onSelectProblem={handleSelectProblemFromHub}
            onBackToWorkspace={() => setCurrentView('workspace')}
            currentProblem={currentProblem}
          />
        </main>
      )}

      {/* ============================================================== */}
      {/* VIEW 2: ACTIVE PROBLEM WORKSPACE / VICTORY                     */}
      {/* ============================================================== */}
      {currentView === 'workspace' && (
        <>
          {/* Error Banner */}
          {loadError && (
            <div className="p-4 bg-rose-50 border-b border-rose-200 text-rose-800 text-xs flex items-center justify-between">
              <span>🔴 Error: {loadError}</span>
              <button
                type="button"
                onClick={() => handleLoadProblem()}
                className="font-bold underline cursor-pointer"
              >
                Retry Loading
              </button>
            </div>
          )}

          {/* If problem is completed and user is not reviewing steps, show Victory Celebration */}
          {isCompleted && !isReviewingSteps ? (
            <main className="flex-1 min-h-0 w-full max-w-4xl mx-auto p-3 sm:p-4 flex flex-col justify-center items-center overflow-y-auto custom-scrollbar">
              <VictoryCelebrationView
                session={session}
                onReviewSteps={() => setIsReviewingSteps(true)}
                onNextProblem={handleNextProblem}
                onStartAgain={handleResetProblem}
                onOpenMainMenu={() => setCurrentView('curriculum')}
              />
            </main>
          ) : (
            <main className="flex-1 min-h-0 w-full max-w-[1720px] mx-auto p-3 sm:p-4 overflow-hidden flex flex-col">
              {/* Banner when reviewing a completed problem */}
              {isCompleted && isReviewingSteps && (
                <div className="mb-3 p-3.5 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-900 flex flex-wrap items-center justify-between gap-3 shadow-xs shrink-0">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">🏆</span>
                    <div>
                      <p className="text-xs font-bold text-emerald-950">Review Mode: Problem Socratically Solved!</p>
                      <p className="text-[11px] text-emerald-700">You are reviewing your verified ledger steps and conversation trail.</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setIsReviewingSteps(false)}
                      className="px-3 py-1.5 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 shadow-xs cursor-pointer flex items-center gap-1.5 transition"
                    >
                      <span>🏆 Back to Victory Celebration</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleNextProblem}
                      className="px-3 py-1.5 rounded-xl bg-white border border-emerald-300 text-emerald-800 text-xs font-bold hover:bg-emerald-100 cursor-pointer flex items-center gap-1.5 transition shadow-2xs"
                    >
                      <span>Next Problem ➔</span>
                    </button>
                  </div>
                </div>
              )}

              {/* 3-Column Socratic Studio Grid (Viewport-Fit: Zero Window Scroll) */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0 h-full items-stretch overflow-hidden">
                
                {/* COLUMN 1: Problem Context & Solution Plan (3 Cols) */}
                <div className="lg:col-span-3 flex flex-col h-full min-h-0 overflow-hidden">
                  <ProblemRoadmapPanel
                    chapter={currentChapter}
                    problem={currentProblem}
                    session={session}
                    isCompleted={isCompleted}
                    totalProblems={totalProblems}
                    problemIndex={currentProblemIndex + 1}
                    formulasOpen={showFormulas}
                    onToggleFormulas={() => setShowFormulas((prev) => !prev)}
                  />
                </div>

                {/* COLUMN 2: Live Solution Notebook (5 Cols) */}
                <div className="lg:col-span-5 flex flex-col h-full min-h-0 overflow-hidden">
                  <LiveSolutionNotebook
                    chapter={currentChapter}
                    problem={currentProblem}
                    session={session}
                    isCompleted={isCompleted}
                  />
                </div>

                {/* COLUMN 3: Socratic Dialogue Stream (4 Cols) */}
                <div className="lg:col-span-4 flex flex-col h-full min-h-0 overflow-hidden">
                  <SocraticChatStream
                    session={session}
                    chapter={currentChapter}
                    history={session?.history || []}
                    stepResult={stepResult}
                    jevMessage={jevMessage}
                    input={input}
                    onInputChange={setInput}
                    onCheckStep={handleCheckStep}
                    onResetProblem={handleResetProblem}
                    isChecking={isChecking}
                    checkButtonText={checkButtonText}
                    isCompleted={isCompleted}
                    showHint={showHint}
                    onToggleHint={() => setShowHint((prev) => !prev)}
                  />
                </div>

              </div>
            </main>
          )}
        </>
      )}

    </div>
  );
}
