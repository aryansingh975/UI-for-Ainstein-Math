import React from 'react';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="." aria-label="Ainstein home">
        <span className="brand-mark">a</span>
        <span>ainstein</span>
      </a>
      <div className="side-label">Socratic Lab</div>
      <nav className="nav-list" aria-label="Main navigation">
        <a className="nav-item is-active" href="#workspace">
          <span className="nav-icon">01</span>Guided practice
        </a>
      </nav>
      <div className="sidebar-bottom">
        <div className="coverage-card">
          <div className="coverage-kicker">CURRENT ACTIVITY</div>
          <strong>Guided Problem Solving</strong>
          <span>Choose a chapter and problem to begin.</span>
        </div>
        <div className="status">
          <span className="status-dot"></span>Learning workspace
        </div>
      </div>
    </aside>
  );
}

