import React, { useRef, useMemo } from 'react';
import katex from 'katex';

function formatLatexString(raw) {
  let text = (raw || '').trim();
  if (!text) return '';
  return text
    .replace(/\*/g, ' \\times ')
    .replace(/x(?=\s*\d)/g, ' \\times ')
    .replace(/==/g, ' = ');
}

const MATH_BUTTONS = [
  { label: '\\times', insert: '\\times' },
  { label: '\\div', insert: '\\div' },
  { label: '\\frac{a}{b}', insert: '\\frac{a}{b}' },
  { label: ':', insert: ' : ' },
  { label: ' = ', insert: ' = ' },
  { label: '\\neq', insert: '\\neq' },
  { label: '\\implies', insert: '\\implies' },
  { label: '\\text{proportional}', insert: '\\text{proportional}' }
];

function HistoryItem({ turn, input, isCorrect, verdict, feedback }) {
  const rendered = useMemo(() => {
    try {
      const formatted = formatLatexString(input);
      return katex.renderToString(formatted, { throwOnError: false, displayMode: false });
    } catch {
      return input;
    }
  }, [input]);

  const isWarn = verdict === 'IRRELEVANT_TRUE' || verdict === 'GARBAGE';
  const badgeClass = isCorrect
    ? 'live-trail-badge live-trail-badge-correct'
    : isWarn
    ? 'live-trail-badge live-trail-badge-warn'
    : 'live-trail-badge live-trail-badge-wrong';

  const badgeIcon = isCorrect ? '✓' : isWarn ? '⚠' : '✗';
  const itemClass = isCorrect
    ? 'live-trail-item live-trail-item-correct'
    : 'live-trail-item live-trail-item-wrong';

  return (
    <div className={itemClass}>
      <div className="live-trail-main-row">
        <span className={badgeClass}>{badgeIcon} Turn {turn}</span>
        <span className="live-trail-text" dangerouslySetInnerHTML={{ __html: rendered }} />
      </div>
      {!isCorrect && feedback && (
        <div className="live-trail-feedback">
          <span className="live-trail-feedback-arrow">↳</span>
          <span className="live-trail-feedback-text">{feedback}</span>
        </div>
      )}
    </div>
  );
}

export default function WorkspacePanel({
  stepLabel,
  isCompleted,
  methodIndicator,
  trail = [],
  history = [],
  input,
  onInputChange,
  placeholder,
  onResetProblem,
  onCheckStep,
  isChecking,
  checkButtonText
}) {
  const textareaRef = useRef(null);

  const historyItems = useMemo(() => {
    if (history && history.length > 0) {
      return history;
    }
    if (trail && trail.length > 0) {
      return trail.map((t, idx) => ({
        turn: idx + 1,
        input: t.input,
        is_correct: true,
        verdict: 'ACCEPT',
        feedback: null
      }));
    }
    return [];
  }, [history, trail]);

  const verifiedCount = useMemo(
    () => historyItems.filter((item) => item.is_correct).length,
    [historyItems]
  );

  const renderedLatexHtml = useMemo(() => {
    const raw = (input || '').trim();
    if (!raw) return null;
    const latex = formatLatexString(raw);
    try {
      return katex.renderToString(latex, { throwOnError: false, displayMode: true });
    } catch {
      return latex;
    }
  }, [input]);

  const handleInsertMath = (insertText) => {
    const el = textareaRef.current;
    if (!el) {
      onInputChange((input || '') + insertText);
      return;
    }
    const start = el.selectionStart || 0;
    const end = el.selectionEnd || 0;
    const current = el.value || '';
    const next = current.substring(0, start) + insertText + current.substring(end);
    onInputChange(next);
    setTimeout(() => {
      el.focus();
      el.setSelectionRange(start + insertText.length, start + insertText.length);
    }, 0);
  };

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      onCheckStep();
    }
  };

  return (
    <section className="query-panel" aria-label="Student reasoning input">
      <div className="panel-top">
        <div>
          <span className="panel-label">YOUR STEP / REASONING</span>
          <span className="panel-hint">Supports LaTeX or plain math notation</span>
        </div>
        <div className="step-indicator-bar" id="step-indicator">
          <span>ACTIVE:</span>
          <span className={isCompleted ? 'step-dot-done' : 'step-dot-active'} id="step-dot-1"></span>
          <span id="step-label">{stepLabel || 'Step 1'}</span>
          {methodIndicator && (
            <span id="method-indicator">{methodIndicator}</span>
          )}
        </div>
      </div>

      {/* Live Conversation & Reasoning History Tracker */}
      {historyItems.length > 0 && (
        <div className="live-trail-wrap">
          <div className="live-trail-header">
            <span>
              📋 Conversation & Reasoning History ({verifiedCount} verified · {historyItems.length} {historyItems.length === 1 ? 'turn' : 'turns'})
            </span>
          </div>
          <div className="live-trail-list">
            {historyItems.map((item, idx) => (
              <HistoryItem
                key={idx}
                turn={item.turn || idx + 1}
                input={item.input}
                isCorrect={item.is_correct}
                verdict={item.verdict}
                feedback={item.feedback}
              />
            ))}
          </div>
        </div>
      )}

      {/* LaTeX Math Toolbar Helper */}
      <div className="math-toolbar">
        <span className="math-toolbar-label">Math Palette:</span>
        {MATH_BUTTONS.map((btn, idx) => (
          <button
            key={idx}
            type="button"
            className="math-btn"
            onClick={() => handleInsertMath(btn.insert)}
          >
            {btn.label}
          </button>
        ))}
      </div>

      <textarea
        ref={textareaRef}
        id="question-input"
        rows={3}
        placeholder={placeholder || 'Type your next step…'}
        spellCheck="false"
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isCompleted}
      />

      {/* Live LaTeX Render Preview Box */}
      <div className="latex-preview-wrap">
        <div className="latex-preview-header">
          <span>Live Rendered LaTeX Math</span>
          <span id="preview-mode-tag">KaTeX Auto-render</span>
        </div>
        {renderedLatexHtml ? (
          <div
            id="latex-preview"
            className="latex-preview-body"
            dangerouslySetInnerHTML={{ __html: renderedLatexHtml }}
          />
        ) : (
          <div id="latex-preview" className="latex-preview-body empty">
            Type math above to see rendered LaTeX here...
          </div>
        )}
      </div>

      <div className="query-footer">
        <div className="example-prompt">
          <button
            type="button"
            className="example-link"
            id="reset-flow-btn"
            onClick={onResetProblem}
          >
            ↺ Reset Problem State
          </button>
        </div>
        <button
          id="solve-button"
          className="solve-button"
          type="button"
          onClick={onCheckStep}
          disabled={isChecking || isCompleted}
        >
          {checkButtonText || 'Check Step'} <span>→</span>
        </button>
      </div>
    </section>
  );
}

