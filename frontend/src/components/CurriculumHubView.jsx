import React, { useState, useMemo } from 'react';

const CHAPTER_ICONS = {
  'proportional-reasoning': '⚖️',
  'squares-and-cubes': '🧊',
  'power-play': '⚡',
  'inverse-proportion': '🔄',
  'percentages': '📈',
  'algebra-play': '🧩',
  'linear-equation': '🎯'
};

export default function CurriculumHubView({
  chapters,
  solvedProblems = new Set(),
  onSelectProblem,
  onBackToWorkspace,
  currentProblem
}) {
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [activeChapterId, setActiveChapterId] = useState(null);

  // Filter chapters by grade
  const filteredChapters = useMemo(() => {
    if (selectedGrade === 'all') return chapters;
    return chapters.filter((c) => String(c.grade) === selectedGrade);
  }, [chapters, selectedGrade]);

  const activeChapter = useMemo(() => {
    return chapters.find((c) => c.id === activeChapterId) || null;
  }, [chapters, activeChapterId]);

  return (
    <div className="p-6 fade-in space-y-6">
      {/* Top Header of Main Menu */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full">
              NCERT Curriculum Hub
            </span>
            <span className="text-xs text-slate-400">Classes 8 &amp; 10</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mt-1">
            Select a Chapter to Master
          </h2>
          <p className="text-xs text-slate-500">
            Browse our Socratic problem sets and master mathematical concepts with step-by-step guidance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {currentProblem && (
            <button
              type="button"
              onClick={onBackToWorkspace}
              className="px-4 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-xs font-bold text-slate-700 flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              <span>←</span>
              <span>Back to Active Problem</span>
            </button>
          )}

          {/* Grade Filters */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 gap-1 text-xs font-semibold">
            <button
              type="button"
              onClick={() => setSelectedGrade('all')}
              className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                selectedGrade === 'all'
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Grades
            </button>
            <button
              type="button"
              onClick={() => setSelectedGrade('8')}
              className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                selectedGrade === '8'
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Grade 8
            </button>
            <button
              type="button"
              onClick={() => setSelectedGrade('10')}
              className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                selectedGrade === '10'
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Grade 10
            </button>
          </div>
        </div>
      </div>

      {/* VIEW A: Chapter Cards Grid (when no specific chapter is opened) */}
      {!activeChapter ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {filteredChapters.map((chapter) => {
            const icon = CHAPTER_ICONS[chapter.id] || '📐';
            const totalCount = chapter.problems.length;
            const solvedCount = chapter.problems.filter((p) => solvedProblems.has(p.uuid)).length;
            const pct = totalCount > 0 ? Math.round((solvedCount / totalCount) * 100) : 0;

            return (
              <div
                key={chapter.id}
                onClick={() => setActiveChapterId(chapter.id)}
                className="bg-white hover:bg-slate-50 border border-slate-200 hover:border-emerald-500 rounded-3xl p-5 shadow-sm hover:shadow-lg transition-all cursor-pointer flex flex-col justify-between space-y-4 group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 rounded-2xl bg-slate-100 group-hover:bg-emerald-100 flex items-center justify-center text-2xl transition-colors shadow-xs">
                      {icon}
                    </div>
                    <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-2.5 py-0.5 rounded-full">
                      Grade {chapter.grade}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-base group-hover:text-emerald-700 transition-colors">
                    {chapter.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    {chapter.description}
                  </p>
                </div>

                <div className="space-y-2 pt-3 border-t border-slate-100">
                  <div className="flex justify-between text-xs text-slate-500 font-semibold">
                    <span>Progress: {solvedCount} / {totalCount} Solved</span>
                    <span className={solvedCount > 0 ? 'text-emerald-600 font-bold' : ''}>{pct}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="text-[11px] font-bold text-emerald-700 flex items-center justify-between pt-1">
                    <span>{totalCount} {totalCount === 1 ? 'Problem' : 'Problems'}</span>
                    <span className="group-hover:translate-x-1 transition-transform">
                      View Questions ➔
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* VIEW B: Questions List for the Selected Chapter */
        <div className="space-y-5 fade-in">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setActiveChapterId(null)}
                className="w-9 h-9 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 flex items-center justify-center text-sm font-bold text-slate-700 cursor-pointer shadow-xs"
              >
                ←
              </button>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl">{CHAPTER_ICONS[activeChapter.id] || '📐'}</span>
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                    Grade {activeChapter.grade}
                  </span>
                  <span className="text-xs text-slate-400">
                    {activeChapter.problems.length} Problems
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-1">
                  {activeChapter.title} — Questions
                </h3>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setActiveChapterId(null)}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 underline cursor-pointer"
            >
              ← All Chapters
            </button>
          </div>

          <p className="text-xs text-slate-500">
            Select any question below to launch into the Socratic tutoring workspace:
          </p>

          <div className="space-y-3">
            {activeChapter.problems.map((prob, idx) => {
              const isSolved = solvedProblems.has(prob.uuid);

              return (
                <div
                  key={prob.id}
                  onClick={() => onSelectProblem(activeChapter.id, prob.id)}
                  className={`border rounded-2xl p-4 flex items-center justify-between transition-all cursor-pointer shadow-xs ${
                    isSolved
                      ? 'bg-emerald-50/40 border-emerald-300 hover:bg-emerald-100/50'
                      : 'bg-white border-slate-200 hover:border-emerald-500 hover:shadow-md'
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <span
                      className={`w-8 h-8 rounded-xl font-bold flex items-center justify-center text-xs shrink-0 ${
                        isSolved
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {isSolved ? '✓' : idx + 1}
                    </span>
                    <div>
                      <h4 className="font-bold text-slate-900 text-sm">
                        {prob.title}
                      </h4>
                      <p className="text-[11px] text-slate-500 font-mono">
                        ID: {prob.uuid}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {isSolved && (
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
                        Solved Socratically ✓
                      </span>
                    )}
                    <button
                      type="button"
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                        isSolved
                          ? 'border border-emerald-400 bg-white text-emerald-800 hover:bg-emerald-50'
                          : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm'
                      }`}
                    >
                      <span>{isSolved ? 'Review' : 'Start Problem'}</span>
                      <span>➔</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

