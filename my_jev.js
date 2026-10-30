// my_jev.js
// ─────────────────────────────────────────────────────────────────────────────
// "My Jev" — a local method detector for Ainstein. No SymPy, no API key, no AI.
//
// It answers the same question Jev answers: "Which solution method is the
// student using?" — and returns the same shape server_jev.js gets from Jev:
//   { status: 'selected' | 'uncertain' | 'off_graph',
//     methodKey, methodId, confidence,
//     probabilities: { method1: 0.91, method2: 0.06, method3: 0.03 },
//     off_graph: false }
//
// How it decides (all evidence comes from the problem's graph.json):
//   1. Each student line is compared with every method's accept lists
//      (the method node + all of its step nodes).
//   2. Each comparison gives a score from 0 to 1:
//        1.00  same text (ignoring spaces / case / ×, ÷, − symbols)
//        0.90  same definition                ("daughter = 0.2x" vs "daughter = x/5")
//        0.85  same equation, side by side   ("5x+6=3(x+6)" vs "5x + 6 = 3(x + 6)")
//        0.85  contains an accept entry       ("D = b^2 - 4ac" contains "b^2 - 4ac")
//        0.80  is part of an accept entry     ("x + 6" is part of "x + 6 and 5x + 6")
//        0.60  equation with this method's answer for x (x = 6 in Method 1, x = 30 in Method 2)
//        0.60  shares key words with an accept entry ("ratio", "units", "factor"…)
//        0.40  uses the same numbers as an accept entry
//   3. A line that fits several methods equally (a shared step) gives no
//      preference. Lines that fit only one method push its probability up.
//   4. Scores are turned into probabilities with a softmax. Nothing fits → off_graph.
// ─────────────────────────────────────────────────────────────────────────────
'use strict';

const fs = require('fs');
const path = require('path');

const CONFIDENCE_THRESHOLD = 0.7;   // same threshold the server uses for Jev
const SHARPNESS = 8;                // higher = more decisive probabilities
const OFF_GRAPH_SCORE = 0.35;       // best evidence below this → "not one of our methods"

// ─── 1. Text clean-up ───────────────────────────────────────────────────────
function clean(text) {
  return String(text).toLowerCase()
    .replace(/[−–—]/g, '-').replace(/×/g, '*').replace(/÷/g, '/')
    .replace(/²/g, '^2').replace(/’/g, "'")
    .replace(/\s+/g, ' ').trim();
}
const compact = text => clean(text).replace(/\s+/g, '');

const STOP_WORDS = new Set(('a an the is are of to and or so then we i my let be by in on at for with ' +
  'it this that its as from into find get have has do does use using now').split(' '));
function words(text) {
  return clean(text).replace(/[^a-z\s]/g, ' ').split(' ').filter(w => w.length >= 3 && !STOP_WORDS.has(w));
}
function numbers(text) {
  return (clean(text).match(/\d+(?:\.\d+)?/g) || []).map(Number);
}

// ─── 2. A small, safe maths evaluator (replaces SymPy for our needs) ─────────
// Handles + − * / ^ ( ), decimals, implicit multiplication (5x, 3(x+6), x/5) and
// single-letter variables. Returns null if the text is not an expression.
function prepare(expr) {
  let s = clean(expr);
  s = s.replace(/(\d)\s*([a-z(])/g, '$1*$2')        // 5x, 3(
       .replace(/\)\s*([a-z\d(])/g, ')*$1')         // )(, )x
       .replace(/\b([a-z])\s*\(/g, '$1*(')          // x(
       .replace(/\b([a-z])\s+([a-z])\b/g, '$1*$2'); // x y
  if (!/^[a-z0-9+\-*/^().\s]+$/.test(s)) return null;
  const letters = s.match(/[a-z]+/g) || [];
  if (letters.some(w => w.length > 1)) return null; // words left → not maths
  return { src: s, vars: new Set(letters) };
}

function evaluate(src, values) {
  const tokens = src.replace(/\s+/g, '').match(/\d+(?:\.\d+)?|[a-z]|[+\-*/^()]/g);
  if (!tokens || tokens.join('') !== src.replace(/\s+/g, '')) return null;
  let i = 0;
  const peek = () => tokens[i];
  function expr() {
    let v = term(); if (v === null) return null;
    while (peek() === '+' || peek() === '-') {
      const op = tokens[i++]; const r = term(); if (r === null) return null;
      v = op === '+' ? v + r : v - r;
    }
    return v;
  }
  function term() {
    let v = unary(); if (v === null) return null;
    while (peek() === '*' || peek() === '/') {
      const op = tokens[i++]; const r = unary(); if (r === null) return null;
      if (op === '/' && r === 0) return null;
      v = op === '*' ? v * r : v / r;
    }
    return v;
  }
  function unary() {
    if (peek() === '-') { i++; const v = unary(); return v === null ? null : -v; }
    if (peek() === '+') { i++; return unary(); }
    return power();
  }
  function power() {
    const b = atom(); if (b === null) return null;
    if (peek() === '^') { i++; const e = unary(); return e === null ? null : Math.pow(b, e); }
    return b;
  }
  function atom() {
    const t = tokens[i++];
    if (t === undefined) return null;
    if (/^\d/.test(t)) return parseFloat(t);
    if (/^[a-z]$/.test(t)) return values[t] === undefined ? null : values[t];
    if (t === '(') { const v = expr(); if (tokens[i++] !== ')') return null; return v; }
    return null;
  }
  const v = expr();
  return (v === null || i !== tokens.length || !Number.isFinite(v)) ? null : v;
}

const TRIALS = [3, 7.5, 11, 40];
function sameValue(a, b) {               // same value for every x?
  const pa = prepare(a), pb = prepare(b);
  if (!pa || !pb) return false;
  const vars = new Set([...pa.vars, ...pb.vars]);
  return TRIALS.every(t => {
    const values = {}; vars.forEach(v => { values[v] = t; });
    const va = evaluate(pa.src, values), vb = evaluate(pb.src, values);
    return va !== null && vb !== null && Math.abs(va - vb) <= 1e-6 * Math.max(1, Math.abs(vb));
  });
}

// "5x + 6 = 3x + 18" → ['5x + 6', '3x + 18'] if it is one equation with a variable
function splitEquation(text) {
  const parts = clean(text).split('=');
  if (parts.length !== 2 || !parts[0].trim() || !parts[1].trim()) return null;
  const l = prepare(parts[0]), r = prepare(parts[1]);
  if (!l || !r || new Set([...l.vars, ...r.vars]).size !== 1) return null;   // exactly one variable
  return [parts[0].trim(), parts[1].trim()];
}

// Solve a LINEAR equation numerically: f(x) = left − right is a straight line.
function linearRoot(eq) {
  const v = [...new Set([...prepare(eq[0]).vars, ...prepare(eq[1]).vars])][0];
  const f = x => { const o = { [v]: x };
    const l = evaluate(prepare(eq[0]).src, o), r = evaluate(prepare(eq[1]).src, o);
    return l === null || r === null ? null : l - r; };
  const f0 = f(0), f1 = f(1), f2 = f(2);
  if (f0 === null || f1 === null || f2 === null) return null;
  if (Math.abs((f2 - f1) - (f1 - f0)) > 1e-9 || Math.abs(f1 - f0) < 1e-12) return null; // not linear
  return -f0 / (f1 - f0);
}

// "daughter = x/5" / "mother is 5x" → { name, expr }
function splitDefinition(text) {
  const s = clean(text).replace(/'s\b/g, '');
  let parts = s.split('=');
  if (parts.length !== 2) { parts = s.split(/\bis\b/); if (parts.length !== 2) return null; }
  const name = parts[0].replace(/\b(let|the|present|current|now|age|ages|of|be|years?|old)\b/g, ' ')
    .replace(/\s+/g, ' ').trim();
  const expr = parts[1].replace(/\b(years?|old)\b/g, ' ').trim();
  if (!/^[a-z]{2,}( [a-z]{2,})?$/.test(name) || !prepare(expr)) return null;
  return { name, expr };
}

// ─── 3. Read the methods from a graph ───────────────────────────────────────
function methodsOf(graph) {
  const byId = new Map(graph.nodes.map(n => [n.id, n]));
  const next = id => (graph.edges.find(e => e.from === id) || {}).to;
  return graph.nodes.filter(n => n.type === 'method').map(m => {
    const accepts = [...(m.accept || [])];
    let id = next(m.id); const seen = new Set();
    while (id && !seen.has(id) && byId.get(id) && byId.get(id).type === 'step') {
      seen.add(id); accepts.push(...(byId.get(id).accept || [])); id = next(id);
    }
    // this method's value of x = the root of its first linear equation
    let root = null;
    for (const a of accepts) { const eq = splitEquation(a); if (eq) { root = linearRoot(eq); if (root !== null) break; } }
    return { id: m.id, label: m.label, accepts, root };
  });
}

// ─── 4. Score one student line against one method ───────────────────────────
function scoreLine(line, method) {
  let best = 0;
  const lineCompact = compact(line);
  const lineNoZero = lineCompact.replace(/=0$/, '');                // "(x-2)(x-3)=0" → "(x-2)(x-3)"
  const hasMaths = t => /[a-z]/.test(t) && /[+\-*/^=()]/.test(t);   // letters AND an operator
  const lineEq = splitEquation(line);
  const lineDef = splitDefinition(line);
  const lineWords = new Set(words(line));
  const lineNums = numbers(line);

  for (const a of method.accepts) {
    const ac = compact(a);
    if (ac === lineCompact || ac === lineNoZero) return 1;           // same text
    const d = lineDef && splitDefinition(a);
    if (d && d.name === lineDef.name && sameValue(lineDef.expr, d.expr)) best = Math.max(best, 0.9);
    const eq = lineEq && splitEquation(a);
    if (eq && sameValue(lineEq[0], eq[0]) && sameValue(lineEq[1], eq[1])) best = Math.max(best, 0.85);
    if (ac.length >= 4 && hasMaths(ac) && lineCompact.includes(ac)) best = Math.max(best, 0.85);   // line contains it
    if (lineCompact.length >= 3 && hasMaths(lineCompact) && !lineEq && ac.includes(lineCompact)) best = Math.max(best, 0.8); // part of it

    const aw = words(a);                                             // key words
    if (aw.length && lineWords.size) {
      const shared = aw.filter(w => lineWords.has(w) || [...lineWords].some(x => x.startsWith(w) || w.startsWith(x)));
      if (shared.length) best = Math.max(best, 0.6 * shared.length / Math.max(aw.length, lineWords.size));
    }
    const an = numbers(a);                                           // same numbers
    if (lineNums.length >= 2 && an.length >= 2 && lineNums.every(n => an.includes(n))) best = Math.max(best, 0.4);
  }
  if (lineEq && method.root !== null) {                              // gives this method's x
    const r = linearRoot(lineEq);
    if (r !== null && Math.abs(r - method.root) < 1e-6) best = Math.max(best, 0.6);
  }
  return best;
}

// ─── 5. Classify: lines → probabilities ─────────────────────────────────────
function classifyGraph(graph, studentWork, threshold = CONFIDENCE_THRESHOLD) {
  const methods = methodsOf(graph);
  const lines = String(studentWork).split(/\n|;/).map(s => s.trim()).filter(Boolean);
  const evidence = Object.fromEntries(methods.map(m => [m.id, 0]));
  let strongest = 0;

  for (const line of lines) {
    const scores = methods.map(m => scoreLine(line, m));
    const top = Math.max(...scores);
    strongest = Math.max(strongest, top);
    if (top === 0) continue;
    // a shared line (several methods score the same) adds no preference
    methods.forEach((m, i) => { evidence[m.id] += scores[i] - top; });
  }

  const ids = methods.map(m => m.id);
  const exps = ids.map(id => Math.exp(SHARPNESS * evidence[id]));
  const total = exps.reduce((a, b) => a + b, 0);
  const probabilities = Object.fromEntries(ids.map((id, i) => [id, Math.round(1000 * exps[i] / total) / 1000]));

  if (strongest < OFF_GRAPH_SCORE) {
    return { status: 'off_graph', confidence: 1 - strongest, probabilities, off_graph: true };
  }
  const bestId = ids.reduce((a, b) => (probabilities[a] >= probabilities[b] ? a : b));
  const confidence = probabilities[bestId];
  if (confidence < threshold) return { status: 'uncertain', confidence, probabilities, off_graph: false };
  return { status: 'selected', methodKey: bestId, methodId: bestId, confidence, probabilities, off_graph: false };
}

// ─── 6. Load every graph.json under solution_graph/ (same files the server reads) ─
function createLocalJev(rootDir) {
  const graphs = {};
  (function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name === 'graph.json' || entry.name.endsWith('.solution-graph.json')) {
        try {
          const g = JSON.parse(fs.readFileSync(full, 'utf8'));
          if (g.graph_meta && g.graph_meta.problem_uuid) graphs[g.graph_meta.problem_uuid] = g;
        } catch (e) { console.warn(`[my_jev] skipped ${full}: ${e.message}`); }
      }
    }
  })(rootDir);
  return {
    graphs,
    classify(problemId, studentWork, threshold) {
      const g = graphs[problemId];
      if (!g) throw Object.assign(new Error(`Unknown problem ${problemId}`), { status: 400, code: 'invalid_request' });
      return classifyGraph(g, studentWork, threshold);
    }
  };
}

module.exports = { classifyGraph, createLocalJev, scoreLine, methodsOf };
