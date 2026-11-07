import React from 'react';

export default function MilestoneStepper({ session, isCompleted }) {
  const activeNodeId = session?.active_node_id || '';
  const trail = session?.trail || [];
  const isConclusion = isCompleted || activeNodeId === 'conclusion' || activeNodeId === 'final_conclusion';

  // Check if session has extraction in trail or is currently at extraction
  const isCurrentlyExtraction = activeNodeId === 'given_extraction' || activeNodeId === 'goal_extraction';
  const hasExtractedInTrail = trail.some(
    (t) => t.nodeId === 'given_extraction' || t.nodeId === 'goal_extraction'
  );
  const isExtractionProblem = isCurrentlyExtraction || hasExtractedInTrail;

  // Count mathematical calculation steps in trail
  const calcStepCount = trail.filter(
    (t) => t.nodeId !== 'given_extraction' && t.nodeId !== 'goal_extraction' && t.nodeId !== 'start'
  ).length;

  // STAGE 1 (Initial Setup / Understand):
  // - NEVER pre-completed on Turn 0! Every checkmark must be earned.
  // - For extraction problem: Done when extraction verified in trail.
  // - For direct math problem: Done when student submits their first calculation step (calcStepCount >= 1).
  const stage1Done = isExtractionProblem ? hasExtractedInTrail : calcStepCount >= 1;
  const stage1Active = !stage1Done && !isConclusion && !isCompleted;

  // STAGE 2 (Mathematical Steps / Core Calculations):
  // - Done if: conclusion reached or completed
  // - Active if: Stage 1 is earned and conclusion not yet reached
  const stage2Done = isConclusion || isCompleted;
  const stage2Active = stage1Done && !stage2Done;

  // STAGE 3 (Final Conclusion):
  // - Done if: completed
  // - Active if: at conclusion node, waiting for final step
  const stage3Done = isCompleted;
  const stage3Active = !isCompleted && isConclusion;

  // Step label for stage 2
  const currentStepName = session?.active_label || (calcStepCount > 0 ? `Step ${calcStepCount + 1}` : 'Calculation');

  // Dynamic milestone titles matching problem nature
  const stage1Title = isExtractionProblem
    ? '1. Understand Problem (Givens & Goal)'
    : '1. Initial Step / Setup';

  const stage2Title = isExtractionProblem
    ? `2. Mathematical Steps ${stage2Active ? `(${currentStepName})` : ''}`
    : `2. Core Calculations ${stage2Active ? `(${currentStepName})` : ''}`;

  return (
    <div className="mb-6 bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center justify-between gap-3 overflow-x-auto text-xs">
      {/* Stage 1: Understand / Initial Step */}
      <div
        className={`flex items-center gap-2 font-medium shrink-0 ${
          stage1Done
            ? 'text-emerald-600'
            : stage1Active
            ? 'text-slate-900 font-bold animate-pulse-subtle'
            : 'text-slate-500'
        }`}
      >
        <span
          className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs ${
            stage1Done
              ? 'bg-emerald-100 border border-emerald-500 text-emerald-700'
              : stage1Active
              ? 'bg-amber-500 text-white shadow-sm'
              : 'bg-white border border-slate-300 text-slate-400'
          }`}
        >
          {stage1Done ? '✓' : '1'}
        </span>
        <span className={stage1Active ? 'underline decoration-amber-500 decoration-2 underline-offset-4' : ''}>
          {stage1Title}
        </span>
      </div>

      <div className={`h-0.5 w-12 shrink-0 ${stage1Done ? 'bg-emerald-500' : 'bg-slate-200'}`} />

      {/* Stage 2: Mathematical Steps / Core Calculations */}
      <div
        className={`flex items-center gap-2 shrink-0 ${
          stage2Done
            ? 'font-medium text-emerald-600'
            : stage2Active
            ? 'font-bold text-slate-900 animate-pulse-subtle'
            : 'font-medium text-slate-400'
        }`}
      >
        <span
          className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs ${
            stage2Done
              ? 'bg-emerald-100 border border-emerald-500 text-emerald-700'
              : stage2Active
              ? 'bg-amber-500 text-white shadow-sm'
              : 'bg-white border border-slate-300 text-slate-400'
          }`}
        >
          {stage2Done ? '✓' : '2'}
        </span>
        <span className={stage2Active ? 'underline decoration-amber-500 decoration-2 underline-offset-4' : ''}>
          {stage2Title}
        </span>
      </div>

      <div className={`h-0.5 w-12 shrink-0 ${stage2Done ? 'bg-emerald-500' : 'bg-slate-200'}`} />

      {/* Stage 3: Final Conclusion */}
      <div
        className={`flex items-center gap-2 shrink-0 ${
          stage3Done
            ? 'font-medium text-emerald-600'
            : stage3Active
            ? 'font-bold text-slate-900 animate-pulse-subtle'
            : 'font-medium text-slate-400'
        }`}
      >
        <span
          className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs ${
            stage3Done
              ? 'bg-emerald-100 border border-emerald-500 text-emerald-700'
              : stage3Active
              ? 'bg-amber-500 text-white shadow-sm'
              : 'bg-white border border-slate-300 text-slate-400'
          }`}
        >
          {stage3Done ? '✓' : '3'}
        </span>
        <span className={stage3Active ? 'underline decoration-amber-500 decoration-2 underline-offset-4' : ''}>
          3. Final Conclusion
        </span>
      </div>
    </div>
  );
}
