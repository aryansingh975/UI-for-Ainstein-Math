import React from 'react';

export default function ProblemSelectorBar({
  chapters,
  selectedChapterId,
  onSelectChapter,
  problems,
  selectedProblemId,
  onSelectProblem,
  onLoadProblem,
  isLoading
}) {
  return (
    <div className="bg-slate-50 border-b border-slate-200 px-6 py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
      <div className="flex flex-wrap items-center gap-3 flex-1">
        {/* Chapter select */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="chapter-select" className="font-semibold text-slate-600">
            Chapter:
          </label>
          <select
            id="chapter-select"
            value={selectedChapterId}
            onChange={(e) => onSelectChapter(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium outline-none focus:border-emerald-500 cursor-pointer"
          >
            {chapters.map((ch) => (
              <option key={ch.id} value={ch.id}>
                {ch.title} ({ch.description})
              </option>
            ))}
          </select>
        </div>

        {/* Problem select */}
        <div className="flex items-center gap-1.5 flex-1 min-w-[200px]">
          <label htmlFor="problem-select" className="font-semibold text-slate-600">
            Problem:
          </label>
          <select
            id="problem-select"
            value={selectedProblemId}
            onChange={(e) => onSelectProblem(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium outline-none focus:border-emerald-500 cursor-pointer"
          >
            {problems.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="button"
        onClick={onLoadProblem}
        disabled={isLoading}
        className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1 cursor-pointer disabled:opacity-50"
      >
        <span>{isLoading ? 'Loading...' : 'Load Problem'}</span>
        <span>➔</span>
      </button>
    </div>
  );
}

