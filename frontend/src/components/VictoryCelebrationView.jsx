import React from 'react';

export default function VictoryCelebrationView({
  session,
  onReviewSteps,
  onNextProblem,
  onStartAgain,
  onOpenMainMenu
}) {
  const trail = session?.trail || [];
  const methodLabel = session?.method_label || 'Direct Mathematical Proof';

  return (
    <div className="w-full flex items-center justify-center p-2">
      <div className="max-w-lg w-full bg-slate-50 border-2 border-emerald-500 rounded-3xl p-4 sm:p-5 text-center space-y-3 shadow-xl relative overflow-hidden">
        {/* Trophy Badge */}
        <div className="w-12 h-12 mx-auto rounded-2xl bg-emerald-600 text-white flex items-center justify-center text-2xl shadow-md shadow-emerald-600/30">
          🏆
        </div>

        <div className="space-y-0.5">
          <h2 className="text-lg font-bold text-slate-900 leading-tight">
            Problem Solved Socratically!
          </h2>
          <p className="text-[11px] text-slate-500 leading-tight">
            You proved every single step rigorously with zero shortcuts.
          </p>
        </div>

        {/* Solution Recap Summary Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-3 text-left text-xs shadow-xs space-y-1.5">
          <div className="flex items-center justify-between pb-1 border-b border-slate-100">
            <span className="font-bold uppercase tracking-wider text-emerald-700 text-[10px]">
              Verified Proof Summary:
            </span>
            <span className="text-[10px] font-semibold text-slate-400">
              {trail.length} steps verified
            </span>
          </div>

          <div className="flex items-center justify-between py-0.5 border-b border-slate-100 text-[11px]">
            <span className="text-slate-500">1. Strategy pursued:</span>
            <span className="font-semibold text-slate-900 truncate max-w-[220px]">{methodLabel}</span>
          </div>

          {/* Scrollable step list if many steps, so card never overflows screen */}
          <div className="max-h-[140px] overflow-y-auto custom-scrollbar space-y-1 pr-1 text-[11px]">
            {trail.map((t, idx) => (
              <div key={idx} className="flex items-center justify-between py-0.5 border-b border-slate-50">
                <span className="text-slate-500 truncate max-w-[180px]">
                  {idx + 2}. {t.label || `Step ${idx + 1}`}:
                </span>
                <span className="font-mono font-bold text-emerald-600 truncate max-w-[190px]">{t.input}</span>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
            <span className="text-slate-500">Final conclusion:</span>
            <span className="font-bold text-emerald-600 truncate max-w-[220px]">
              {session?.conclusion_description || 'Goal Achieved & Verified ✓'}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
          {onNextProblem && (
            <button
              type="button"
              onClick={onNextProblem}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <span>Next Problem</span>
              <span>➔</span>
            </button>
          )}
          <button
            type="button"
            onClick={onReviewSteps}
            className="px-3.5 py-2 rounded-xl border border-emerald-300 bg-white text-emerald-800 text-xs font-semibold hover:bg-emerald-50 transition-colors cursor-pointer"
          >
            Review Steps
          </button>
          {onOpenMainMenu && (
            <button
              type="button"
              onClick={onOpenMainMenu}
              className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs transition-all flex items-center gap-1 cursor-pointer"
            >
              <span>📚 All Chapters</span>
            </button>
          )}
          <button
            type="button"
            onClick={onStartAgain}
            className="px-3 py-2 rounded-xl border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            ↺ Solve Again
          </button>
        </div>
      </div>
    </div>
  );
}
