import React from 'react';

export default function StrategyExplainerView({ onBackToWorkspace }) {
  return (
    <div className="p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 px-3 py-1 rounded-full bg-emerald-100">
            True Socratic Pedagogy
          </span>
          <h2 className="text-xl font-bold text-slate-900">
            Autonomous Method Discovery (No Multiple-Choice)
          </h2>
          <p className="text-xs text-slate-600 max-w-lg mx-auto">
            Instead of spoon-feeding the student a list of methods upfront, the student initiates their own strategy. Ainstein's engine recognizes the path dynamically:
          </p>
        </div>

        {/* 3 Socratic Scenarios Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Scenario A: Student starts with HCF */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between space-y-3 shadow-sm">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-md">
                  Path A: Simplification
                </span>
                <span className="text-base">🧮</span>
              </div>
              <p className="text-xs text-slate-500 font-semibold">Student begins directly:</p>
              <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-900 font-mono">
                "HCF of 72 and 96 is 24"
              </div>
              <p className="text-xs text-slate-500 font-semibold">Tutor recognizes &amp; locks:</p>
              <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-300 text-xs text-emerald-900">
                "Great intuition! You're simplifying by HCF. Now divide 72 and 96 by 24."
              </div>
            </div>
            <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500">
              DAG automatically focuses on: <strong className="text-slate-800">m1_simplify</strong>
            </div>
          </div>

          {/* Scenario B: Student starts with Cross-Multiply */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between space-y-3 shadow-sm">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-md">
                  Path B: Cross-Product
                </span>
                <span className="text-base">✖️</span>
              </div>
              <p className="text-xs text-slate-500 font-semibold">Student begins directly:</p>
              <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-900 font-mono">
                "3 * 96 = 288"
              </div>
              <p className="text-xs text-slate-500 font-semibold">Tutor recognizes &amp; locks:</p>
              <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-300 text-xs text-emerald-900">
                "Awesome! You're using cross-multiplication. Now what is 4 * 72?"
              </div>
            </div>
            <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500">
              DAG automatically focuses on: <strong className="text-slate-800">m5_cross_mult</strong>
            </div>
          </div>

          {/* Scenario C: Student is Stuck */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col justify-between space-y-3 shadow-sm">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md">
                  Path C: Stuck / Help
                </span>
                <span className="text-base">💡</span>
              </div>
              <p className="text-xs text-slate-500 font-semibold">Student asks for help:</p>
              <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900">
                "I don't know how to test if they are equal"
              </div>
              <p className="text-xs text-slate-500 font-semibold">Tutor gently guides:</p>
              <div className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-800">
                "Think about it: could you simplify 72/96 to its smallest numbers, or cross-multiply? Which would you like to try?"
              </div>
            </div>
            <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500">
              Scaffolding provided <strong className="text-slate-800">only on demand</strong>
            </div>
          </div>
        </div>

        <div className="text-center pt-4">
          <button
            type="button"
            onClick={onBackToWorkspace}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
          >
            ← Return to Workspace
          </button>
        </div>
      </div>
    </div>
  );
}

