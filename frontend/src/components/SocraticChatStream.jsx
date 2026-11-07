import React, { useRef, useEffect, useMemo, useState } from 'react';
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

export default function SocraticChatStream({
  session,
  chapter,
  history = [],
  stepResult,
  jevMessage,
  input,
  onInputChange,
  onCheckStep,
  onResetProblem,
  isChecking,
  checkButtonText,
  isCompleted,
  showHint: externalShowHint,
  onToggleHint: externalToggleHint
}) {
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const [internalShowHint, setInternalShowHint] = useState(false);
  const showHint = externalShowHint !== undefined ? externalShowHint : internalShowHint;
  const toggleHint = externalToggleHint || (() => setInternalShowHint((prev) => !prev));

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
    return [
      { label: '₹', insert: '₹' },
      { label: '%', insert: '%' },
      { label: '=', insert: ' = ' },
      { label: '×', insert: ' \\times ' },
      { label: '÷', insert: ' \\div ' },
      { label: ':', insert: ' : ' },
      { label: '-', insert: ' - ' },
      { label: '+', insert: ' + ' },
    ];
  }, [chapter]);

  // Handle helper chip insertion
  const handleChipClick = (insertStr) => {
    const current = input || '';
    onInputChange(current + insertStr);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Auto-scroll chat to latest message on history change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history, isChecking, jevMessage, showHint]);

  // Initial welcome message from tutor
  const initialPromptText = useMemo(() => {
    if (session?.prompt) return session.prompt;
    return "Hello! I am Ainstein, your Socratic math tutor. Let's solve this problem step-by-step. What information is given in the problem statement?";
  }, [session?.prompt]);

  // Current active hint text
  const currentHintText = useMemo(() => {
    return session?.hint || stepResult?.hint || "Read the question carefully. Break down what is given and what needs to be calculated.";
  }, [session?.hint, stepResult?.hint]);

  // Live KaTeX preview of student's current input
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

  return (
    <div className="flex flex-col bg-white rounded-2xl border border-indigo-100 shadow-xs overflow-hidden h-full min-h-0">
      
      {/* Tutor Header with Illustrated Character */}
      <div className="bg-gradient-to-r from-indigo-700 via-indigo-600 to-purple-700 text-white p-3 shrink-0 flex items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-xl shadow-inner">
              👨‍🏫
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-indigo-700"></span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h2 className="text-xs font-extrabold tracking-tight">Ainstein</h2>
              <span className="text-[9px] font-bold bg-white/20 px-1.5 py-0.5 rounded-full uppercase tracking-wider">AI Guide</span>
            </div>
            <p className="text-[11px] text-indigo-100/90 font-medium leading-none mt-0.5">Your Socratic Math Partner</p>
          </div>
        </div>

        {/* Top actions: Hint & Reset */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleHint}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-white/15 hover:bg-white/25 text-white transition shadow-2xs cursor-pointer"
            title="Toggle Socratic Hint"
          >
            <span>💡</span>
            <span>{showHint ? 'Hide Hint' : 'Hint'}</span>
          </button>
        </div>
      </div>

      {/* Socratic Dialogue Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 min-h-0 p-3 space-y-3 overflow-y-auto custom-scrollbar text-xs bg-slate-50/50"
      >
        {/* Initial Tutor Guidance Bubble */}
        <div className="flex items-start gap-2.5 max-w-[90%]">
          <div className="w-7 h-7 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
            🦉
          </div>
          <div className="bg-white rounded-2xl rounded-tl-xs p-3.5 shadow-xs border border-slate-200/80 space-y-1">
            <p className="text-[11px] font-bold text-indigo-700 uppercase tracking-wider">
              Ainstein Guidance
            </p>
            <p className="text-xs text-slate-800 leading-relaxed font-medium">
              {initialPromptText}
            </p>
          </div>
        </div>

        {/* Conversation History Turns */}
        {history.map((item, idx) => {
          const renderedContent = renderStudentTurn(item.input);
          
          // Verdict classification (Problem 9 Target Fix)
          const isCorrect = item.is_correct || item.verdict === 'ACCEPT' || item.verdict === 'MULTI_STEP_ACCEPT' || item.verdict === 'CONCLUSION_RIGHT';
          const isPartial = item.verdict === 'PARTIAL_EXTRACTION';
          const isMisconception = item.verdict === 'MISCONCEPTION';
          const isWarn = item.verdict === 'IRRELEVANT_TRUE' || item.verdict === 'GARBAGE' || item.verdict === 'APPROACH_ONLY' || item.verdict === 'EXTRACTION_REQUIRED' || item.verdict === 'METHOD_LOCKED';
          const isExtractionPhase = session?.active_node_id === 'given_extraction' || session?.active_node_id === 'goal_extraction' || item.verdict === 'EXTRACTION_REQUIRED' || item.verdict === 'PARTIAL_EXTRACTION';

          const cardStyle = isCorrect
            ? 'bg-emerald-50 border-emerald-300'
            : isPartial
            ? 'bg-sky-50 border-sky-300'
            : isMisconception || isWarn
            ? 'bg-amber-50 border-amber-300'
            : 'bg-rose-50 border-rose-300';

          const headerTextStyle = isCorrect
            ? 'text-emerald-800'
            : isPartial
            ? 'text-sky-900'
            : isMisconception || isWarn
            ? 'text-amber-900'
            : 'text-rose-800';

          const iconText = isCorrect ? '✓' : isPartial ? '📋' : isMisconception ? '💡' : isWarn ? '⚠️' : '✗';

          const titleText = isCorrect
            ? 'Step Verified'
            : isPartial
            ? 'Given Fact Recorded'
            : isMisconception
            ? 'Conceptual Tip'
            : isWarn
            ? 'Clarification Needed'
            : isExtractionPhase
            ? 'Check Problem Details'
            : 'Check Your Calculation';

          const nextQuestion = item.next_prompt || (idx === history.length - 1 && session?.prompt && !isCompleted ? session.prompt : null);

          return (
            <React.Fragment key={idx}>
              {/* Student message bubble */}
              <div className="flex items-start gap-2.5 max-w-[85%] ml-auto flex-row-reverse">
                <div className="w-7 h-7 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
                  👤
                </div>
                <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-xs p-3 shadow-xs">
                  <p className="text-[10px] text-indigo-200 font-semibold uppercase tracking-wider">
                    You (Turn {item.turn || idx + 1})
                  </p>
                  <p
                    className="font-mono text-xs font-bold"
                    dangerouslySetInnerHTML={{ __html: renderedContent }}
                  />
                </div>
              </div>

              {/* Tutor feedback bubble */}
              <div className="flex items-start gap-2.5 max-w-[92%]">
                <div className={`w-7 h-7 rounded-xl text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs ${
                  isCorrect
                    ? 'bg-emerald-600'
                    : isPartial
                    ? 'bg-sky-600'
                    : isMisconception || isWarn
                    ? 'bg-amber-600'
                    : 'bg-rose-600'
                }`}>
                  {iconText}
                </div>
                <div className={`rounded-2xl rounded-tl-xs p-3.5 shadow-xs space-y-2 border ${cardStyle}`}>
                  <div className={`flex items-center gap-1.5 font-bold ${headerTextStyle}`}>
                    <span>{iconText}</span>
                    <span>{titleText}</span>
                  </div>

                  <p className="text-slate-800 leading-relaxed font-medium">
                    {item.feedback ||
                      (isCorrect
                        ? `"${item.input}" — verified!`
                        : 'Review this step carefully and try again.')}
                  </p>

                  {/* Socratic Next Question (prominently asked by the tutor) */}
                  {nextQuestion && (
                    <div className="mt-2 pt-2 border-t border-slate-200/80">
                      <div className="flex items-center gap-1.5 text-indigo-800 font-bold text-[11px] uppercase tracking-wider mb-1">
                        <span>💬</span>
                        <span>Ainstein Asks:</span>
                      </div>
                      <p className="text-slate-900 font-semibold text-xs leading-relaxed">
                        {nextQuestion}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </React.Fragment>
          );
        })}

        {/* Jev Message (if method classification alert) */}
        {jevMessage && (
          <div className="flex items-start gap-2.5 max-w-[90%]">
            <div className="w-7 h-7 rounded-xl bg-amber-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
              ⚠️
            </div>
            <div className="bg-amber-50 border border-amber-300 rounded-2xl rounded-tl-xs p-3.5 shadow-xs space-y-1">
              <p className="font-bold text-amber-900 text-[11px] uppercase tracking-wider">
                {jevMessage.label}
              </p>
              <p className="text-slate-800 leading-relaxed">{jevMessage.message}</p>
            </div>
          </div>
        )}

        {/* Progressive Hint Card */}
        {showHint && (
          <div className="bg-gradient-to-br from-amber-50 to-orange-50/60 rounded-2xl p-3.5 border border-amber-200 shadow-xs space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 font-bold text-amber-900 text-xs">
                <span>💡</span>
                <span>Socratic Guidance &amp; Hint</span>
              </div>
              <span className="text-[10px] font-bold text-amber-700 bg-amber-100/80 px-2 py-0.5 rounded-full">Scaffold</span>
            </div>
            <p className="text-xs text-slate-800 leading-relaxed font-medium">
              {currentHintText}
            </p>
            <div className="flex items-center gap-2 pt-1 border-t border-amber-200/60">
              <button
                type="button"
                onClick={() => {
                  alert(`💡 Detailed Pedagogical Hint:\n\n${currentHintText}\n\nReview the given facts on your notebook and proceed with your calculation.`);
                }}
                className="px-2.5 py-1 rounded-lg bg-white hover:bg-amber-100 text-amber-900 border border-amber-200 font-bold text-[11px] transition shadow-2xs cursor-pointer"
              >
                Another hint ⚡
              </button>
            </div>
          </div>
        )}

        {/* Typing indicator bubble */}
        {isChecking && (
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium pl-2">
            <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>
            <span>Ainstein is verifying your step...</span>
          </div>
        )}
      </div>

      {/* Socratic Math Input & Helper Chips */}
      <div className="p-3.5 bg-white border-t border-slate-200 space-y-2.5">
        
        {/* Mathematical Helper Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs custom-scrollbar">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1">Insert:</span>
          {topicChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleChipClick(chip.insert)}
              className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 font-bold text-slate-700 border border-slate-200 transition cursor-pointer"
            >
              {chip.label}
            </button>
          ))}
        </div>

        {/* Live KaTeX preview of mathematical input */}
        {previewHtml && (
          <div className="px-3 py-1.5 bg-indigo-50/70 border border-indigo-200 rounded-xl text-xs font-mono text-indigo-900 flex items-center gap-2 shadow-2xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500">Live Preview:</span>
            <span dangerouslySetInnerHTML={{ __html: previewHtml }} />
          </div>
        )}

        {/* Input Box with Enter Action */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!isChecking) onCheckStep();
          }}
          className="relative flex items-center"
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            disabled={isChecking || isCompleted}
            placeholder={
              isCompleted
                ? 'Problem solved! Press "Next Problem" to continue.'
                : 'Type your step or response... (e.g. 5% for 1 year)'
            }
            className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-3.5 pr-11 py-2.5 text-xs font-mono-math font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-600 transition disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={isChecking || isCompleted}
            className="absolute right-1.5 p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition shadow-xs disabled:opacity-50 cursor-pointer"
            title="Check Step"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
            </svg>
          </button>
        </form>

        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span>Press Enter ↵ to submit step</span>
          <button
            type="button"
            onClick={onResetProblem}
            className="text-slate-500 hover:text-slate-800 font-semibold cursor-pointer transition"
          >
            ↺ Reset Problem
          </button>
        </div>
      </div>

    </div>
  );
}
