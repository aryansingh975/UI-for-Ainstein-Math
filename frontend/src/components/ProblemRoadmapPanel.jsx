import React from 'react';

export default function ProblemRoadmapPanel({
  chapter,
  problem,
  session,
  isCompleted,
  totalProblems = 4,
  problemIndex = 1,
  solvedProblems = new Set(),
  onSelectProblem
}) {
  const trail = session?.trail || [];
  const history = session?.history || [];
  const hasStarted = trail.length > 0 || history.length > 0;
  const chapterProblems = chapter?.problems || [];

  const givenStep = trail.find((t) => t.nodeId === 'given_extraction');
  const goalStep = trail.find((t) => t.nodeId === 'goal_extraction');
  const hasExtractedGivens = Boolean(givenStep);
  const hasExtractedGoal = Boolean(goalStep);

  // Active step calculation
  const activeNodeId = session?.active_node_id || '';
  const isGivenActive = activeNodeId === 'given_extraction';
  const isGoalActive = activeNodeId === 'goal_extraction';
  const isConclActive = activeNodeId.includes('conclusion') || session?.next_is_conclusion;
  const isCalcActive = !isGivenActive && !isGoalActive && !isConclActive && !isCompleted;

  return (
    <div className="space-y-2.5 flex flex-col h-full min-h-0">

      {/* Vertical Solution Plan Stepper (Slim 200px Edition) */}
      <div className="bg-white rounded-xl p-2.5 border border-indigo-100 shadow-xs shrink-0 flex flex-col">
        <div className="flex items-center justify-between mb-1.5 shrink-0">
          <h2 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1">
            <span className="text-indigo-600">🎯</span> Roadmap
          </h2>
          <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">
            Q{problemIndex}/{totalProblems}
          </span>
        </div>

        <div className="space-y-1 relative pr-0.5">
          {/* Continuous vertical timeline line */}
          <div className="absolute left-2.5 top-2.5 bottom-2.5 w-0.5 bg-slate-200 -z-0"></div>

          {/* Step 1: Understand Problem */}
          <div className={`flex items-center gap-2 relative z-10 p-1 rounded-lg transition-all ${
            !hasStarted ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shadow-xs shrink-0 ${
              hasStarted
                ? 'bg-emerald-600 text-white'
                : 'bg-indigo-600 text-white animate-pulse'
            }`}>
              {hasStarted ? '✓' : '1'}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <p className={`text-[11px] font-bold truncate ${!hasStarted ? 'text-indigo-900' : 'text-slate-800'}`}>
                  Understand
                </p>
                {!hasStarted && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
            </div>
          </div>

          {/* Step 2: Extract Givens */}
          <div className={`flex items-center gap-2 relative z-10 p-1 rounded-lg transition-all ${
            isGivenActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shadow-xs shrink-0 ${
              hasExtractedGivens
                ? 'bg-emerald-600 text-white'
                : isGivenActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {hasExtractedGivens ? '✓' : '2'}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <p className={`text-[11px] font-bold truncate ${isGivenActive ? 'text-indigo-900' : 'text-slate-800'}`}>
                  Givens
                </p>
                {isGivenActive && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
            </div>
          </div>

          {/* Step 3: State Goal */}
          <div className={`flex items-center gap-2 relative z-10 p-1 rounded-lg transition-all ${
            isGoalActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shadow-xs shrink-0 ${
              hasExtractedGoal
                ? 'bg-emerald-600 text-white'
                : isGoalActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {hasExtractedGoal ? '✓' : '3'}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <p className={`text-[11px] font-bold truncate ${isGoalActive ? 'text-indigo-900' : 'text-slate-800'}`}>
                  To Find
                </p>
                {isGoalActive && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
            </div>
          </div>

          {/* Step 4: Mathematical Steps */}
          <div className={`flex items-center gap-2 relative z-10 p-1 rounded-lg transition-all ${
            isCalcActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shadow-xs shrink-0 ${
              isCompleted
                ? 'bg-emerald-600 text-white'
                : isCalcActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {isCompleted ? '✓' : '4'}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1">
                <p className={`text-[11px] font-bold truncate ${isCalcActive ? 'text-indigo-900' : 'text-slate-800'}`}>
                  Math Steps
                </p>
                {isCalcActive && <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
            </div>
          </div>

          {/* Step 5: Final Conclusion */}
          <div className={`flex items-center gap-2 relative z-10 p-1 rounded-lg transition-all ${
            isConclActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shadow-xs shrink-0 ${
              isCompleted
                ? 'bg-emerald-600 text-white'
                : isConclActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {isCompleted ? '✓' : '5'}
            </div>
            <div className="min-w-0">
              <p className={`text-[11px] font-bold truncate ${isCompleted ? 'text-emerald-700' : isConclActive ? 'text-indigo-900' : 'text-slate-600'}`}>
                Conclusion
              </p>
            </div>
          </div>

        </div>

      </div>

      {/* Chapter Problems List (Quick Switcher inside Sidebar) */}
      {chapterProblems.length > 0 && (
        <div className="bg-white rounded-xl p-2.5 border border-slate-200/90 shadow-2xs flex-1 min-h-0 flex flex-col">
          <div className="flex items-center justify-between mb-1.5 shrink-0">
            <h2 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1">
              <span>📚</span> Chapter Problems
            </h2>
            <span className="text-[10px] font-semibold text-slate-400">
              {chapterProblems.length}
            </span>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar space-y-1 pr-0.5">
            {chapterProblems.map((prob, idx) => {
              const isActive = problem?.id === prob.id || problem?.uuid === prob.uuid;
              const isSolved = solvedProblems?.has?.(prob.uuid) || solvedProblems?.has?.(prob.id);
              return (
                <button
                  key={prob.id}
                  type="button"
                  onClick={() => onSelectProblem && chapter?.id && onSelectProblem(chapter.id, prob.id)}
                  className={`w-full text-left flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-[11px] transition cursor-pointer ${
                    isActive
                      ? 'bg-indigo-50 border border-indigo-200 text-indigo-950 font-bold'
                      : 'hover:bg-slate-100 text-slate-600 border border-transparent'
                  }`}
                  title={prob.title}
                >
                  <span
                    className={`font-bold shrink-0 ${
                      isSolved
                        ? 'text-emerald-600'
                        : isActive
                        ? 'text-indigo-600'
                        : 'text-slate-300'
                    }`}
                  >
                    {isSolved ? '✓' : isActive ? '●' : '○'}
                  </span>
                  <span className="truncate">
                    Q{idx + 1}: {prob.title}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}
