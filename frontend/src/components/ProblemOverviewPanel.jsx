import React, { useMemo } from 'react';

export default function ProblemOverviewPanel({
  chapter,
  problem,
  session,
  isCompleted
}) {
  const trail = session?.trail || [];

  // Determine extraction state
  const givenExtractionStep = trail.find((t) => t.nodeId === 'given_extraction');
  const goalExtractionStep = trail.find((t) => t.nodeId === 'goal_extraction');
  const hasExtractedGoal = Boolean(goalExtractionStep);
  const hasExtractedGivens = Boolean(givenExtractionStep);

  // Check if problem starts with an explicit extraction step
  const isExtractionProblem = Boolean(
    session?.active_node_id === 'given_extraction' ||
    session?.active_node_id === 'goal_extraction' ||
    hasExtractedGivens ||
    hasExtractedGoal
  );

  // Count calculation steps in trail
  const calcStepCount = trail.filter(
    (t) => t.nodeId !== 'given_extraction' && t.nodeId !== 'goal_extraction' && t.nodeId !== 'start'
  ).length;

  // Stage 1 Done: every checkmark must be earned!
  // - If extraction problem: student verified givens/goal
  // - If direct problem: student submitted their first calculation step (calcStepCount >= 1)
  const stage1Done = isExtractionProblem
    ? (hasExtractedGivens || hasExtractedGoal)
    : calcStepCount >= 1;

  const stage1StatusText = stage1Done ? 'Verified ✓' : 'In progress...';

  // Derive givens and goal items
  const { givenList, goalItem } = useMemo(() => {
    const givens = [];
    const text = session?.problem_text || '';

    // 1. If student explicitly answered given_extraction in trail
    if (givenExtractionStep) {
      givens.push({
        label: 'Verified Givens',
        value: givenExtractionStep.input,
        type: 'verified_given',
        isStudentStep: true
      });
    } else if (isExtractionProblem) {
      // Socratic extraction required: do not spoil or dump raw digits on Turn 0
      givens.push({
        label: 'Given Information',
        value: 'Pending discovery in chat...',
        type: 'pending',
        isPending: true
      });
    } else {
      // Direct problem (no extraction phase): show structured parameters if present

      // 2. Ratios (e.g. 3:4 and 72:96)
      const ratioMatches = [...text.matchAll(/(\d+\s*:\s*\d+)/g)].map((m) => m[1]);
      if (ratioMatches.length >= 2) {
        givens.push({
          label: 'First Ratio',
          value: `${ratioMatches[0]} (Given)`,
          type: 'given'
        });
        givens.push({
          label: 'Second Ratio',
          value: `${ratioMatches[1]} (Given)`,
          type: 'given'
        });
      }

      // 3. Prices / Profit & Loss (e.g. CP = 75, SP = 110)
      const cpMatch = text.match(/(?:CP|cost price|bought for)\s*(?:=|is|of)?\s*(?:Rs\.?|₹)?\s*(\d+(?:\.\d+)?)/i);
      const spMatch = text.match(/(?:SP|selling price|sold for)\s*(?:=|is|of)?\s*(?:Rs\.?|₹)?\s*(\d+(?:\.\d+)?)/i);
      if (cpMatch) {
        givens.push({
          label: 'Cost Price (CP)',
          value: `₹${cpMatch[1]}`,
          type: 'given'
        });
      }
      if (spMatch) {
        givens.push({
          label: 'Selling Price (SP)',
          value: `₹${spMatch[1]}`,
          type: 'given'
        });
      }

      // 4. Cube root / Square root / Target number
      const rootMatch = text.match(/(?:cube root|square root|prime factorisation of|cube of|square of)\s*(?:of)?\s*(\d+)/i);
      if (rootMatch && !cpMatch && !spMatch && ratioMatches.length < 2) {
        const isCube = /cube/i.test(text);
        givens.push({
          label: 'Target Number',
          value: rootMatch[1],
          type: 'given'
        });
        givens.push({
          label: 'Operation Required',
          value: isCube ? 'Cube Root (∛)' : 'Square Root (√)',
          type: 'given'
        });
      }

      // 5. Percentages in text
      const pctMatch = text.match(/(\d+(?:\.\d+)?\s*%)/);
      if (pctMatch && !givens.some((g) => g.value.includes('%'))) {
        givens.push({
          label: 'Given Percentage',
          value: pctMatch[1],
          type: 'given'
        });
      }
    }

    // 7. Extract any verified calculation steps from trail
    trail.forEach((t, idx) => {
      if (t.nodeId !== 'given_extraction' && t.nodeId !== 'goal_extraction' && t.nodeId !== 'start') {
        givens.push({
          label: t.label || `Step ${idx + 1} Result`,
          value: t.input,
          type: 'calc'
        });
      }
    });

    // Derive Goal
    let goal = null;
    if (goalExtractionStep) {
      goal = {
        label: 'Identified Goal',
        value: goalExtractionStep.input,
        verified: true
      };
    } else if (session?.conclusion_prompt) {
      goal = {
        label: 'Problem Goal',
        value: session.conclusion_prompt,
        verified: false
      };
    } else if (text) {
      if (/are\s+the\s+ratios/i.test(text)) {
        goal = {
          label: 'Problem Goal',
          value: 'Determine if the two ratios are proportional',
          verified: false
        };
      } else {
        const match = text.match(/(Check whether|Find|Determine|Calculate|Simplify|Solve)[^.?]+/i);
        if (match) {
          goal = {
            label: 'Problem Goal',
            value: match[0].trim(),
            verified: false
          };
        } else {
          goal = {
            label: 'Problem Goal',
            value: 'Solve for the requested quantity',
            verified: false
          };
        }
      }
    }

    return { givenList: givens, goalItem: goal };
  }, [session, trail, givenExtractionStep, goalExtractionStep]);

  const hasMethod = Boolean(session?.method_id || session?.method_label);
  const methodLabel = session?.method_label || (hasMethod ? 'Recognized Strategy' : 'Autonomous Discovery');

  return (
    <div className="md:col-span-5 flex flex-col gap-4">
      {/* Box 1: Stage 1 - Givens & Goal Extraction Tracker */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md uppercase tracking-wider mr-2">
              Stage 1
            </span>
            <h3 className="inline text-xs font-bold uppercase tracking-wider text-slate-600">
              Givens &amp; Goal
            </h3>
          </div>
          <span
            className={`text-xs font-medium ${
              stage1StatusText.includes('✓') ? 'text-emerald-600' : 'text-slate-400'
            }`}
          >
            {stage1StatusText}
          </span>
        </div>

        <div className="space-y-2 text-xs">
          {/* List of Givens */}
          {givenList.map((item, idx) => (
            <div
              key={idx}
              className={`flex items-center justify-between p-2 rounded-lg bg-white border shadow-xs ${
                item.type === 'calc'
                  ? 'border-emerald-500/40 bg-emerald-50/30'
                  : item.type === 'verified_given'
                  ? 'border-emerald-500/30 bg-emerald-50/20'
                  : item.type === 'pending'
                  ? 'border-amber-400/50 bg-amber-50/40'
                  : 'border-slate-200'
              }`}
            >
              <div className="flex items-center gap-1.5 text-slate-600 font-medium">
                {item.type === 'pending' && <span className="text-amber-500">⏳</span>}
                {item.type === 'verified_given' && <span className="text-emerald-500 font-bold">✓</span>}
                <span>{item.label}:</span>
              </div>
              <span
                className={`font-semibold ${
                  item.type === 'calc' || item.type === 'verified_given'
                    ? 'text-emerald-700 font-mono font-bold'
                    : item.type === 'pending'
                    ? 'text-amber-800 text-[11px] font-sans italic bg-amber-100/70 px-2 py-0.5 rounded-full'
                    : 'text-slate-800 font-mono font-bold'
                }`}
              >
                {item.value}
              </span>
            </div>
          ))}

          {/* Explicit Goal Card */}
          {goalItem && (
            <div
              className={`flex items-start justify-between p-2 rounded-lg bg-blue-50/60 border ${
                goalItem.verified ? 'border-emerald-400 bg-emerald-50/40' : 'border-blue-400/40'
              } shadow-xs`}
            >
              <div className="flex items-center gap-1.5 text-blue-900 font-semibold">
                <span>🎯</span>
                <span>{goalItem.label}:</span>
              </div>
              <div className="text-right">
                <span className="font-semibold text-blue-900 block font-sans">
                  {goalItem.value}
                </span>
                {goalItem.verified && (
                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">
                    Verified ✓
                  </span>
                )}
              </div>
            </div>
          )}

          {givenList.length === 0 && !goalItem && (
            <p className="text-slate-400 italic">State what is given or start calculating...</p>
          )}
        </div>
      </div>

      {/* Box 2: Stage 2 - Discovered Strategy & Roadmap */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div>
            <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md uppercase tracking-wider mr-2">
              Stage 2
            </span>
            <h3 className="inline text-xs font-bold uppercase tracking-wider text-slate-600">
              Strategy &amp; Roadmap
            </h3>
          </div>
          <span
            className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
              hasMethod
                ? 'text-emerald-700 bg-emerald-100'
                : 'text-slate-500 bg-slate-200'
            }`}
          >
            {hasMethod ? 'Locked by Student Step' : 'Student-Led Discovery'}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 mb-3">
          <span className="p-1 rounded bg-emerald-100">🧮</span>
          <span>{methodLabel}</span>
        </div>

        {/* Mini Roadmap dots */}
        <div className="space-y-2 text-xs">
          {hasMethod ? (
            <>
              {trail
                .filter((t) => t.nodeId !== 'given_extraction' && t.nodeId !== 'goal_extraction' && t.nodeId !== 'start')
                .map((t, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-emerald-600 font-medium">
                    <span className="w-4 h-4 rounded-full bg-emerald-100 border border-emerald-500 flex items-center justify-center text-[10px] font-bold">
                      ✓
                    </span>
                    <span>
                      Step {idx + 1}: {t.label || t.input}
                    </span>
                  </div>
                ))}
              {!isCompleted && (
                <div className="flex items-center gap-2 font-bold text-slate-900 bg-amber-50 p-1.5 rounded-lg border border-amber-200">
                  <span className="w-4 h-4 rounded-full bg-amber-500 text-white flex items-center justify-center text-[10px] font-bold">
                    ▶
                  </span>
                  <span>{session?.active_label || 'Current Calculation Step'}</span>
                </div>
              )}
              <div className="flex items-center gap-2 text-slate-400">
                <span
                  className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isCompleted ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200'
                  }`}
                >
                  {isCompleted ? '✓' : '○'}
                </span>
                <span>Final Conclusion &amp; Verification</span>
              </div>
            </>
          ) : (
            <p className="text-slate-500 text-xs leading-relaxed bg-white p-2.5 rounded-lg border border-slate-200">
              💡 No pre-selected method. Begin solving with your preferred calculation step, and Ainstein's Socratic engine will detect and scaffold your approach dynamically.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
