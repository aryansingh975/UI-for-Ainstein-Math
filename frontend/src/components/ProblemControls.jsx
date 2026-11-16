import React from 'react';

export default function ProblemControls({
  chapters,
  selectedChapterId,
  onSelectChapter,
  problems,
  selectedProblemId,
  onSelectProblem,
  onLoadProblem,
  problemTitle,
  problemDescription,
  isLoading
}) {
  // One dropdown section per class, in class order
  const grades = [...new Set(chapters.map((ch) => ch.grade))].sort((a, b) => a - b);

  return (
    <>
      <section className="controls" aria-label="Choose a problem">
        <div className="chapter-selector">
          <label htmlFor="chapter-select">Chapter</label>
          <select
            id="chapter-select"
            value={selectedChapterId}
            onChange={(e) => onSelectChapter(e.target.value)}
          >
            <option value="">Select a chapter...</option>
            {grades.map((grade) => (
              <optgroup key={grade} label={`Class ${grade}`}>
                {chapters.filter((ch) => ch.grade === grade).map((ch) => (
                  <option key={ch.id} value={ch.id}>
                    {ch.title} ({ch.description})
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        <div className="problem-selector">
          <label htmlFor="problem-select">Problem</label>
          <select
            id="problem-select"
            value={selectedProblemId}
            onChange={(e) => onSelectProblem(e.target.value)}
          >
            <option value="">Select a problem...</option>
            {problems.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
          </select>
        </div>

        <button
          id="load-problem"
          className="load-button"
          type="button"
          onClick={onLoadProblem}
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : 'Load Problem'} <span>→</span>
        </button>
      </section>

      <section className="problem-info" aria-live="polite">
        <div className="eyebrow">SELECTED PROBLEM <span></span></div>
        <div id="problem-header">
          <h2 id="problem-title">{problemTitle || 'Select a problem to begin'}</h2>
          <p id="problem-description">{problemDescription || ''}</p>
        </div>
      </section>
    </>
  );
}

