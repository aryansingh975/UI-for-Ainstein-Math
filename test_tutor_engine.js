// ─────────────────────────────────────────────────────────────────────────────
// Test the tutor-engine: parser, safe evaluator, claim verification,
// 4-verdict classification, auto-conclusion, and full dialogue flows.
// Run: node test_tutor_engine.js
// ─────────────────────────────────────────────────────────────────────────────
const TutorEngine = require('./tutor-engine.js');
const graph = require('./solution_graph/g08-hegp107-ex001.solution-graph.json');

TutorEngine.init(graph);

let passed = 0;
let failed = 0;

function check(name, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (ok) { passed++; console.log(`PASS | ${name}`); }
  else {
    failed++;
    console.log(`FAIL | ${name} | expected=${JSON.stringify(expected)} got=${JSON.stringify(actual)}`);
  }
}

function approx(name, actual, expected) {
  const ok = actual !== null && Math.abs(actual - expected) < 1e-9;
  if (ok) { passed++; console.log(`PASS | ${name}`); }
  else { failed++; console.log(`FAIL | ${name} | expected=${expected} got=${actual}`); }
}

// ─── 1. Safe arithmetic evaluator ───
console.log('\n=== EVALUATOR TESTS ===');
approx('eval 3*96', TutorEngine.evalArithmetic('3*96'), 288);
approx('eval 72/24', TutorEngine.evalArithmetic('72/24'), 3);
approx('eval gcd(72,96)', TutorEngine.evalArithmetic('gcd(72,96)'), 24);
approx('eval hcf(72,96)', TutorEngine.evalArithmetic('hcf(72,96)'), 24);
approx('eval 2^3*3^2', TutorEngine.evalArithmetic('2^3*3^2'), 72);
approx('eval 2^5*3', TutorEngine.evalArithmetic('2^5*3'), 96);
approx('eval 3+4', TutorEngine.evalArithmetic('3+4'), 7);
approx('eval (3+4)*2', TutorEngine.evalArithmetic('(3+4)*2'), 14);
approx('eval 3/4', TutorEngine.evalArithmetic('3/4'), 0.75);
approx('eval 72/96', TutorEngine.evalArithmetic('72/96'), 0.75);
check('eval garbage returns null', TutorEngine.evalArithmetic('hello world'), null);
check('eval division by zero returns null', TutorEngine.evalArithmetic('5/0'), null);

// ─── 2. Claim extraction & truth-checking ───
// (extractClaims expects a NORMALIZED string, as produced by parseStep)
const norm = TutorEngine.normalizeText;
console.log('\n=== CLAIM TESTS ===');
let claims = TutorEngine.extractClaims(norm('gcd(72,96) is 25'));
check('gcd claim false', claims.map(c => c.isTrue), [false]);

claims = TutorEngine.extractClaims(norm('hcf is 24'));
check('bare hcf claim true', claims.map(c => c.isTrue), [true]);

claims = TutorEngine.extractClaims(norm('hcf of 72 and 96 is 24'));
check('hcf-of claim true', claims.map(c => c.isTrue), [true]);

claims = TutorEngine.extractClaims(norm('3:4=72:96'));
check('ratio equality true', claims.map(c => c.isTrue), [true]);

claims = TutorEngine.extractClaims(norm('3:4=3:5'));
check('ratio equality false', claims.map(c => c.isTrue), [false]);

claims = TutorEngine.extractClaims(norm('3+4=7'));
check('irrelevant but true claim', claims.map(c => c.isTrue), [true]);

claims = TutorEngine.extractClaims(norm('3*96=287'));
check('wrong product claim', claims.map(c => c.isTrue), [false]);

claims = TutorEngine.extractClaims(norm('72/24=3 and 96/24=4'));
check('two claims both true', claims.map(c => c.isTrue), [true, true]);

claims = TutorEngine.extractClaims(norm('72 = 24 × 3 and 96 = 24 × 4'));
check('multiplication-form claims true', claims.map(c => c.isTrue), [true, true]);

claims = TutorEngine.extractClaims(norm('3 times 96 is 288'));
check('word-form claim true', claims.map(c => c.isTrue), [true]);

claims = TutorEngine.extractClaims(norm('3:4 ≠ 72:96'));
check('negated ratio claim false', claims.map(c => c.isTrue), [false]);

// ─── 3. Dialogue flow tests (processStep + applyResult) ───
console.log('\n=== DIALOGUE FLOW TESTS ===');

function step(input, session) {
  const r = TutorEngine.processStep(input, session);
  TutorEngine.applyResult(session, r);
  return r;
}

// Flow A: clean HCF path → auto-completion
let s = TutorEngine.newSession();
check('A1 garbage rejected', step('i love paris , #:4', s).verdict, 'GARBAGE');
check('A2 irrelevant true flagged', step('3+4=7', s).verdict, 'IRRELEVANT_TRUE');
check('A3 wrong gcd corrected immediately', step('gcd(72,96) is 25', s).verdict, 'WRONG_CLAIM');
check('A4 correct gcd accepted (unlisted phrasing)', step('gcd(72,96) = 24', s).verdict, 'ACCEPT');
check('A4 method silently inferred', s.methodId, 'm1');
check('A5 divide step accepted', step('72/24=3 and 96/24=4', s).verdict, 'ACCEPT');
check('A6 simplified ratio accepted', step('3:4', s).verdict, 'ACCEPT');
check('A7 comparison accepted', step('3:4 = 3:4', s).verdict, 'ACCEPT');
check('A8 conclusion auto-detected', step('yes they are proportional', s).verdict, 'CONCLUSION_RIGHT');
check('A9 session completed', s.completed, true);

// Flow B: multiplication phrasing that the old matcher rejected
s = TutorEngine.newSession();
check('B1 72=24×3 accepted', step('72 = 24 × 3 and 96 = 24 × 4', s).verdict, 'ACCEPT');
check('B2 conclusion right', step('3:4 and 72:96 are proportional', s).verdict, 'CONCLUSION_RIGHT');

// Flow C: decimal method via value
s = TutorEngine.newSession();
check('C1 0.75 accepted', step('0.75', s).verdict, 'ACCEPT');
check('C2 decimal method inferred silently', s.methodId, 'm4');
check('C3 second decimal accepted', step('72/96 = 0.75', s).verdict, 'ACCEPT');
check('C4 comparison accepted', step('0.75 = 0.75', s).verdict, 'ACCEPT');
check('C5 conclusion right', step('yes', s).verdict, 'CONCLUSION_RIGHT');

// Flow D: cross multiplication with immediate correction
s = TutorEngine.newSession();
check('D1 288 accepted', step('288', s).verdict, 'ACCEPT');
check('D2 cross method inferred', s.methodId, 'm2');
check('D3 wrong product corrected', step('287', s).verdict, 'WRONG_CLAIM');
check('D4 corrected value accepted', step('288', s).verdict, 'ACCEPT');
check('D5 both products equal accepted', step('288 = 288', s).verdict, 'ACCEPT');
check('D6 conclusion right', step('they are proportional', s).verdict, 'CONCLUSION_RIGHT');

// Flow E: step-by-step reduction
s = TutorEngine.newSession();
check('E1 36:48 accepted', step('36:48', s).verdict, 'ACCEPT');
check('E2 reduce method inferred', s.methodId, 'm8');
check('E3 18:24 accepted', step('18:24', s).verdict, 'ACCEPT');
check('E4 9:12 accepted', step('9:12', s).verdict, 'ACCEPT');
check('E5 3:4 accepted', step('3:4', s).verdict, 'ACCEPT');
check('E6 conclusion right', step('yes they are proportional', s).verdict, 'CONCLUSION_RIGHT');

// Flow F: wrong conclusion (after reaching the conclusion point)
s = TutorEngine.newSession();
step('72/24=3 and 96/24=4', s);
step('3:4', s);
step('3:4 = 3:4', s);
check('F1 wrong conclusion detected', step('no', s).verdict, 'CONCLUSION_WRONG');
check('F2 not completed', s.completed, false);
check('F3 negated conclusion detected', step('they are not proportional', s).verdict, 'CONCLUSION_WRONG');

// Flow F2: bare yes/no mid-flow is NOT a conclusion (nudged instead)
s = TutorEngine.newSession();
step('72/24=3 and 96/24=4', s);
check('F4 mid-step bare no is not a conclusion', step('no', s).verdict, 'UNPARSED');

// Flow G: bare yes at start is nudged, not accepted as conclusion
s = TutorEngine.newSession();
check('G1 bare yes at start not a conclusion', step('yes', s).verdict, 'UNPARSED');

// Flow H: pure ratio-equality IS the conclusion
s = TutorEngine.newSession();
check('H1 3:4=72:96 completes the problem', step('3:4 = 72:96', s).verdict, 'CONCLUSION_RIGHT');

// Flow I: method keyword approach (silent)
s = TutorEngine.newSession();
const rI = step('cross multiply', s);
check('I1 keyword approach accepted', rI.verdict, 'ACCEPT');
check('I2 approachOnly flag set', rI.approachOnly, true);
check('I3 method locked silently', s.methodId, 'm2');
check('I4 first step accepted', step('3*96 and 4*72', s).verdict, 'ACCEPT');
check('I5 product accepted', step('3*96=288', s).verdict, 'ACCEPT');

// Flow J: garbage and off-topic
s = TutorEngine.newSession();
check('J1 garbage sentence rejected', step('i love paris 3:4', s).verdict, 'GARBAGE');
check('J2 hello world rejected', step('hello world', s).verdict, 'GARBAGE');

// Flow K: skip-ahead within a method (free order)
s = TutorEngine.newSession();
step('simplify', s);
check('K1 skip to comparison accepted', step('3:4 = 3:4', s).verdict, 'ACCEPT');
check('K2 conclusion right', step('yes they are proportional', s).verdict, 'CONCLUSION_RIGHT');

// Flow L: wrong value at current step (immediate correction, no expected leak)
s = TutorEngine.newSession();
step('simplify', s);
const rL = step('25', s);
check('L1 wrong HCF value flagged', rL.verdict, 'WRONG_CLAIM');
check('L2 fail streak incremented', s.failStreak, 1);
check('L3 corrected value accepted', step('24', s).verdict, 'ACCEPT');
check('L4 fail streak reset', s.failStreak, 0);

console.log(`\n=== RESULTS: ${passed} passed, ${failed} failed ===`);
process.exit(failed > 0 ? 1 : 0);