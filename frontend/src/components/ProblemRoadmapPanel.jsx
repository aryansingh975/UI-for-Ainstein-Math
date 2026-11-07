import React, { useMemo, useState } from 'react';

export default function ProblemRoadmapPanel({
  chapter,
  problem,
  session,
  isCompleted,
  totalProblems = 4,
  problemIndex = 1,
  formulasOpen: externalFormulasOpen,
  onToggleFormulas: externalToggleFormulas
}) {
  const [internalFormulasOpen, setInternalFormulasOpen] = useState(false);
  const formulasOpen = externalFormulasOpen !== undefined ? externalFormulasOpen : internalFormulasOpen;
  const toggleFormulas = externalToggleFormulas || (() => setInternalFormulasOpen((prev) => !prev));
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

  // Derive relevant formulas based on problem topic / chapter
  const formulaData = useMemo(() => {
    const lowerText = text.toLowerCase();
    const chId = chapter?.id || '';

    if (lowerText.includes('depreciat') || chId.includes('percentage') || chId.includes('profit')) {
      return {
        title: 'Percentages & Depreciation',
        items: [
          { expr: 'Depreciation = (P × R × T) / 100', desc: 'Amount lost per year' },
          { expr: 'Final Value = Original Price - Depreciation', desc: 'Net asset valuation' },
          { expr: 'P: Principal, R: Rate (%), T: Time (years)', desc: 'Standard variables' }
        ]
      };
    }
    if (lowerText.includes('age') || chId.includes('algebra')) {
      return {
        title: 'Linear Equations & Ages',
        items: [
          { expr: 'Age after t years = Present Age + t', desc: 'Future age addition' },
          { expr: 'Mother = k × Daughter', desc: 'Ratio relationship' },
          { expr: 'ax + b = c  ⟹  x = (c - b) / a', desc: 'Linear solver' }
        ]
      };
    }
    if (lowerText.includes('ratio') || lowerText.includes('proport') || chId.includes('ratio')) {
      return {
        title: 'Ratio & Proportion',
        items: [
          { expr: 'a : b = c : d  ⟺  a × d = b × c', desc: 'Cross-multiplication rule' },
          { expr: 'Simplest Form: Divide by HCF(a, b)', desc: 'Reduction by common factor' }
        ]
      };
    }
    if (lowerText.includes('cube') || lowerText.includes('square') || chId.includes('square') || chId.includes('power')) {
      return {
        title: 'Powers & Roots',
        items: [
          { expr: '√n = prime factor pairs', desc: 'Square root factorisation' },
          { expr: '∛n = prime factor triplets', desc: 'Cube root grouping' }
        ]
      };
    }
    return {
      title: 'Problem Formulas',
      items: [
        { expr: 'Step-by-step mathematical deduction', desc: 'Express reasoning clearly' }
      ]
    };
  }, [text, chapter]);

  return (
    <div className="space-y-3 flex flex-col h-full min-h-0">
      
      {/* Problem Question Card */}
      <div className="bg-white rounded-2xl p-4 border border-indigo-100 shadow-xs relative overflow-hidden shrink-0">
        <div className="absolute -top-6 -right-6 w-20 h-20 rounded-full bg-indigo-50/70 pointer-events-none"></div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-lg">
            Question {problemIndex} of {totalProblems}
          </span>
          <span className="text-[11px] font-semibold text-slate-400">
            {chapter?.grade ? `Grade ${chapter.grade}` : 'NCERT'}
          </span>
        </div>
        <h3 className="font-bold text-slate-900 text-xs sm:text-sm mb-1">{problem?.title}</h3>
        <p className="text-slate-700 text-xs font-medium leading-relaxed">
          "{text || 'Loading problem statement...'}"
        </p>
      </div>

      {/* Vertical Solution Plan Stepper */}
      <div className="bg-white rounded-2xl p-4 border border-indigo-100 shadow-xs flex-1 min-h-0 flex flex-col">
        <div className="flex items-center justify-between mb-3 shrink-0">
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <span className="text-indigo-600">🎯</span> Solution Roadmap
          </h2>
          <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-full">
            {isCompleted
              ? 'Completed ✓'
              : isConclActive
              ? 'Final Step'
              : isCalcActive
              ? 'Stage 2: Math'
              : !hasStarted
              ? 'Stage 0: Reading'
              : 'Stage 1: Discovery'}
          </span>
        </div>

        <div className="space-y-3 relative flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-1">
          {/* Continuous vertical timeline line */}
          <div className="absolute left-3.5 top-3 bottom-3 w-0.5 bg-slate-200 -z-0"></div>

          {/* Step 1: Understand Problem */}
          <div className={`flex items-start gap-3 relative z-10 p-1.5 rounded-xl transition-all ${
            !hasStarted ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shadow-xs shrink-0 ${
              hasStarted
                ? 'bg-emerald-600 text-white'
                : 'bg-indigo-600 text-white animate-pulse'
            }`}>
              {hasStarted ? '✓' : '1'}
            </div>
            <div className="pt-0.5">
              <div className="flex items-center gap-1.5">
                <p className={`text-xs font-bold ${!hasStarted ? 'text-indigo-900' : 'text-slate-800'}`}>
                  Understand Problem
                </p>
                {!hasStarted && <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {hasStarted ? 'Problem statement understood ✓' : 'Read problem statement & context'}
              </p>
            </div>
          </div>

          {/* Step 2: Extract Givens */}
          <div className={`flex items-start gap-3 relative z-10 p-1.5 rounded-xl transition-all ${
            isGivenActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shadow-xs shrink-0 ${
              hasExtractedGivens || !isGivenActive && trail.length > 0
                ? 'bg-emerald-600 text-white'
                : isGivenActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {hasExtractedGivens || (!isGivenActive && trail.length > 0) ? '✓' : '2'}
            </div>
            <div className="pt-0.5">
              <div className="flex items-center gap-1.5">
                <p className={`text-xs font-bold ${isGivenActive ? 'text-indigo-900' : 'text-slate-800'}`}>
                  Identify Givens
                </p>
                {isGivenActive && <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {hasExtractedGivens ? 'Given quantities verified' : 'Extract known problem facts'}
              </p>
            </div>
          </div>

          {/* Step 3: Identify Goal */}
          <div className={`flex items-start gap-3 relative z-10 p-1.5 rounded-xl transition-all ${
            isGoalActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shadow-xs shrink-0 ${
              hasExtractedGoal || (!isGoalActive && !isGivenActive && trail.length > 1)
                ? 'bg-emerald-600 text-white'
                : isGoalActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {hasExtractedGoal || (!isGoalActive && !isGivenActive && trail.length > 1) ? '✓' : '3'}
            </div>
            <div className="pt-0.5">
              <div className="flex items-center gap-1.5">
                <p className={`text-xs font-bold ${isGoalActive ? 'text-indigo-900' : 'text-slate-800'}`}>
                  State Problem Goal
                </p>
                {isGoalActive && <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {hasExtractedGoal ? 'Goal objective verified' : 'What needs to be found'}
              </p>
            </div>
          </div>

          {/* Step 4: Mathematical Steps */}
          <div className={`flex items-start gap-3 relative z-10 p-1.5 rounded-xl transition-all ${
            isCalcActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shadow-xs shrink-0 ${
              isCompleted
                ? 'bg-emerald-600 text-white'
                : isCalcActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {isCompleted ? '✓' : '4'}
            </div>
            <div className="pt-0.5">
              <div className="flex items-center gap-1.5">
                <p className={`text-xs font-bold ${isCalcActive ? 'text-indigo-900' : 'text-slate-800'}`}>
                  Mathematical Steps
                </p>
                {isCalcActive && <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping"></span>}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {session?.method_label ? (
                  <span className="text-indigo-600 font-bold">{session.method_label}</span>
                ) : (
                  'Autonomous strategy discovery'
                )}
              </p>
            </div>
          </div>

          {/* Step 5: Final Conclusion */}
          <div className={`flex items-start gap-3 relative z-10 p-1.5 rounded-xl transition-all ${
            isConclActive ? 'bg-indigo-50 border border-indigo-200' : ''
          }`}>
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shadow-xs shrink-0 ${
              isCompleted
                ? 'bg-emerald-600 text-white'
                : isConclActive
                ? 'bg-indigo-600 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400 border border-slate-300'
            }`}>
              {isCompleted ? '✓' : '5'}
            </div>
            <div className="pt-0.5">
              <p className={`text-xs font-bold ${isCompleted ? 'text-emerald-700' : isConclActive ? 'text-indigo-900' : 'text-slate-600'}`}>
                Final Conclusion
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {isCompleted ? 'Problem solved 🎉' : 'Verify final answer & units'}
              </p>
            </div>
          </div>

        </div>
      </div>

      {/* Collapsible Useful Formulas Card */}
      <div id="formula-card" className="bg-gradient-to-br from-indigo-50/70 to-purple-50/60 rounded-2xl p-3 border border-indigo-200/80 shadow-2xs shrink-0 transition-all duration-300">
        <div
          className="flex items-center justify-between cursor-pointer"
          onClick={toggleFormulas}
        >
          <div className="flex items-center gap-1.5">
            <span className="text-indigo-600 font-bold text-xs">📐</span>
            <span className="text-[11px] font-bold text-indigo-900 uppercase tracking-wider">
              {formulaData.title}
            </span>
          </div>
          <span className="text-[10px] font-semibold text-indigo-600 bg-white px-2 py-0.5 rounded-full border border-indigo-200">
            {formulasOpen ? 'Hide ▴' : 'Show ▾'}
          </span>
        </div>

        {formulasOpen && (
          <div className="space-y-1.5 text-xs text-slate-700 mt-2.5 pt-2 border-t border-indigo-100 max-h-[180px] overflow-y-auto custom-scrollbar">
            {formulaData.items.map((item, idx) => (
              <div key={idx} className="bg-white p-2 rounded-xl border border-indigo-100 font-mono-math text-center font-bold text-indigo-950 shadow-2xs text-[11px]">
                <div>{item.expr}</div>
                <div className="text-[9px] text-slate-500 font-sans font-normal mt-0.5">{item.desc}</div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
