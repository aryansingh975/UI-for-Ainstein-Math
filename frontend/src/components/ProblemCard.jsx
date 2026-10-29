import React from 'react';

export default function ProblemCard({ badge, text }) {
  if (!text) return null;

  return (
    <article className="problem-card" aria-label="Current Problem">
      <div className="problem-badge" id="problem-badge">
        {badge}
      </div>
      <div className="problem-text" id="problem-text">
        {text}
      </div>
    </article>
  );
}

