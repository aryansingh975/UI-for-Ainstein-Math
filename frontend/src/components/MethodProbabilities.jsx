import React from 'react';

// Small bar chart of Jev's probability for each method
export default function MethodProbabilities({ probabilities, labels = {} }) {
  if (!probabilities || Object.keys(probabilities).length === 0) return null;

  const rows = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);

  return (
    <div className="jev-probabilities">
      <div className="answer-meta">JEV · METHOD PROBABILITIES</div>
      {rows.map(([id, p]) => {
        const pct = Math.round(Number(p) * 100);
        return (
          <div key={id} className="jev-prob-row">
            <span className="jev-prob-label">{labels[id] || id}</span>
            <span className="jev-prob-track">
              <span className="jev-prob-fill" style={{ width: `${pct}%` }} />
            </span>
            <span className="jev-prob-value">{pct}%</span>
          </div>
        );
      })}
    </div>
  );
}
