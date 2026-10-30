// test_my_jev.js — run:  node test_my_jev.js
// Checks "My Jev" against real student lines from the three Jev problems.
const path = require('path');
const { createLocalJev } = require('./my_jev');

const ROOT = process.argv[2] || path.join(__dirname, 'solution_graph');
const jev = createLocalJev(ROOT);

// [problem, student work (lines separated by \n), expected: method id | 'uncertain' | 'off_graph']
const cases = [
  ['g08-hegp206-age-q7', 'mother = 5x', 'method1'],
  ['g08-hegp206-age-q7', 'daughter = x', 'method1'],
  ['g08-hegp206-age-q7', '5x + 6 = 3(x + 6)', 'method1'],
  ['g08-hegp206-age-q7', '5x+6=3x+18', 'method1'],
  ['g08-hegp206-age-q7', 'mother = x', 'method2'],
  ['g08-hegp206-age-q7', 'daughter = x/5', 'method2'],
  ['g08-hegp206-age-q7', 'daughter = 0.2x', 'method2'],
  ['g08-hegp206-age-q7', 'x + 6 = 3x/5 + 18', 'method2'],
  ['g08-hegp206-age-q7', '5 - 1 = 4', 'method3'],
  ['g08-hegp206-age-q7', 'ratio method', 'method3'],
  ['g08-hegp206-age-q7', '1 unit = 6 years', 'method3'],
  ['g08-hegp206-age-q7', 'x + 6', 'uncertain'],                 // shared by Methods 1 and 2
  ['g08-hegp206-age-q7', 'x + 6\n5x + 6 = 3(x + 6)', 'method1'], // shared line, then a clear one
  ['g08-hegp206-age-q7', 'I like pizza', 'off_graph'],

  ['g08-lin-ex003', '3x - 6 + 5 = 2x + 4', 'uncertain'],         // first step is shared
  ['g08-lin-ex003', '3x - 6 + 5 = 2x + 4\n3x - 2x = 4 + 1', 'm1_transpose'],
  ['g08-lin-ex003', '3x - 1 - 2x = 2x + 4 - 2x', 'm2_balance'],
  ['g08-lin-ex003', 'subtract 2x from both sides', 'm2_balance'],
  ['g08-lin-ex003', 'try x = 3', 'm3_trial'],

  // (x-2)(x-3) is written in BOTH Factoring (m1_s3) and Trial (m6_s3) in the graph → truly shared
  ['g10-quad-ex001', '(x - 2)(x - 3) = 0', 'uncertain'],
  ['g10-quad-ex001', 'x^2 - 2x - 3x + 6\n(x - 2)(x - 3) = 0', 'm1_factor'],
  ['g10-quad-ex001', 'x^2 - 2x - 3x + 6', 'm1_factor'],
  ['g10-quad-ex001', 'D = b^2 - 4ac', 'm2_formula'],
  ['g10-quad-ex001', 'complete the square', 'm3_square'],
  ['g10-quad-ex001', 'x^2 - 5x + 25/4 = 1/4', 'm3_square'],
  ['g10-quad-ex001', 'sum of roots = 5', 'm5_vieta'],
  ['g10-quad-ex001', 'f(2) = 0', 'm6_trial'],
];

let pass = 0;
for (const [problem, work, expected] of cases) {
  const r = jev.classify(problem, work);
  const got = r.status === 'selected' ? r.methodId : r.status;
  const ok = got === expected;
  if (ok) pass++;
  const top = Object.entries(r.probabilities).sort((a, b) => b[1] - a[1]).slice(0, 3)
    .map(([k, v]) => `${k} ${Math.round(v * 100)}%`).join(', ');
  console.log(`${ok ? 'PASS' : 'FAIL'} | ${work.replace(/\n/g, ' ⏎ ').padEnd(42)} | expected ${String(expected).padEnd(12)} got ${String(got).padEnd(12)} | ${top}`);
}
console.log(`\n${pass}/${cases.length} correct`);

// Lines that are NOT written in any graph (maths matching must do the work)
const extra = [
  ['g08-hegp206-age-q7', '5y + 6 = 3(y + 6)', 'method1'],        // different letter
  ['g08-hegp206-age-q7', '5x + 6 = 3*x + 18', 'method1'],
  ['g08-hegp206-age-q7', 'x + 6 = 0.6x + 18', 'method2'],
  ['g08-hegp206-age-q7', '5(x + 6) = 3x + 90', 'method2'],
  ['g08-lin-ex003', '3(x-2) + 5 - 2x = 4', 'm2_balance'],     // 2x subtracted from both sides = balancing
];
let extraPass = 0;
for (const [problem, work, expected] of extra) {
  const r = jev.classify(problem, work);
  const got = r.status === 'selected' ? r.methodId : r.status;
  if (got === expected) extraPass++;
  console.log(`${got === expected ? 'PASS' : 'FAIL'} | ${work.padEnd(42)} | expected ${String(expected).padEnd(12)} got ${got}`);
}
console.log(`${extraPass}/${extra.length} unseen lines correct`);
