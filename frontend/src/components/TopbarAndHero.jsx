import React from 'react';

export default function TopbarAndHero() {
  return (
    <>
      <header className="topbar">
        <div className="breadcrumb">Workspace <span>/</span> Guided practice</div>
        <div className="chapter-chip">
          <span className="chip-dot"></span>Socratic tutor
        </div>
      </header>

      <section className="hero" id="workspace">
        <div className="eyebrow">Ainstein Socratic Lab <span></span> 01</div>
        <h1>
          The student solves.<br />
          <em>The tutor guides.</em>
        </h1>
        <p className="hero-copy">
          Work through each problem one step at a time. Choose a chapter and problem, then show your reasoning.
        </p>
      </section>
    </>
  );
}

