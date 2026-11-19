import React, { useMemo, useState, useRef, useEffect } from 'react';
import katex from 'katex';

function formatLatexString(raw) {
  let text = (raw || '').trim();
  if (!text) return '';
  text = text.replace(/\b(and|or|is|are|to|for|with|of|by|in|whether|the|ratios|proportional)\b/gi, ' \\text{ $1 } ');
  return text
    .replace(/\*/g, ' \\times ')
    .replace(/x(?=\s*\d)/g, ' \\times ')
    .replace(/==/g, ' = ');
}

function renderStudentTurn(input) {
  if (!input) return '';
  const text = input.trim();
  const hasMathEquation = /[=≠+\-*/÷×^\\_]/.test(text);
  const isWordSentence = /^[a-zA-Z0-9\s,.:?!'"()]+$/.test(text) && !/[=≠+\-*/÷×^\\_]/.test(text) && /[a-zA-Z]{3,}/.test(text);

  if (isWordSentence && !hasMathEquation) {
    return text;
  }

  try {
    return katex.renderToString(formatLatexString(text), {
      throwOnError: false,
      displayMode: false
    });
  } catch {
    return text;
  }
}

/**
 * Animated Typewriter Component with Live Gliding Pen Nib Cursor
 */
function TypewriterText({ text, speed = 25, onComplete, cursorSymbol = "✒️", isDraft = false, playSound }) {
  const [displayedLength, setDisplayedLength] = useState(0);
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    setDisplayedLength(0);
    setIsTyping(true);

    if (speed === 0 || !text) {
      setDisplayedLength(text ? text.length : 0);
      setIsTyping(false);
      if (onComplete) onComplete();
      return;
    }

    let current = 0;
    const interval = setInterval(() => {
      current++;
      setDisplayedLength(current);
      if (current % 2 === 0 && playSound) {
        playSound();
      }
      if (current >= text.length) {
        clearInterval(interval);
        setIsTyping(false);
        if (onComplete) onComplete();
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  const visibleText = text ? text.slice(0, displayedLength) : '';

  return (
    <span className="inline-flex items-center flex-wrap">
      <span className={isDraft ? "pencil-draft" : "ink-student"}>{visibleText}</span>
      {isTyping && (
        <span className="pen-cursor text-xl ml-1 select-none pointer-events-none">
          {cursorSymbol}
        </span>
      )}
    </span>
  );
}

export default function LiveSolutionNotebook({
  chapter,
  problem,
  session,
  isCompleted,
  input = '',
  onInputChange,
  onCheckStep,
  onResetProblem,
  isChecking = false,
  checkButtonText = 'Check Step',
  stepResult,
  jevMessage,
  showHint = false,
  onToggleHint
}) {
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const tutorFeedRef = useRef(null);
  const typeSpeed = 20; // smooth, brisk character writing speed
  const [pendingDraft, setPendingDraft] = useState(null);

  // Clear pendingDraft once verification completes
  useEffect(() => {
    if (!isChecking) {
      setPendingDraft(null);
    }
  }, [isChecking]);

  const playPencilSound = () => {};

  const trail = session?.trail || [];
  const history = session?.history || [];
  const text = session?.problem_text || '';

  // Extract date formatted nicely
  const currentDateStr = useMemo(() => {
    const d = new Date();
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }, []);

  // Determine extraction states
  const givenStep = trail.find((t) => t.nodeId === 'given_extraction');
  const goalStep = trail.find((t) => t.nodeId === 'goal_extraction');
  const isGivenActive = session?.active_node_id === 'given_extraction';
  const isGoalActive = session?.active_node_id === 'goal_extraction';
  const isExtractionProblem = isGivenActive || isGoalActive || Boolean(givenStep) || Boolean(goalStep);

  // Givens list
  const givensList = useMemo(() => {
    const list = [];
    if (session?.accumulated_givens && session.accumulated_givens.length > 0) {
      session.accumulated_givens.forEach((g, idx) => {
        list.push({ label: `Given Fact ${idx + 1}`, value: g, verified: true });
      });
    } else if (givenStep) {
      list.push({ label: 'Verified Givens', value: givenStep.input, verified: true });
    } else if (isExtractionProblem) {
      list.push({ label: 'Given Facts', value: 'Pending extraction...', isPending: true });
    } else {
      const numbers = text.match(/\b\d+(?:,\d+)*(?:\.\d+)?%?\b/g);
      if (numbers && numbers.length > 0) {
        list.push({ label: 'Problem Parameters', value: numbers.join(', '), verified: true });
      } else {
        list.push({ label: 'Given Information', value: 'Extracted from problem statement', verified: true });
      }
    }
    return list;
  }, [session, givenStep, isExtractionProblem, text]);

  // Goal data
  const goalData = useMemo(() => {
    if (session?.extracted_goal) {
      return { value: session.extracted_goal, isPending: false };
    }
    if (goalStep) {
      return { value: goalStep.input, isPending: false };
    }
    if (isExtractionProblem) {
      return { value: 'Pending extraction...', isPending: true };
    }
    const findMatch = text.match(/(?:find|calculate|determine|what is|how many|check whether)\s+([^.?\n]+)/i);
    if (findMatch) {
      return { value: findMatch[1].trim(), isPending: false };
    }
    return { value: problem?.title || 'Solve for the required quantity', isPending: false };
  }, [session, goalStep, isExtractionProblem, text, problem]);

  // Calculation steps
  const calcSteps = trail.filter(
    (t) => t.nodeId !== 'given_extraction' && t.nodeId !== 'goal_extraction' && t.nodeId !== 'start'
  );

  // Section visibility:
  // 1. Given: always visible
  // 2. To Find: visible once givens are verified OR direct problem
  const isToFindVisible = !isGivenActive || Boolean(givenStep) || !isExtractionProblem;
  // 3. Calculation: visible once both givens and goal are verified OR direct problem
  const isCalcVisible = (!isGivenActive && !isGoalActive) || calcSteps.length > 0 || !isExtractionProblem;

  // Track latest verified step for typewriter animation
  const [animatingStepInput, setAnimatingStepInput] = useState(null);
  const prevTrailLengthRef = useRef(trail.length);

  // Dual-mode input: Step-by-Step vs Full Working
  const [inputMode, setInputMode] = useState('single'); // 'single' | 'multi'

  useEffect(() => {
    if (trail.length > prevTrailLengthRef.current) {
      const latest = trail[trail.length - 1];
      if (latest && latest.input) {
        setAnimatingStepInput(latest.input);
      }
    }
    prevTrailLengthRef.current = trail.length;
  }, [trail.length]);

  // =========================================================================
  // UNIVERSAL ERROR DETECTION ACROSS ALL SECTIONS
  // =========================================================================
  const isErrorState = useMemo(() => {
    if (jevMessage) return true;
    if (!stepResult) return false;
    const verdict = (stepResult.verdict || '').toUpperCase();
    const isVerdictWrong = [
      'MISCONCEPTION',
      'WRONG_CLAIM',
      'EXTRACTION_REQUIRED',
      'METHOD_LOCKED',
      'CONCLUSION_WRONG',
      'GARBAGE',
      'UNPARSED'
    ].includes(verdict);
    const hasFailStreak = (stepResult.fail_streak || 0) > 0;
    const isExplicitlyWrong = stepResult.is_correct === false;
    return isVerdictWrong || hasFailStreak || isExplicitlyWrong;
  }, [stepResult, jevMessage]);

  const lastAttemptedInput = useMemo(() => {
    if (stepResult?.parsed_input) return stepResult.parsed_input;
    if (stepResult?.attempted_input) return stepResult.attempted_input;
    if (history && history.length > 0) {
      const lastTurn = [...history].reverse().find(t => t.input && (!t.is_correct || isErrorState));
      if (lastTurn) return lastTurn.input;
      const anyLastTurn = [...history].reverse().find(t => t.input);
      if (anyLastTurn && isErrorState) return anyLastTurn.input;
    }
    return pendingDraft || null;
  }, [stepResult, history, isErrorState, pendingDraft]);

  // Active error feedback message from tutor
  const tutorErrorMessage = useMemo(() => {
    if (jevMessage?.message) return jevMessage.message;
    if (stepResult?.feedback_message) return stepResult.feedback_message;
    if (stepResult?.explanation) return stepResult.explanation;
    if (stepResult?.next_prompt) return stepResult.next_prompt;
    return "Check your calculation or extraction carefully!";
  }, [jevMessage, stepResult]);

  // Dynamic context-aware helper chips based on chapter
  const topicChips = useMemo(() => {
    const id = chapter?.id || '';
    if (id === 'squares-and-cubes') {
      return [
        { label: '³√', insert: '\\sqrt[3]{}' },
        { label: '√', insert: '\\sqrt{}' },
        { label: '²', insert: '^2' },
        { label: '³', insert: '^3' },
        { label: '×', insert: ' \\times ' },
        { label: '=', insert: ' = ' },
        { label: '÷', insert: ' \\div ' },
      ];
    }
    if (id === 'percentages') {
      return [
        { label: '₹', insert: '₹' },
        { label: '%', insert: '%' },
        { label: '=', insert: ' = ' },
        { label: '×', insert: ' \\times ' },
        { label: '÷', insert: ' \\div ' },
        { label: '+', insert: ' + ' },
        { label: '-', insert: ' - ' },
      ];
    }
    if (id === 'power-play') {
      return [
        { label: '^', insert: '^' },
        { label: '×', insert: ' \\times ' },
        { label: '÷', insert: ' \\div ' },
        { label: '=', insert: ' = ' },
        { label: '⁻¹', insert: '^{-1}' },
        { label: '²', insert: '^2' },
      ];
    }
    if (id === 'real-numbers') {
      return [
        { label: '²', insert: '^2' },
        { label: '³', insert: '^3' },
        { label: '×', insert: ' × ' },
        { label: '÷', insert: ' ÷ ' },
        { label: '=', insert: ' = ' },
        { label: 'HCF', insert: 'HCF' },
        { label: 'LCM', insert: 'LCM' },
      ];
    }
    if (id === 'polynomials') {
      return [
        { label: 'x²', insert: 'x^2' },
        { label: 'α', insert: 'α' },
        { label: 'β', insert: 'β' },
        { label: '±', insert: '±' },
        { label: '√', insert: '√' },
        { label: ' = ', insert: ' = ' },
        { label: 'D = b² - 4ac', insert: 'D = b^2 - 4ac' },
      ];
    }
    if (id === 'circles' || id === 'surface-areas-and-volumes') {
      return [
        { label: 'π', insert: 'π' },
        { label: 'r²', insert: 'r^2' },
        { label: 'r³', insert: 'r^3' },
        { label: 'cm²', insert: 'cm^2' },
        { label: 'cm³', insert: 'cm^3' },
        { label: 'kg', insert: 'kg' },
        { label: 'g', insert: 'g' },
        { label: '=', insert: ' = ' },
      ];
    }
    if (id === 'probability') {
      return [
        { label: 'P(E)', insert: 'P(E)' },
        { label: 'P(not E)', insert: 'P(not E)' },
        { label: '≤', insert: '≤' },
        { label: '≥', insert: '≥' },
        { label: '1 - ', insert: '1 - ' },
        { label: '=', insert: ' = ' },
      ];
    }
    return [
      { label: 'x', insert: 'x' },
      { label: '5x', insert: '5x' },
      { label: ' = ', insert: ' = ' },
      { label: '+ 6', insert: ' + 6' },
      { label: '3(x + 6)', insert: '3(x + 6)' },
      { label: 'x = 6', insert: 'x = 6' },
      { label: '₹', insert: '₹' },
      { label: '%', insert: '%' },
    ];
  }, [chapter]);

  const handleChipClick = (insertStr) => {
    const current = input || '';
    if (onInputChange) {
      onInputChange(current + (current && !current.endsWith(' ') ? ' ' : '') + insertStr);
    }
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Live KaTeX preview of mathematical input
  const previewHtml = useMemo(() => {
    const raw = (input || '').trim();
    if (!raw) return null;
    const hasMath = /[=≠+\-*/÷×^\\_:0-9]/.test(raw);
    if (!hasMath) return null;
    try {
      return katex.renderToString(formatLatexString(raw), {
        throwOnError: false,
        displayMode: false
      });
    } catch {
      return null;
    }
  }, [input]);

  // Current active hint text with comprehensive resolution
  const currentHintText = useMemo(() => {
    if (stepResult?.hint) return stepResult.hint;
    if (session?.hint) return session.hint;
    if (Array.isArray(session?.hints) && session.hints.length > 0) return session.hints[0];
    return "Focus on the key relationships given in the problem statement.";
  }, [session?.hint, session?.hints, stepResult?.hint]);

  // Auto-scroll notebook canvas: reset to top when switching problems
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [problem?.uuid, problem?.id]);

  // Auto-scroll tutor feed to bottom when history or state updates
  useEffect(() => {
    if (tutorFeedRef.current) {
      tutorFeedRef.current.scrollTop = tutorFeedRef.current.scrollHeight;
    }
  }, [history.length, isErrorState, jevMessage, isChecking, isCompleted, showHint]);

  return (
    <div className="flex-1 min-w-0 flex flex-col lg:flex-row h-full min-h-0 items-stretch overflow-hidden">
      
      {/* ============================================================== */}
      {/* PANEL 2: NOTEBOOK WRITING STUDIO (EXPANSIVE FLEX-1)            */}
      {/* ============================================================== */}
      <section className="flex-1 min-w-0 bg-white lg:border-r border-slate-200 flex flex-col h-full min-h-0 overflow-hidden">
        
        {/* Ruled School Notebook Paper (Clean, Uncluttered, Max Width) */}
        <div
          ref={scrollRef}
          className="notebook-clean-sheet flex-1 min-h-0 custom-scrollbar overflow-y-auto text-slate-900 pt-0 pr-3.5 pb-3.5 pl-16 sm:pl-18 relative"
        >
          {/* Top Header Stamp (Locked to exact 30px first notebook line) */}
          <div className="h-[30px] border-b border-slate-300/60 flex items-center justify-between text-[11px] text-slate-500 font-mono-math mb-1">
            <div className="flex items-center gap-3">
              <span className="font-bold text-slate-600">Date: {currentDateStr}</span>
              <span className="text-slate-300">•</span>
              <span className="font-bold text-indigo-900">
                {chapter?.title ? `${chapter.title} • Class ${chapter.grade || session?.grade || 8}` : `Mathematics • Class ${session?.grade || 8}`}
              </span>
            </div>
            <span className="font-semibold text-slate-600 truncate max-w-[340px]">
              {problem?.title || 'Algebra Play'}
            </span>
          </div>

          {/* SECTION 1: GIVEN */}
          <div className="space-y-0.5 mb-2.5">
            <h3 className="font-pen text-xl sm:text-2xl font-extrabold text-indigo-950 flex items-center gap-2">
              <span>Given :</span>
              {isGivenActive && (
                <span className="text-[10px] font-sans font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.2 rounded-md border border-indigo-200/60">
                  Active Phase
                </span>
              )}
            </h3>

            <div className="space-y-0.5 font-pen text-base sm:text-lg ink-student">
              {givensList.map((g, idx) => (
                <div key={idx} className="flex items-center gap-2.5 flex-wrap">
                  <span className="font-bold text-indigo-900">• {g.label}</span>
                  <span>=</span>
                  {g.isPending ? (
                    <span className="text-slate-400 italic font-sans text-xs flex items-center gap-1.5">
                      <span>Enter the problem's given facts below...</span>
                    </span>
                  ) : animatingStepInput && g.value === animatingStepInput ? (
                    <span className="highlight-marker font-bold text-indigo-950">
                      <TypewriterText
                        text={g.value}
                        speed={typeSpeed}
                        playSound={playPencilSound}
                        onComplete={() => setAnimatingStepInput(null)}
                      />
                    </span>
                  ) : (
                    <span className="highlight-marker font-bold text-indigo-950">
                      {g.value}
                    </span>
                  )}
                </div>
              ))}

              {/* Live Drafting Line while Pen is Writing */}
              {isGivenActive && isChecking && pendingDraft && (
                <div className="flex items-center gap-2.5 animate-stage-appear pt-0.5">
                  <span className="font-mono-math text-[11px] text-indigo-500 font-bold">Drafting:</span>
                  <TypewriterText
                    text={pendingDraft}
                    speed={typeSpeed}
                    playSound={playPencilSound}
                    cursorSymbol="✒️"
                    isDraft={true}
                  />
                </div>
              )}

              {/* Error Strike-Through in Given Phase */}
              {isGivenActive && isErrorState && lastAttemptedInput && (
                <div className="space-y-1 animate-stage-appear pt-0.5">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-mono-math text-[11px] text-rose-500 font-bold">Draft:</span>
                    <span className="strikethrough-line text-lg sm:text-xl text-slate-400 font-pen tracking-wide font-medium">
                      {lastAttemptedInput}
                    </span>
                    <span className="text-[10px] font-sans font-bold text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.2 rounded-full ml-1">
                      ✗ crossed out
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* SECTION 2: TO FIND */}
          {isToFindVisible && (
            <div className="space-y-0.5 mb-2.5 animate-stage-appear">
              <h3 className="font-pen text-xl sm:text-2xl font-extrabold text-indigo-950 flex items-center gap-2">
                <span>To Find :</span>
                {isGoalActive && (
                  <span className="text-[10px] font-sans font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.2 rounded-md border border-indigo-200/60">
                    Active Phase
                  </span>
                )}
              </h3>

              <div className="font-pen text-base sm:text-lg ink-student flex items-center gap-2.5 flex-wrap">
                <span className="font-bold text-indigo-900">• Required Value</span>
                <span>=</span>
                {goalData.isPending ? (
                  <span className="text-slate-400 italic font-sans text-xs flex items-center gap-1.5">
                    <span>State what needs to be solved...</span>
                  </span>
                ) : animatingStepInput && goalData.value === animatingStepInput ? (
                  <span className="px-2.5 py-0.2 rounded-lg bg-indigo-50/70 border border-indigo-200/70 text-indigo-950 font-bold">
                    <TypewriterText
                      text={goalData.value}
                      speed={typeSpeed}
                      playSound={playPencilSound}
                      onComplete={() => setAnimatingStepInput(null)}
                    />
                  </span>
                ) : (
                  <span className="px-2.5 py-0.2 rounded-lg bg-indigo-50/70 border border-indigo-200/70 text-indigo-950 font-bold">
                    {goalData.value}
                  </span>
                )}
              </div>

              {/* Live Drafting Line while Pen is Writing */}
              {isGoalActive && isChecking && pendingDraft && (
                <div className="flex items-center gap-2.5 animate-stage-appear pt-0.5">
                  <span className="font-mono-math text-[11px] text-indigo-500 font-bold">Drafting:</span>
                  <TypewriterText
                    text={pendingDraft}
                    speed={typeSpeed}
                    playSound={playPencilSound}
                    cursorSymbol="✒️"
                    isDraft={true}
                  />
                </div>
              )}

              {/* Error Strike-Through in To Find Phase */}
              {isGoalActive && isErrorState && lastAttemptedInput && (
                <div className="space-y-1 animate-stage-appear pt-0.5">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-mono-math text-[11px] text-rose-500 font-bold">Draft:</span>
                    <span className="strikethrough-line text-lg sm:text-xl text-slate-400 font-pen tracking-wide font-medium">
                      {lastAttemptedInput}
                    </span>
                    <span className="text-[10px] font-sans font-bold text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.2 rounded-full ml-1">
                      ✗ crossed out
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SECTION 3: CALCULATION */}
          {isCalcVisible && (
            <div className="space-y-1 animate-stage-appear">
              <h3 className="font-pen text-xl sm:text-2xl font-extrabold text-indigo-950 flex items-center gap-2">
                <span>Calculation :</span>
                <span className="text-[10px] font-sans font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.2 rounded-md border border-indigo-200/60">
                  Step-by-Step Proof
                </span>
              </h3>

              <div className="space-y-1.5 font-pen text-base sm:text-lg ink-student">
                {/* Render Verified Steps Line by Line */}
                {calcSteps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-3 flex-wrap">
                    <span className="font-mono-math text-[11px] text-slate-400 font-bold">Step {idx + 1}:</span>
                    {animatingStepInput && step.input === animatingStepInput ? (
                      <span className="bg-emerald-50 border border-emerald-200 text-emerald-950 font-bold px-2 py-0.2 rounded font-mono-math text-xs sm:text-sm">
                        <TypewriterText
                          text={step.input}
                          speed={typeSpeed}
                          playSound={playPencilSound}
                          onComplete={() => setAnimatingStepInput(null)}
                        />
                      </span>
                    ) : (
                      <span
                        className="bg-emerald-50 border border-emerald-200 text-emerald-950 font-bold px-2 py-0.2 rounded font-mono-math text-xs sm:text-sm"
                        dangerouslySetInnerHTML={{ __html: renderStudentTurn(step.input) }}
                      />
                    )}
                  </div>
                ))}

                {/* Live Drafting Line while Pen is Writing */}
                {!isGivenActive && !isGoalActive && isChecking && pendingDraft && (
                  <div className="flex items-center gap-3 animate-stage-appear pt-0.5">
                    <span className="font-mono-math text-[11px] text-indigo-500 font-bold">
                      Step {calcSteps.length + 1} (Drafting):
                    </span>
                    <TypewriterText
                      text={pendingDraft}
                      speed={typeSpeed}
                      playSound={playPencilSound}
                      cursorSymbol="✒️"
                      isDraft={true}
                    />
                  </div>
                )}

                {/* STRIKE-THROUGH ON WRONG INPUT / MISCONCEPTION */}
                {!isGivenActive && !isGoalActive && isErrorState && lastAttemptedInput && (
                  <div className="space-y-1 animate-stage-appear pt-0.5">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-mono-math text-[11px] text-rose-500 font-bold">Draft:</span>
                      <span className="strikethrough-line text-lg sm:text-xl text-slate-400 font-pen tracking-wide font-medium">
                        {lastAttemptedInput}
                      </span>
                      <span className="text-[10px] font-sans font-bold text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.2 rounded-full ml-1">
                        ✗ crossed out
                      </span>
                    </div>
                  </div>
                )}

                {/* If waiting for next calculation step without error */}
                {!isCompleted && !isErrorState && !isGivenActive && !isGoalActive && !isChecking && (
                  <div className="flex items-center gap-2.5 text-slate-400 italic pt-0.5">
                    <span className="font-mono-math text-[11px] text-slate-400 font-bold not-italic">
                      Step {calcSteps.length + 1}:
                    </span>
                    <span className="text-xs">write your next step onto the paper below...</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SECTION 4: CONCLUSION */}
          {isCompleted && (
            <div className="pt-1 animate-stage-appear">
              <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xl text-emerald-950 flex items-center gap-3 shadow-xs">
                <span className="text-2xl">🏆</span>
                <div>
                  <p className="font-pen text-2xl font-bold text-emerald-800 leading-tight">
                    Q.E.D. • Problem Solved!
                  </p>
                  <p className="font-pen text-lg text-emerald-700">
                    Every algebraic step proved rigorously. Well done!
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ============================================================== */}
        {/* DOCKED PEN INPUT CONSOLE (STRICTLY UNDER NOTEBOOK ONLY!)       */}
        {/* ============================================================== */}
        <div id="notebook-input-dock" className="border-t border-slate-200 bg-white px-3.5 py-1.5 shrink-0 space-y-1 shadow-2xs">
          
          {/* Math Helper Chips Tray + Input Mode Toggle */}
          <div className="flex items-center justify-between gap-2 overflow-x-auto min-w-0 shrink-0 custom-scrollbar">
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400 shrink-0">Insert:</span>
              <div className="flex items-center gap-1">
                {topicChips.map((chip, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleChipClick(chip.insert)}
                    className="px-1.5 py-0.2 rounded bg-slate-50 hover:bg-indigo-50 hover:text-indigo-700 font-bold text-slate-700 border border-slate-200 text-[10px] transition cursor-pointer"
                  >
                    {chip.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Mode Switcher */}
            <div className="flex items-center gap-0.5 bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-[10px] shrink-0 ml-auto">
              <button
                type="button"
                onClick={() => setInputMode('single')}
                className={`px-2 py-0.5 rounded font-bold transition cursor-pointer ${
                  inputMode === 'single'
                    ? 'bg-white text-indigo-700 shadow-2xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
                title="Single step mode with immediate tutor guidance"
              >
                Step-by-Step
              </button>
              <button
                type="button"
                onClick={() => setInputMode('multi')}
                className={`px-2 py-0.5 rounded font-bold transition cursor-pointer ${
                  inputMode === 'multi'
                    ? 'bg-white text-indigo-700 shadow-2xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
                title="Multi-line mode: write your plan and full working line by line"
              >
                Full Working 📝
              </button>
            </div>
          </div>

          {/* Live KaTeX preview of mathematical input (if any) */}
          {previewHtml && (
            <div className="px-2.5 py-0.5 bg-indigo-50/70 border border-indigo-200 rounded-lg text-xs font-mono text-indigo-900 flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500">Preview:</span>
              <span dangerouslySetInnerHTML={{ __html: previewHtml }} />
            </div>
          )}

          {/* ROW 2: Input Field + Submit Button + Inline Controls */}
          {inputMode === 'single' ? (
            <div className="flex items-center gap-2">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const trimmed = (input || '').trim();
                  if (!trimmed || isChecking) return;
                  setPendingDraft(trimmed);
                  playPencilSound();
                  if (onCheckStep) {
                    onCheckStep();
                  }
                }}
                className="relative flex-1 flex items-center min-w-0"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => onInputChange && onInputChange(e.target.value)}
                  disabled={isChecking || isCompleted}
                  placeholder={
                    isCompleted
                      ? 'Problem solved! Press Next Problem to continue.'
                      : 'Type your algebraic step or extraction here...'
                  }
                  className="w-full bg-slate-50 border border-slate-300 focus:border-indigo-600 focus:bg-white rounded-lg pl-3 pr-20 py-1.5 text-xs font-mono-math font-medium text-slate-900 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 transition shadow-2xs disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={isChecking || isCompleted}
                  className="absolute right-1 px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-[11px] shadow-xs transition cursor-pointer flex items-center justify-center gap-1 disabled:opacity-50"
                  title="Write on Notebook (Submit)"
                >
                  <span>{isChecking ? 'Writing...' : 'Write'}</span>
                </button>
              </form>

              {onResetProblem && (
                <button
                  type="button"
                  onClick={onResetProblem}
                  className="hover:text-slate-800 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 px-2 py-1 rounded transition cursor-pointer shrink-0"
                  title="Reset this problem paper"
                >
                  ↺ Reset
                </button>
              )}
            </div>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const trimmed = (input || '').trim();
                if (!trimmed || isChecking) return;
                setPendingDraft(trimmed.split('\n')[0]);
                playPencilSound();
                if (onCheckStep) {
                  onCheckStep();
                }
              }}
              className="space-y-1.5"
            >
              <div className="relative">
                <textarea
                  rows={4}
                  value={input}
                  onChange={(e) => onInputChange && onInputChange(e.target.value)}
                  disabled={isChecking || isCompleted}
                  placeholder="Write your plan and working line by line:&#10;e.g.&#10;Givens: ...&#10;Plan: factorise the quadratic&#10;x² - 5x + 6 = 0&#10;(x - 2)(x - 3) = 0&#10;x = 2 or x = 3"
                  className="w-full bg-slate-50 border border-slate-300 focus:border-indigo-600 focus:bg-white rounded-lg p-2.5 text-xs font-mono-math font-medium text-slate-900 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 transition shadow-2xs disabled:opacity-60 resize-y min-h-[80px]"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                      e.preventDefault();
                      const trimmed = (input || '').trim();
                      if (!trimmed || isChecking) return;
                      setPendingDraft(trimmed.split('\n')[0]);
                      playPencilSound();
                      if (onCheckStep) {
                        onCheckStep();
                      }
                    }
                  }}
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-medium italic">
                  Press <kbd className="px-1 py-0.2 bg-slate-100 border border-slate-300 rounded text-[9px] not-italic font-mono">Ctrl + Enter</kbd> to evaluate full working
                </span>
                <div className="flex items-center gap-2">
                  {onResetProblem && (
                    <button
                      type="button"
                      onClick={onResetProblem}
                      className="hover:text-slate-800 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 px-2 py-0.5 rounded transition cursor-pointer"
                    >
                      ↺ Reset
                    </button>
                  )}
                  <button
                    type="submit"
                    disabled={isChecking || isCompleted}
                    className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-[11px] shadow-xs transition cursor-pointer flex items-center gap-1 disabled:opacity-50"
                  >
                    <span>{isChecking ? 'Checking Working...' : 'Check Full Working'}</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>

      </section>

      {/* ============================================================== */}
      {/* PANEL 3: DEDICATED AINSTEIN SOCRATIC DIALOGUE (OPTION 2 BUBBLES) */}
      {/* ============================================================== */}
      <aside className="w-full lg:w-[290px] shrink-0 bg-white flex flex-col h-full min-h-0 overflow-hidden border-l border-slate-200">
        
        {/* Socratic Dialogue Header */}
        <div className="bg-gradient-to-r from-indigo-700 to-purple-700 text-white px-3.5 py-2.5 shrink-0 flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <span className="text-base">🦉</span>
            <div>
              <h2 className="text-xs font-bold tracking-tight">Socratic Dialogue</h2>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            {onToggleHint && (
              <button
                type="button"
                onClick={onToggleHint}
                className={`px-2 py-0.5 rounded-full text-[9px] font-bold flex items-center gap-1 cursor-pointer transition ${
                  showHint
                    ? 'bg-amber-400 text-amber-950 shadow-xs'
                    : 'bg-white/20 hover:bg-white/30 text-amber-200 border border-white/20'
                }`}
                title="Toggle Socratic Clue"
              >
                <span>💡</span>
                <span>{showHint ? 'Hide Clue' : 'Clue'}</span>
              </button>
            )}
            <span className="text-[10px] font-mono text-indigo-100 bg-white/20 px-2 py-0.5 rounded-full">
              Stream
            </span>
          </div>
        </div>

        {/* Chat Stream Area (Natural bubbles, zero nested boxes) */}
        <div
          ref={tutorFeedRef}
          id="tutor-feed"
          className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-3 bg-slate-50/60"
        >
          {/* Opening Turn #0 Bubble if History is Empty */}
          {history.length === 0 && (
            <div className="flex items-start gap-2 max-w-[90%] animate-stage-appear">
              <div className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs">
                A
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-xs p-2.5 text-xs text-slate-800 shadow-2xs leading-relaxed">
                {session?.prompt || 'Read the problem statement carefully. What is given or what is our first step?'}
              </div>
            </div>
          )}

          {/* Conversational Turns in History */}
          {history.map((turn, idx) => (
            <div key={idx} className="space-y-2">
              {/* Student Bubble (Right aligned) */}
              {turn.input && (
                <div className="flex items-start gap-2 max-w-[85%] ml-auto flex-row-reverse animate-stage-appear">
                  <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs">
                    You
                  </div>
                  <div
                    className={`rounded-2xl rounded-tr-xs p-2.5 text-xs shadow-2xs font-mono-math break-words ${
                      turn.is_correct
                        ? 'bg-indigo-600 text-white'
                        : 'bg-rose-600 text-white line-through opacity-90'
                    }`}
                  >
                    {turn.input}
                  </div>
                </div>
              )}

              {/* Tutor Response Bubble (Left aligned) */}
              <div className={`flex items-start gap-2 ${turn.is_correct ? 'max-w-[90%]' : 'max-w-[92%]'} animate-stage-appear`}>
                <div
                  className={`w-6 h-6 rounded-full text-white flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs ${
                    turn.is_correct ? 'bg-emerald-600' : 'bg-amber-500'
                  }`}
                >
                  {turn.is_correct ? '✓' : '💡'}
                </div>
                <div
                  className={`rounded-2xl rounded-tl-xs p-2.5 text-xs shadow-2xs space-y-1.5 ${
                    turn.is_correct
                      ? 'bg-emerald-50 border border-emerald-200 text-emerald-950'
                      : 'bg-amber-50 border border-amber-200 text-amber-950'
                  }`}
                >
                  <p className="leading-relaxed">
                    {turn.feedback || turn.feedback_message || (turn.is_correct ? 'Step verified!' : "Let's review this carefully.")}
                  </p>
                  {turn.next_prompt && !isCompleted && (
                    <div
                      className={`pt-1.5 border-t text-[11px] font-bold text-indigo-950 ${
                        turn.is_correct ? 'border-emerald-200' : 'border-amber-200'
                      }`}
                    >
                      👉 {turn.next_prompt}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Active Error State (if error is active and not already captured in the latest turn) */}
          {isErrorState && (
            history.length === 0 || history[history.length - 1]?.is_correct !== false
          ) && (
            <div className="flex items-start gap-2 max-w-[92%] animate-stage-appear">
              <div className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs">
                ⚠️
              </div>
              <div className="bg-rose-50 border border-rose-200 rounded-2xl rounded-tl-xs p-2.5 text-xs text-rose-950 shadow-2xs space-y-1.5">
                <p className="font-semibold">{tutorErrorMessage}</p>
                {session?.prompt && (
                  <div className="pt-1.5 border-t border-rose-200 text-indigo-950 font-bold text-[11px]">
                    👉 {session.prompt}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Active Next Prompt Bubble (if not completed and not already shown in the last turn bubble) */}
          {!isCompleted && !isErrorState && session?.prompt && (
            history.length > 0 &&
            history[history.length - 1]?.next_prompt !== session.prompt
          ) && (
            <div className="flex items-start gap-2 max-w-[90%] animate-stage-appear">
              <div className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs">
                🎯
              </div>
              <div className="bg-indigo-50 border border-indigo-200 rounded-2xl rounded-tl-xs p-2.5 text-xs text-indigo-950 shadow-2xs font-semibold">
                👉 {session.prompt}
              </div>
            </div>
          )}

          {/* Socratic Clue Bubble (Toggled On-Demand) */}
          {showHint && (
            <div className="flex items-start gap-2 max-w-[92%] animate-stage-appear">
              <div className="w-6 h-6 rounded-full bg-amber-500 text-white flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs">
                💡
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded-2xl rounded-tl-xs p-2.5 text-xs text-amber-950 shadow-2xs space-y-1">
                <div className="flex items-center justify-between text-[10px] font-bold text-amber-900">
                  <span>Socratic Clue</span>
                  <span className="text-[9px] bg-amber-200/60 text-amber-900 px-1.5 py-0.2 rounded font-mono">Scaffold</span>
                </div>
                <p className="leading-relaxed font-medium">{currentHintText}</p>
              </div>
            </div>
          )}

          {/* Jev Method Router Bubble */}
          {jevMessage && (
            <div className="flex items-start gap-2 max-w-[92%] animate-stage-appear">
              <div className="w-6 h-6 rounded-full bg-amber-500 text-white flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs">
                🤖
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded-2xl rounded-tl-xs p-2.5 text-xs text-amber-950 shadow-2xs space-y-1">
                <div className="flex items-center justify-between text-[10px] font-bold text-amber-900">
                  <span>Jev Method Router</span>
                  <span className="text-[9px] font-bold text-amber-800 bg-white px-1.5 py-0.2 rounded border border-amber-200">
                    {jevMessage.label || 'Notice'}
                  </span>
                </div>
                <p className="leading-relaxed">{jevMessage.message}</p>
              </div>
            </div>
          )}

          {/* Completion Celebration Bubble */}
          {isCompleted && (
            <div className="flex items-start gap-2 max-w-[95%] animate-badge-pop">
              <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] shrink-0 font-bold shadow-2xs">
                🏆
              </div>
              <div className="bg-emerald-50 border border-emerald-300 rounded-2xl rounded-tl-xs p-2.5 text-xs text-emerald-950 shadow-2xs space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-emerald-800 text-xs">
                  <span>★ Problem Completed!</span>
                </div>
                <p className="font-medium text-emerald-950">
                  All algebraic steps verified successfully. Excellent work!
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Panel Footer: Stream Status & Jump to Latest */}
        <div className="p-2 bg-white border-t border-slate-200 flex items-center justify-between px-3 text-[10px] text-slate-500 shrink-0">
          <span className="font-medium text-slate-400">Conversational Stream</span>
          <button
            type="button"
            onClick={() => {
              if (tutorFeedRef.current) {
                tutorFeedRef.current.scrollTop = tutorFeedRef.current.scrollHeight;
              }
            }}
            className="text-indigo-600 hover:text-indigo-800 font-bold text-[10px] cursor-pointer"
          >
            Jump to Latest ▼
          </button>
        </div>

      </aside>

    </div>
  );
}
