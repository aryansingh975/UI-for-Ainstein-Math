const assert = require('node:assert/strict');
const { METHODS, canonicalMethod, interpretJevResponse, parseModelJson } = require('./server.js');

let passed = 0;

function check(name, actual, expected) {
  assert.deepEqual(actual, expected, name);
  passed++;
  console.log(`PASS | ${name}`);
}

for (const [methodKey, methodInfo] of Object.entries(METHODS)) {
  check(`maps ${methodKey} to its graph node`, interpretJevResponse({
    method: methodKey,
    confidence: 0.96,
    off_graph: false
  }), {
    status: 'selected',
    methodKey,
    methodId: methodInfo.nodeId,
    confidence: 0.96
  });
}

check('normalizes Jev choice labels', canonicalMethod('answer_quadratic-formula'), 'quadratic_formula');
check('routes high-confidence off-graph response to clarification', interpretJevResponse({
  method: 'factoring',
  confidence: 0.98,
  off_graph: true
}), { status: 'off_graph', confidence: 1 });
check('does not lock a low-confidence method', interpretJevResponse({
  method: 'factoring',
  confidence: 0.69,
  off_graph: false
}), { status: 'uncertain', confidence: 0.69 });
check('rejects an unknown choice', interpretJevResponse({
  method: 'guessing',
  confidence: 1,
  off_graph: false
}), { status: 'uncertain' });
check('parses JSON inside a fenced response', parseModelJson('```json\n{"method":{"type":"choice"}}\n```'), {
  method: { type: 'choice' }
});
assert.throws(() => parseModelJson('no structured result'), /did not return a JSON response/);
passed++;
console.log('PASS | rejects a response without JSON');
console.log(`\n=== RESULTS: ${passed} passed ===`);
