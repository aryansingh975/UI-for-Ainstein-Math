import React from 'react';

const PRAISE = [
  'Right step!',
  'Correct — keep going!',
  "Nice, that's right!",
  'Well done — next one!'
];

export default function TutorFeedback({ result, jevMessage, onStartAgain }) {
  if (jevMessage) {
    const { label, message, stateClass = 'warn-state' } = jevMessage;
    return (
      <section id="result" className="result-area" aria-live="polite">
        <article className={`answer-card ${stateClass}`}>
          <div className="answer-meta">{label}</div>
          <div className="tutor-bubble">
            <div className="tutor-speech">{message}</div>
          </div>
        </article>
      </section>
    );
  }

  if (!result || !result.verdict) return null;

  const v = result.verdict;
  const praise = PRAISE[Math.floor(Math.random() * PRAISE.length)];
  const conclusionPrompt = result.conclusion_prompt || 'State your conclusion';
  const conclusionDesc = result.conclusion_description || 'Problem solved';

  return (
    <section id="result" className="result-area" aria-live="polite">
      {v === 'ACCEPT' && (
        <article className="answer-card success-state">
          {result.approach_only ? (
            <>
              <div className="answer-meta">🟢 GOOD APPROACH</div>
              <h3>Good approach!</h3>
              <div className="tutor-bubble">
                <div className="tutor-speech">"Great — now show me your first step. Work it out one calculation at a time."</div>
              </div>
              <p className="retry-prompt">Type your first calculation above.</p>
            </>
          ) : (
            <>
              <div className="answer-meta">🟢 STEP VERIFIED</div>
              <h3>{praise}</h3>
              <div className="tutor-bubble">
                <div className="tutor-speech">"{result.parsed_input}" — that's correct.</div>
              </div>
              <p>
                {result.next_is_conclusion
                  ? <>Now give your final conclusion: <strong>{conclusionPrompt}</strong></>
                  : "What's your next step?"}
              </p>
            </>
          )}
        </article>
      )}

      {v === 'CONCLUSION_RIGHT' && (
        <article className="answer-card success-state">
          <div className="answer-meta">🟢 PROBLEM COMPLETED · VALID SOLUTION</div>
          <h3>Excellent — solved!</h3>
          <div className="tutor-bubble">
            <div className="tutor-speech">{result.feedback_message || conclusionDesc} Your solution is complete.</div>
          </div>

          {result.trail && result.trail.length > 0 && (
            <div className="steps">
              {result.trail.map((t, idx) => (
                <div key={idx} className="step">
                  <b>✓</b>{t.input}
                </div>
              ))}
            </div>
          )}

          {(!result.trail || result.trail.length <= 1) && (
            <p className="answer-note">You stated the conclusion directly — for practice, try showing the steps too!</p>
          )}

          <div style={{ marginTop: '14px' }}>
            <button
              type="button"
              className="preset-chip"
              onClick={onStartAgain}
            >
              ↺ Start Again
            </button>
          </div>
        </article>
      )}

      {v === 'CONCLUSION_WRONG' && (
        <article className="answer-card failure-state">
          <div className="answer-meta">🔴 CONCLUSION DOESN'T HOLD</div>
          <h3>That conclusion isn't right.</h3>
          <div className="tutor-bubble">
            <div className="tutor-speech">Your conclusion does not match this problem. Recheck your reasoning and try again.</div>
          </div>
          {result.hint && <p className="tutor-hint-text">Hint: {result.hint}</p>}
          <p className="retry-prompt">Recheck your steps above, then state your conclusion again.</p>
        </article>
      )}

      {v === 'WRONG_CLAIM' && (
        <article className="answer-card failure-state">
          <div className="answer-meta">🔴 MISTAKE IN THIS STEP</div>
          <h3>This step has a mistake.</h3>
          <div className="tutor-bubble">
            <div className="tutor-speech">
              "🔴 {result.explanation || 'This step contains an error.'} Fix this step and try it again."
            </div>
          </div>
          {result.hint && <p className="tutor-hint-text">Hint: {result.hint}</p>}
          <p className="retry-prompt">Correct this step — the tutor will continue from here.</p>
        </article>
      )}

      {v === 'IRRELEVANT_TRUE' && (
        <article className="answer-card warn-state">
          <div className="answer-meta">🟡 TRUE — BUT NOT WHAT WE NEED</div>
          <h3>That's correct math, but it doesn't answer the question.</h3>
          <div className="tutor-bubble">
            <div className="tutor-speech">
              "{result.parsed_input} is true, but it does not yet help answer this question. Connect your step to the quantities in the problem."
            </div>
          </div>
          <p className="retry-prompt">Return to the question.</p>
        </article>
      )}

      {v === 'GARBAGE' && (
        <article className="answer-card failure-state">
          <div className="answer-meta">🔴 NOT A MATH STEP</div>
          <h3>I need an actual math step.</h3>
          <div className="tutor-bubble">
            <div className="tutor-speech">"That does not look related to this problem. Try a calculation or explain a method for the question above."</div>
          </div>
          <p className="retry-prompt">Type a calculation or an approach above.</p>
        </article>
      )}

      {v === 'UNPARSED' && (
        <article className="answer-card warn-state">
          <div className="answer-meta">🟡 COULDN'T FOLLOW THAT</div>
          <h3>I couldn't follow that as a math step.</h3>
          <div className="tutor-bubble">
            <div className="tutor-speech">"Try writing a calculation or mathematical relationship that helps answer this question."</div>
          </div>
          <p className="retry-prompt">Type your step as a calculation above.</p>
        </article>
      )}
    </section>
  );
}

