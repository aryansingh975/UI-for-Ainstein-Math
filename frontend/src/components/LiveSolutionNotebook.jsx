import React, { useMemo } from 'react';

export default function LiveSolutionNotebook({
  session,
  chapter,
  problem,
  isCompleted
}) {
  const trail = session?.trail || [];
  const text = session?.problem_text || '';

  // Extract date formatted nicely
  const currentDateStr = useMemo(() => {
    const d = new Date();
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }, []);

  // Determine extraction states
  const givenStep = trail.find((t) => t.nodeId === 'given_extraction');
  const goalStep = trail.find((t) => t.nodeId === 'goal_extraction');
  const isExtractionProblem = session?.active_node_id === 'given_extraction' || session?.active_node_id === 'goal_extraction' || Boolean(givenStep) || Boolean(goalStep);

  // Extract calculation steps (exclude extraction & start nodes)
  const calcSteps = trail.filter(
    (t) => t.nodeId !== 'given_extraction' && t.nodeId !== 'goal_extraction' && t.nodeId !== 'start'
  );

  // Derive Givens List
  const givensList = useMemo(() => {
    const list = [];
    if (session?.accumulated_givens && session.accumulated_givens.length > 0) {
      session.accumulated_givens.forEach((g, idx) => {
        list.push({ label: `Given Fact ${idx + 1}`, value: g, verified: true });
      });
    } else if (givenStep) {
      list.push({ label: 'Verified Givens', value: givenStep.input, verified: true });
    } else if (isExtractionProblem) {
      list.push({ label: 'Given Facts', value: 'Pending discovery in chat...', isPending: true });
    } else {
      // Direct problems: extract numbers or standard parameters
      const numbers = text.match(/\b\d+(?:,\d+)*(?:\.\d+)?%?\b/g);
      if (numbers && numbers.length > 0) {
        list.push({ label: 'Problem Parameters', value: numbers.join(', '), verified: true });
      } else {
        list.push({ label: 'Given Information', value: 'Extracted from problem statement', verified: true });
      }
    }
    return list;
  }, [session, givenStep, isExtractionProblem, text]);

  // Derive Goal Statement (Never reveal prematurely on extraction problems)
  const goalData = useMemo(() => {
    if (session?.extracted_goal) {
      return { value: session.extracted_goal, isPending: false };
    }
    if (goalStep) {
      return { value: goalStep.input, isPending: false };
    }
    // If extraction phase is part of this problem, keep it pending until student discovers it
    if (isExtractionProblem) {
      return { value: 'Pending discovery in chat...', isPending: true };
    }
    // Direct calculation problems without extraction phase:
    const findMatch = text.match(/(?:find|calculate|determine|what is|how many|check whether)\s+([^.?\n]+)/i);
    if (findMatch) {
      return { value: findMatch[1].trim(), isPending: false };
    }
    return { value: problem?.title || 'Solve for the required quantity', isPending: false };
  }, [session, goalStep, isExtractionProblem, text, problem]);

  return (
    <div className="flex flex-col bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden relative h-full min-h-0">
      
      {/* Notebook Toolbar */}
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 shrink-0 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-400"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400"></div>
          <span className="text-xs font-bold text-slate-700 ml-1.5 flex items-center gap-1.5">
            <span>📝</span> Live Solution Notebook
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[10px] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Live Auto-Sync</span>
          </span>
        </div>
      </div>

      {/* Ruled School Notebook Canvas */}
      <div className="notebook-paper p-5 sm:p-6 flex-1 min-h-0 custom-scrollbar overflow-y-auto text-slate-900 relative">
        
        {/* Header stamp inside notebook */}
        <div className="pl-12 mb-4 border-b border-slate-200/80 pb-2 flex items-center justify-between text-xs text-slate-500 font-mono-math">
          <span>Date: {currentDateStr}</span>
          <span className="font-semibold text-slate-600 truncate max-w-[200px]">
            {chapter?.title} • {problem?.title}
          </span>
        </div>

        {/* Section 1: Given Facts */}
        <div className="pl-12 mb-6">
          <h3 className="font-handwritten text-2xl font-bold text-indigo-950 leading-tight mb-1">
            Given :
          </h3>
          <div className="space-y-1 font-handwritten text-xl text-slate-800 tracking-wide">
            {givensList.map((g, idx) => (
              <p key={idx} className="flex items-center gap-2.5 flex-wrap">
                <span className="font-bold text-indigo-900">• {g.label}</span>
                <span>=</span>
                {g.isPending ? (
                  <span className="text-slate-400 italic font-sans text-xs">
                    ⏳ Pending discovery in chat...
                  </span>
                ) : (
                  <span className="bg-amber-100/80 px-2 py-0.5 rounded-md font-bold text-indigo-950 shadow-2xs">
                    {g.value}
                  </span>
                )}
              </p>
            ))}
          </div>
        </div>

        {/* Section 2: To Find */}
        <div className="pl-12 mb-6">
          <h3 className="font-handwritten text-2xl font-bold text-indigo-950 leading-tight mb-1">
            To Find :
          </h3>
          <p className="font-handwritten text-xl text-slate-800 tracking-wide flex items-center gap-2.5 flex-wrap">
            <span className="font-bold text-indigo-900">• Target Objective</span>
            <span>=</span>
            {goalData.isPending ? (
              <span className="text-slate-400 italic font-sans text-xs">
                ⏳ Pending discovery in chat...
              </span>
            ) : (
              <span className="text-indigo-700 font-bold bg-indigo-50/70 px-2 py-0.5 rounded-md border border-indigo-200/60 shadow-2xs">
                {goalData.value}
              </span>
            )}
          </p>
        </div>

        {/* Section 3: Mathematical Working */}
        <div className="pl-12 mb-6">
          <h3 className="font-handwritten text-2xl font-bold text-indigo-950 leading-tight mb-1">
            Calculation :
          </h3>
          {calcSteps.length === 0 ? (
            <p className="font-sans text-xs text-slate-400 italic pl-1">
              (Verified calculation steps will appear here as you solve them with Ainstein)
            </p>
          ) : (
            <div className="space-y-2 font-handwritten text-xl text-slate-800 tracking-wide">
              {calcSteps.map((step, idx) => (
                <div key={idx} className="flex items-center gap-3 flex-wrap">
                  <span className="text-slate-500 font-mono-math text-xs">Step {idx + 1}:</span>
                  <span className="bg-emerald-50 border border-emerald-200 text-emerald-950 font-bold px-2.5 py-0.5 rounded-lg shadow-2xs font-mono-math text-sm">
                    {step.input}
                  </span>
                  <span className="text-[11px] font-sans font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    Verified ✓
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Section 4: Next step in progress */}
        <div className="pl-12 pt-2">
          {isCompleted ? (
            <div className="font-handwritten text-2xl text-emerald-700 font-bold flex items-center gap-2">
              <span>🎉 Q.E.D. • Problem Successfully Solved!</span>
            </div>
          ) : (
            <div>
              <p className="font-handwritten text-xl text-indigo-700 font-bold flex items-center gap-2">
                <span>Working: </span>
                <span className="font-sans text-xs font-semibold text-slate-500">
                  {session?.prompt || 'State your next calculation step...'}
                </span>
                <span className="inline-block w-2.5 h-4 bg-indigo-600 animate-pulse ml-1"></span>
              </p>
              <p className="text-[11px] text-slate-400 font-sans italic mt-1">
                (Type in the dialogue console on the right →)
              </p>
            </div>
          )}
        </div>

      </div>

      {/* Notebook Bottom Footer */}
      <div className="bg-slate-50 border-t border-slate-200 px-4 py-2 shrink-0 flex items-center justify-between text-[11px] text-slate-500">
        <span>Handwritten ledger dynamically updates as Socratic steps verify</span>
        <span className="font-bold text-indigo-600">Ainstein Ledger</span>
      </div>

    </div>
  );
}
