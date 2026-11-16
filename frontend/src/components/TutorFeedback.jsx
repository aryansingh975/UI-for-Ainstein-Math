import React from 'react';
import MethodProbabilities from './MethodProbabilities.jsx';

const PRAISE = [
  'Right step!',
  'Correct — keep going!',
  "Nice, that's right!",
  'Well done — next one!'
];

const PLAN_LABELS = {
  correct: '🟢 COMPLETE PLAN',
  partial: '🟡 PARTLY THERE',
  misconception: '🔴 CHECK THIS IDEA',
  contradiction: '🟡 TWO DIFFERENT IDEAS',
  dont_know: '🟡 LET’S BUILD THE PLAN',
  off_topic: '🟡 NOT A PLAN YET',
  explain: '🟡 ONE QUICK CHECK'
};

// Progress through the plan: ideas the student said (✓), ideas the tutor gave (✓ with "hint"), and the
// rest only as "one more step", so the checklist never gives the plan away
function PlanConcepts({ choice }) {
  const ideas = choice.concept_ideas || {};
  const found = choice.concepts_found || [];
  const given = (choice.concepts_given || []).filter((id) => !found.includes(id));
  const missing = (choice.concepts_missing || []).filter((id) => !given.includes(id));
  if (!found.length && !given.length) return null;   // nothing yet: no empty list
  const order = Object.keys(ideas);
  const done = [...found, ...given].sort((a, b) => order.indexOf(a) - order.indexOf(b));
  return (
    <ul className="plan-concepts">
      {done.map((id) => (
        <li key={id} className={given.includes(id) ? 'plan-concept given' : 'plan-concept found'}>
          ✓ {ideas[id] || id}{given.includes(id) && <span className="plan-concept-tag">with a hint</span>}
        </li>
      ))}
      {missing.map((id) => <li key={id} className="plan-concept">○ one more step</li>)}
    </ul>
  );
}

export default function TutorFeedback({ result, jevMessage, jevNote, onStartAgain }) {
  if (jevMessage) {
    const { label, message, stateClass = 'warn-state', probabilities, labels } = jevMessage;
    return (
      <section id="result" className="result-area" aria-live="polite">
        <article className={`answer-card ${stateClass}`}>
          <div className="answer-meta">{label}</div>
          <div className="tutor-bubble">
            <div className="tutor-speech">{message}</div>
          </div>
          <MethodProbabilities probabilities={probabilities} labels={labels} />
        </article>
      </section>
    );
  }

  if (!result || !result.verdict) return null;

  const v = result.verdict;
  const choice = result.choice;
  const praise = PRAISE[Math.floor(Math.random() * PRAISE.length)];
  const conclusionPrompt = result.conclusion_prompt || 'State your conclusion';
  const conclusionDesc = result.conclusion_description || 'Problem solved';
  // Shown under the step result when Jev has just identified the method
  const jevExtra = jevNote ? (
    <>
      <p className="answer-note">{jevNote.text}</p>
      <MethodProbabilities probabilities={jevNote.probabilities} labels={jevNote.labels} />
    </>
  ) : null;

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
          ) : choice ? (
            <>
              <div className="answer-meta">{choice.category === 'correct' ? PLAN_LABELS.correct : '🟢 PLAN READY'}</div>
              <h3>{choice.category === 'correct' ? praise : "Let's follow this plan."}</h3>
              <div className="tutor-bubble">
                <div className="tutor-speech">{choice.message}</div>
              </div>
              <PlanConcepts choice={choice} />
              <p>{result.active_label === 'Solve on Your Own'
                ? 'Now solve it on your own, one step per line. You will only hear from me if something is wrong.'
                : <>{result.method_label ? <>Path: <strong>{result.method_label}</strong>. </> : null}Answer the next question above.</>}</p>
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
          {jevExtra}
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
          {jevExtra}
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
          {jevExtra}
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
          {jevExtra}
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
          {jevExtra}
        </article>
      )}

      {v === 'PLAN_FEEDBACK' && choice && (
        <article className={`answer-card ${choice.category === 'misconception' ? 'failure-state' : 'warn-state'}`}>
          <div className="answer-meta">{PLAN_LABELS[choice.category] || '🟡 NOT QUITE'}</div>
          <div className="tutor-bubble">
            <div className="tutor-speech">{choice.message}</div>
          </div>
          <PlanConcepts choice={choice} />
          {choice.concept_hint && (
            <p className="tutor-hint-text">
              <strong>Hint {choice.concept_hint.id}:</strong> {choice.concept_hint.question}
            </p>
          )}
          {choice.concept_hint && <p className="retry-prompt">Think about the hint, then describe your plan again.</p>}
          {choice.category === 'explain' && <p className="retry-prompt">Answer in your own words. Then you'll solve it.</p>}
          {choice.category === 'partial' && !choice.concept_hint && <p className="retry-prompt">Answer the question above. What you've said so far is kept.</p>}
          {jevExtra}
        </article>
      )}

      {v === 'UNIT_ISSUE' && (
        <article className="answer-card warn-state">
          <div className="answer-meta">🟡 CHECK THE UNIT</div>
          <h3>Right number, but check the unit.</h3>
          <div className="tutor-bubble">
            <div className="tutor-speech">{result.feedback_message}</div>
          </div>
          <p className="retry-prompt">Write the step again with its unit (cm, cm³, g or kg).</p>
        </article>
      )}

      {v === 'PART' && (
        <article className="answer-card warn-state">
          <div className="answer-meta">🧭 PART</div>
          <div className="tutor-bubble">
            <div className="tutor-speech">{result.feedback_message}</div>
          </div>
        </article>
      )}

      {v === 'WORKING' && (
        <article className="answer-card success-state">
          <div className="answer-meta">🟢 GOOD STEP</div>
          <div className="tutor-bubble">
            <div className="tutor-speech">{result.feedback_message}</div>
          </div>
          {result.hint && <p className="tutor-hint-text">Hint: {result.hint}</p>}
          <p className="retry-prompt">Keep going, or write the full answer when you have it.</p>
        </article>
      )}

      {v === 'DONT_KNOW' && (
        <article className="answer-card warn-state">
          <div className="answer-meta">🟡 LET'S LOOK AT THIS</div>
          <div className="tutor-bubble">
            <div className="tutor-speech">{result.feedback_message}</div>
          </div>
          {result.hint && <p className="tutor-hint-text">Hint: {result.hint}</p>}
          <p className="retry-prompt">Use this, then try the question again.</p>
        </article>
      )}

      {v === 'WRONG_ANSWER' && (
        <article className="answer-card warn-state">
          <div className="answer-meta">🟡 NOT QUITE</div>
          <h3>That's not the answer to this question yet.</h3>
          {result.hint && <p className="tutor-hint-text">Hint: {result.hint}</p>}
          <p className="retry-prompt">Read the question again and try once more.</p>
          {jevExtra}
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
          {jevExtra}
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
          {jevExtra}
        </article>
      )}
    </section>
  );
}

