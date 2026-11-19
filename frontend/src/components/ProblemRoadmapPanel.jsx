import React from 'react';

export default function ProblemRoadmapPanel({
  chapter,
  problem,
  session,
  isCompleted,
  totalProblems = 4,
  problemIndex = 1
}) {
  const trail = session?.trail || [];
  const history = session?.history || [];
  const text = session?.problem_text || '';
  const hasStarted = trail.length > 0 || history.length > 0;

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
    <div className="space-y-2 flex flex-col h-full min-h-0">
      
      {/* Problem Question Card (Expanded & Clear Edition) */}
      <div className="bg-white rounded-xl p-3 border border-indigo-100/90 shadow-2xs relative shrink-0 flex flex-col gap-1.5">
        <div className="flex items-center justify-between pb-1 border-b border-indigo-50">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-md border border-indigo-100/80 flex items-center gap-1">
            <span>❓</span> Q{problemIndex} of {totalProblems}
          </span>
        </div>

        <div>
          <h3 className="font-extrabold text-slate-900 text-xs sm:text-sm leading-snug mb-1.5" title={problem?.title}>
            {problem?.title || 'Problem Statement'}
          </h3>
          <div className="text-slate-700 text-xs font-medium leading-relaxed max-h-48 overflow-y-auto custom-scrollbar p-2 rounded-lg bg-slate-50/70 border border-slate-100 text-left">
            "{text || 'Loading problem statement...'}"
          </div>
        </div>
      </div>

      {/* Vertical Solution Plan Stepper (Slim 200px Edition) */}
      <div className="bg-white rounded-xl p-2.5 border border-indigo-100 shadow-xs flex-1 min-h-0 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-1.5 shrink-0">
          <h2 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1">
            <span className="text-indigo-600">🎯</span> Roadmap
          </h2>
        </div>

        <div className="space-y-1.5 relative flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-0.5">
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

    </div>
  );
}
