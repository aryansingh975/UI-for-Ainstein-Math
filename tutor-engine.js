// tutor-engine.js
// ─────────────────────────────────────────────────────────────────────────────
// Ainstein Step-Understanding Engine — 100% deterministic JS (no LLM, no eval)
//
// Layers:
//   1. parseStep()      — tokenizes student input into structured math objects
//   2. evalArithmetic() — safe recursive-descent evaluator (gcd/hcf/lcm/sqrt…)
//   3. extractClaims()  — finds every mathematical claim and checks its TRUTH
//   4. processStep()    — 4-verdict classifier + auto-conclusion detection
//   5. applyResult()    — single source of truth for session state transitions
//
// Verdicts:
//   ACCEPT           — step is relevant AND mathematically true
//   WRONG_CLAIM      — step contains false math → immediate correction
//   IRRELEVANT_TRUE  — math is true but doesn't help answer the question
//   GARBAGE          — off-topic / no math content
//   UNPARSED         — relevant words but nothing checkable
//   CONCLUSION_RIGHT — final answer, correct → tutor declares completion
//   CONCLUSION_WRONG — final answer, incorrect → tutor pushes back
//
// Runs in the browser (window.TutorEngine) and Node (module.exports).
// ─────────────────────────────────────────────────────────────────────────────

(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TutorEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const EPS = 1e-9;

  // ─── Module state (set by init) ───
  let GRAPH = null;   // solution graph { nodes, edges, ... }
  let CTX = null;     // problem context { first: [a,b], second: [c,d] }
  let NODE_MAP = null;
  let CONCLUSION_ID = null;

  function init(graph, context) {
    GRAPH = graph;
    CTX = context || parseContextFromGraph(graph) || { first: [3, 4], second: [72, 96] };
    NODE_MAP = new Map(graph.nodes.map(n => [n.id, n]));
    const concl = graph.nodes.find(n => n.type === 'conclusion');
    CONCLUSION_ID = (graph.conclusion_node) || (concl && concl.id) || 'conclusion';
  }

  function parseContextFromGraph(graph) {
    const text = (graph.graph_meta && graph.graph_meta.problem_text) || '';
    const m = text.match(/(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)[^\d]+(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)/);
    if (m) return { first: [+m[1], +m[2]], second: [+m[3], +m[4]] };
    return null;
  }

  function getNode(nodeId) {
    return (NODE_MAP && NODE_MAP.get(nodeId)) || null;
  }

  function newSession() {
    return { trail: [], currentNodeId: null, methodId: null, failStreak: 0, completed: false };
  }

  // ─── Text normalization (synced with the accept-list matcher) ───
  function normalizeText(value) {
    return String(value).toLowerCase()
      .replace(/\s+/g, ' ')
      .replace(/\s*:\s*/g, ':')
      .replace(/\s*×\s*/g, '*')
      .replace(/\bx\b/g, '*')
      .replace(/\s*÷\s*/g, '/')
      .replace(/\s*=\s*/g, '=')
      .replace(/\s*->\s*/g, '->')
      .replace(/[.,!;?]+$/g, '')
      .trim();
  }

  function stripConnectingWords(text) {
    return String(text).replace(/\b(i|love|paris|the|a|an|and|is|are|so|then|therefore|hence|thus|we|can|get|have|has|of|to|for|it|that|this|my|me|you|your|with)\b/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  // ─── Relevance vocabulary ───
  const RELEVANT_WORDS = new Set([
    'i','a','an','the','and','or','so','if','then','thus','hence','therefore',
    'is','are','am','was','were','be','been','being','do','does','did','done',
    'can','will','would','should','shall','may','might','must',
    'we','us','our','you','your','my','me','it','its','they','them','their',
    'this','that','these','those','there','here','of','to','for','with','by',
    'in','on','at','as','from','into','both','each','per',
    'get','got','have','has','had','give','gives','given','use','used','using','after',
    'check','see','find','found','try','tries','trying','want','wants','let',
    'lets','think','okay','ok','yes','no','not','now','first','next','last',
    'final','because','since','when','make','makes','made','means','mean',
    'know','known','suppose','supposed','maybe','please',
    'first','second','explain','show','calculate','multiple',
    'equal','equals','same','identical','match','matches','matched','matching',
    'ratio','ratios','proportional','proportion','proportions',
    'fraction','fractions','numerator','denominator','numerators','denominators',
    'hcf','gcd','highest','common','factor','factors','factorization',
    'factorise','factorize','factorised','factorized','prime','primes',
    'simplest','simple','simplify','simplified','simplifies','simplifying',
    'cancel','cancels','canceled','cancelled','canceling','cancelling',
    'reduce','reduced','reduces','reducing','reduction',
    'divide','divided','divides','dividing','division','divisor','dividend',
    'multiply','multiplied','multiplies','multiplying','multiplication',
    'times','product','products','scale','scaled','scales','scaling',
    'decimal','decimals','equivalent','equivalence',
    'value','values','result','results','answer','answers','term','terms',
    'number','numbers','step','steps','method','methods','approach','over',
    'cross','form','side','sides',
    'one','two','three','four','five','six','seven','eight','nine','ten',
    'quarter','quarters','half','halves','third','thirds'
  ]);

  const MATH_INTENT = new Set([
    'hcf','gcd','simplify','simplified','simplifies','simplifying','simplest',
    'cross','multiply','multiplied','multiplication','scale','scaled','scaling',
    'decimal','decimals','fraction','fractions','prime','factorization',
    'factorize','factorise','equivalent','reduce','reduced','reduction',
    'proportional','proportion','ratio','ratios','divide','divided','division',
    'equal','equals','same','identical','yes','no','not','times','product'
  ]);

  function hasIrrelevantWords(normalizedInput, normalizedAccepted) {
    const inputWords = normalizedInput.split(/[^a-z]+/).filter(Boolean);
    if (inputWords.length === 0) return false;
    const acceptedWords = normalizedAccepted.split(/[^a-z]+/).filter(Boolean);
    const acceptedIsKeyword = /^[a-z]+$/.test(normalizedAccepted) && normalizedAccepted.length >= 3;
    for (const word of inputWords) {
      if (RELEVANT_WORDS.has(word)) continue;
      if (acceptedWords.some(aw =>
        (aw.length >= 3 && word.startsWith(aw)) ||
        (word.length >= 3 && aw.startsWith(word))
      )) continue;
      if (acceptedIsKeyword && word.startsWith(normalizedAccepted)) continue;
      return true;
    }
    return false;
  }

  // ─── Accept-list matcher (fast path; synced with test_solution_graph.js) ───
  function matchesAccept(rawInput, acceptedAnswer) {
    const normalizedInput = normalizeText(rawInput);
    const normalizedAccepted = normalizeText(acceptedAnswer);

    if (normalizedInput === normalizedAccepted) return true;
    if (hasIrrelevantWords(normalizedInput, normalizedAccepted)) return false;

    if (/^[a-z]+$/.test(normalizedAccepted) && normalizedAccepted.length >= 3) {
      if (normalizedInput.includes(normalizedAccepted)) return true;
      const inputWords = normalizedInput.split(' ');
      for (const word of inputWords) {
        if (word.startsWith(normalizedAccepted)) return true;
      }
    }

    if (/^[\d.]*$/.test(normalizedAccepted) && normalizedAccepted.length > 0) {
      const inputNumbers = normalizedInput.match(/(\d+(?:\.\d+)?)/g);
      if (normalizedInput === normalizedAccepted) return true;
      if (inputNumbers && inputNumbers.length === 1 && inputNumbers[0] === normalizedAccepted) {
        const words = normalizedInput.split(' ');
        if (words.length <= 3) {
          const nonNumericWords = words.filter(w => !/^\d+(?:\.\d+)?$/.test(w));
          if (nonNumericWords.every(w => w.length <= 6)) return true;
        }
      }
      return false;
    }

    if (/^\d+:\d+$/.test(normalizedAccepted)) {
      return normalizedInput === normalizedAccepted;
    }

    if (/^\d+\/\d+$/.test(normalizedAccepted)) {
      return normalizedInput === normalizedAccepted;
    }

    const inputNumbers = normalizedInput.match(/(\d+(?:\.\d+)?)/g);
    const acceptedNumbers = normalizedAccepted.match(/(\d+(?:\.\d+)?)/g);

    if (acceptedNumbers && acceptedNumbers.length > 1 && inputNumbers) {
      if (inputNumbers.join(',') !== acceptedNumbers.join(',')) return false;
      const acceptedHasOperator = /[/*=÷×]/.test(normalizedAccepted);
      if (!acceptedHasOperator) return false;
      const hasOperator = /[/*=÷×]/.test(normalizedInput);
      if (!hasOperator) return false;
      return true;
    }

    if (/[a-z]/.test(normalizedAccepted)) {
      const stripped = normalizeText(stripConnectingWords(rawInput));
      if (stripped === normalizedAccepted) return true;
    }

    return false;
  }

  function matchesAcceptAny(rawInput, accepts) {
    return (accepts || []).some(a => matchesAccept(rawInput, a));
  }

  // ─── Safe arithmetic evaluator (recursive descent — NO eval) ───
  function gcdInt(a, b) {
    a = Math.abs(Math.round(a)); b = Math.abs(Math.round(b));
    while (b) { const t = a % b; a = b; b = t; }
    return a;
  }

  function applyFn(name, args) {
    switch (name) {
      case 'gcd': case 'hcf':
        if (args.length < 2) return null;
        return args.reduce((x, y) => gcdInt(x, y));
      case 'lcm':
        if (args.length < 2) return null;
        return args.reduce((x, y) => Math.abs(x * y) / gcdInt(x, y));
      case 'sqrt':
        return (args.length === 1 && args[0] >= 0) ? Math.sqrt(args[0]) : null;
      case 'abs':
        return args.length === 1 ? Math.abs(args[0]) : null;
      case 'min': return args.length ? Math.min.apply(null, args) : null;
      case 'max': return args.length ? Math.max.apply(null, args) : null;
      default: return null;
    }
  }

  function tokenizeMath(src) {
    const tokens = [];
    const s = String(src);
    let i = 0;
    while (i < s.length) {
      const ch = s[i];
      if (/\s/.test(ch)) { i++; continue; }
      if (/\d|\./.test(ch)) {
        let j = i;
        while (j < s.length && /[\d.]/.test(s[j])) j++;
        const v = parseFloat(s.slice(i, j));
        if (isNaN(v)) return null;
        tokens.push({ t: 'num', v });
        i = j;
        continue;
      }
      if (/[a-zA-Z]/.test(ch)) {
        let j = i;
        while (j < s.length && /[a-zA-Z]/.test(s[j])) j++;
        tokens.push({ t: 'id', v: s.slice(i, j).toLowerCase() });
        i = j;
        continue;
      }
      if ('+-*/^(),'.indexOf(ch) !== -1) { tokens.push({ t: ch }); i++; continue; }
      return null; // unknown character → not evaluable
    }
    return tokens;
  }

  function evalArithmetic(src) {
    const tokens = tokenizeMath(src);
    if (!tokens || tokens.length === 0) return null;
    let pos = 0;
    function peek() { return tokens[pos]; }
    function next() { return tokens[pos++]; }

    function parseExpr() {
      let v = parseTerm();
      if (v === null) return null;
      while (peek() && (peek().t === '+' || peek().t === '-')) {
        const op = next().t;
        const r = parseTerm();
        if (r === null) return null;
        v = (op === '+') ? v + r : v - r;
      }
      return v;
    }
    function parseTerm() {
      let v = parseFactor();
      if (v === null) return null;
      while (peek() && (peek().t === '*' || peek().t === '/')) {
        const op = next().t;
        const r = parseFactor();
        if (r === null) return null;
        if (op === '/') {
          if (Math.abs(r) < EPS) return null;
          v = v / r;
        } else {
          v = v * r;
        }
      }
      return v;
    }
    function parseFactor() {
      if (peek() && peek().t === '-') { next(); const v = parseFactor(); return v === null ? null : -v; }
      if (peek() && peek().t === '+') { next(); return parseFactor(); }
      return parsePower();
    }
    function parsePower() {
      const base = parsePrimary();
      if (base === null) return null;
      if (peek() && peek().t === '^') {
        next();
        const e = parseFactor();
        if (e === null) return null;
        return Math.pow(base, e);
      }
      return base;
    }
    function parsePrimary() {
      const tk = peek();
      if (!tk) return null;
      if (tk.t === 'num') { next(); return tk.v; }
      if (tk.t === '(') {
        next();
        const v = parseExpr();
        if (v === null) return null;
        if (!peek() || peek().t !== ')') return null;
        next();
        return v;
      }
      if (tk.t === 'id') {
        next();
        if (peek() && peek().t === '(') {
          next();
          const args = [];
          if (peek() && peek().t !== ')') {
            let a = parseExpr();
            if (a === null) return null;
            args.push(a);
            while (peek() && peek().t === ',') {
              next();
              a = parseExpr();
              if (a === null) return null;
              args.push(a);
            }
          }
          if (!peek() || peek().t !== ')') return null;
          next();
          return applyFn(tk.v, args);
        }
        return null; // bare identifier is not evaluable
      }
      return null;
    }

    const v = parseExpr();
    if (v === null || pos !== tokens.length) return null;
    return v;
  }

  // Rewrite "hcf of 72 and 96" → "gcd(72,96)"; bare "hcf"/"gcd" → gcd(ctx)
  function preprocessGcdPhrases(s) {
    s = s.replace(/\b(?:highest common factor|greatest common divisor|hcf|gcd)\b(?:\s*of\s*)?(\d+(?:\.\d+)?)\s*(?:,|and)\s*(\d+(?:\.\d+)?)/g,
      'gcd($1,$2)');
    return s;
  }

  function canonicalizeSide(side) {
    const t = String(side).trim();
    if (!t) return null;
    if (/\b(hcf|gcd|highest common factor|greatest common divisor)\b/.test(t)) {
      const nums = t.match(/\d+(?:\.\d+)?/g);
      if (nums && nums.length >= 2) return 'gcd(' + nums[0] + ',' + nums[1] + ')';
      return 'gcd(' + CTX.second[0] + ',' + CTX.second[1] + ')';
    }
    if (/[a-z]/.test(t)) {
      const stripped = t.replace(/\b(gcd|hcf|lcm|sqrt|abs|min|max)\b/g, '');
      if (/[a-z]/.test(stripped)) return null; // non-math words → not evaluable
    }
    return t;
  }

  // ─── Claim extraction & truth-checking ───
  function extractClaims(normalized) {
    let s = ' ' + normalized + ' ';

    // word operators → symbols
    s = s.replace(/\btimes\b/g, '*')
         .replace(/\bmultiplied by\b/g, '*')
         .replace(/\bdivided by\b/g, '/')
         .replace(/\bover\b/g, '/')
         .replace(/\bplus\b/g, '+')
         .replace(/\bminus\b/g, '-');

    // gcd phrases BEFORE "and" becomes a separator
    s = preprocessGcdPhrases(s);

    // comparators
    s = s.replace(/\s*(?:≠|!=|<>)\s*/g, '≠')
         .replace(/\bis not\b/g, '≠')
         .replace(/\bdoes not equal\b/g, '≠')
         .replace(/\bisn't\b/g, '≠')
         .replace(/\bnot equal to\b/g, '≠')
         .replace(/\bare not\b/g, '≠')
         .replace(/\bis\b/g, '=')
         .replace(/\bequals\b/g, '=')
         .replace(/\bgives\b/g, '=')
         .replace(/\bmakes\b/g, '=')
         .replace(/\s*=\s*/g, '=')
         .replace(/\s*≠\s*/g, '≠');

    // "and" separates two statements (';' can't collide with gcd(a,b) commas)
    s = s.replace(/\band\b/g, ';');
    s = s.trim();

    const claims = [];

    // ratio-equality claims: a:b = c:d  (or ≠)
    const ratioEqRe = /(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)(=|≠)(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)/g;
    let m;
    let cleaned = s;
    while ((m = ratioEqRe.exec(s)) !== null) {
      const a = +m[1], b = +m[2], c = +m[4], d = +m[5];
      const equal = Math.abs(a * d - b * c) < EPS;
      claims.push({
        text: m[0], kind: 'ratio_eq', a, b, c, d, op: m[3],
        isTrue: (m[3] === '=') ? equal : !equal
      });
      cleaned = cleaned.split(m[0]).join(' ');
    }

    // arithmetic equality claims: split on = ≠ ; at top level
    const parts = cleaned.split(/(=|≠|;)/);
    let lhs = null, pendingOp = null;
    for (const part of parts) {
      const p = part.trim();
      if (p === '=' || p === '≠') { pendingOp = p; continue; }
      if (p === ';') { lhs = null; pendingOp = null; continue; }
      if (!p) continue;
      if (lhs === null) { lhs = p; continue; }
      if (pendingOp && /[a-z\d]/.test(lhs) && /\d/.test(p)) {
        const cl = canonicalizeSide(lhs);
        const cr = canonicalizeSide(p);
        const lv = (cl !== null) ? evalArithmetic(cl) : null;
        const rv = (cr !== null) ? evalArithmetic(cr) : null;
        if (lv !== null && rv !== null) {
          const equal = Math.abs(lv - rv) < EPS;
          claims.push({
            text: lhs + (pendingOp === '=' ? ' = ' : ' ≠ ') + p,
            kind: 'arith', lhs, rhs: p, lhsVal: lv, rhsVal: rv, op: pendingOp,
            isTrue: (pendingOp === '=') ? equal : !equal
          });
        }
      }
      lhs = p;
      pendingOp = null;
    }
    return claims;
  }

  // ─── Step parsing ───
  function parseStep(raw) {
    const normalized = normalizeText(raw);
    const words = normalized.split(/[^a-z]+/).filter(Boolean);
    const numbers = (normalized.match(/\d+(?:\.\d+)?/g) || []).map(Number);
    const ratios = [];
    const ratioRe = /(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)/g;
    let m;
    while ((m = ratioRe.exec(normalized)) !== null) ratios.push({ a: +m[1], b: +m[2] });
    const fractions = [];
    const fracRe = /(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/g;
    while ((m = fracRe.exec(normalized)) !== null) fractions.push({ n: +m[1], d: +m[2] });
    const claims = extractClaims(normalized);
    const intents = new Set(words.filter(w => MATH_INTENT.has(w)));
    const expressions = (claims.length === 0)
      ? (normalized.match(/[\d.]+(?:\s*[+\-*/^]\s*[\d.]+)+/g) || [])
      : [];
    return { raw, normalized, words, numbers, ratios, fractions, claims, intents, expressions };
  }

  function isBareYesNo(parsed) {
    return parsed.words.length <= 2 && /^(yes|no|yeah|yep|nope|ok|okay)\b/.test(parsed.normalized);
  }

  function isGarbage(parsed) {
    if (hasIrrelevantWords(parsed.normalized, '')) return true;
    const hasMath = parsed.numbers.length > 0 || parsed.claims.length > 0 || parsed.ratios.length > 0;
    const hasIntent = parsed.intents.size > 0;
    return !hasMath && !hasIntent;
  }

  // ─── Graph helpers ───
  function methodOf(nodeId) {
    const m = String(nodeId).match(/^(m\d+)_/);
    return m ? m[1] : null;
  }

  function successorOf(nodeId) {
    const edges = GRAPH.edges.filter(e => e.from === nodeId);
    return edges.length > 0 ? edges[0].to : CONCLUSION_ID;
  }

  function firstStepOf(methodId) {
    // Accepts a prefix ("m2") or a full method node id ("m2_cross_multiply")
    let src = null;
    const direct = NODE_MAP.get(methodId);
    if (direct && direct.type === 'method') {
      src = methodId;
    } else {
      const mn = GRAPH.nodes.find(n => n.type === 'method' && methodOf(n.id) === methodId);
      if (mn) src = mn.id;
    }
    if (!src) return CONCLUSION_ID;
    const edges = GRAPH.edges.filter(e => e.from === src);
    return edges.length > 0 ? edges[0].to : CONCLUSION_ID;
  }

  function methodChain(methodId) {
    const chain = [];
    let cur = methodId;
    const seen = new Set();
    while (cur && !seen.has(cur)) {
      seen.add(cur);
      chain.push(cur);
      cur = successorOf(cur);
      if (cur === CONCLUSION_ID) break;
    }
    return chain;
  }

  // ─── Expected values per step node (derived from its accept list) ───
  function collectNumbers(accepts) {
    const out = [];
    for (const a of accepts || []) {
      const m = normalizeText(a).match(/\d+(?:\.\d+)?/g) || [];
      for (const x of m) out.push(parseFloat(x));
    }
    return out;
  }

  function expectedFor(node) {
    for (const a of node.accept || []) {
      const n = normalizeText(a);
      const m = n.match(/^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$/);
      if (m) return { kind: 'ratio', a: +m[1], b: +m[2] };
    }
    const nums = [];
    for (const x of collectNumbers(node.accept)) {
      if (!nums.some(v => Math.abs(v - x) < EPS)) nums.push(x);
    }
    if (nums.length === 1) return { kind: 'number', value: nums[0] };
    if (nums.length > 1) return { kind: 'values', values: nums };
    return null;
  }

  function verifyAgainstExpected(parsed, exp) {
    // claims first — a false claim is always a wrong claim
    for (const c of parsed.claims) {
      if (!c.isTrue) return { accepted: false, wrongClaim: true, claim: c };
      const vals = [];
      if (c.kind === 'arith') vals.push(c.lhsVal, c.rhsVal);
      if (c.kind === 'ratio_eq') vals.push(c.a / c.b, c.c / c.d);
      if (exp.kind === 'number' && vals.some(v => Math.abs(v - exp.value) < EPS)) return { accepted: true };
      if (exp.kind === 'values' && vals.some(v => exp.values.some(x => Math.abs(v - x) < EPS))) return { accepted: true };
      if (exp.kind === 'ratio' && vals.some(v => Math.abs(v - exp.a / exp.b) < EPS)) return { accepted: true };
    }
    if (exp.kind === 'ratio') {
      for (const r of parsed.ratios) {
        if (Math.abs(r.a - exp.a) < EPS && Math.abs(r.b - exp.b) < EPS) return { accepted: true };
        if (Math.abs(r.a / r.b - exp.a / exp.b) < EPS) return { accepted: true };
      }
      for (const f of parsed.fractions) {
        if (Math.abs(f.n / f.d - exp.a / exp.b) < EPS) return { accepted: true };
      }
      if (parsed.numbers.length === 1 && parsed.claims.length === 0) {
        if (Math.abs(parsed.numbers[0] - exp.a / exp.b) < EPS) return { accepted: true };
      }
    }
    if (exp.kind === 'number') {
      if (parsed.numbers.length === 1 && parsed.claims.length === 0) {
        if (Math.abs(parsed.numbers[0] - exp.value) < EPS) return { accepted: true };
        return {
          accepted: false, wrongClaim: true,
          claim: { kind: 'value', isTrue: false, got: parsed.numbers[0], expected: exp.value, text: String(parsed.numbers[0]) }
        };
      }
      for (const expr of parsed.expressions) {
        const v = evalArithmetic(expr);
        if (v !== null && Math.abs(v - exp.value) < EPS) return { accepted: true };
      }
    }
    if (exp.kind === 'values') {
      if (parsed.numbers.length >= 1 && parsed.claims.length === 0) {
        // A ratio must be matched as an ordered pair, not as two unrelated values.
        if (parsed.ratios.length > 0) return { accepted: false };
        const allIn = parsed.numbers.every(n => exp.values.some(x => Math.abs(n - x) < EPS));
        if (allIn) return { accepted: true };
        const anyIn = parsed.numbers.some(n => exp.values.some(x => Math.abs(n - x) < EPS));
        if (!anyIn) {
          return {
            accepted: false, wrongClaim: true,
            claim: { kind: 'value', isTrue: false, got: parsed.numbers.join(', '), expected: exp.values.join(' or '), text: parsed.numbers.join(', ') }
          };
        }
      }
    }
    return { accepted: false };
  }

  function matchNode(parsed, node) {
    if (matchesAcceptAny(parsed.raw, node.accept)) return { accepted: true };
    const exp = expectedFor(node);
    if (!exp) return { accepted: false };
    return verifyAgainstExpected(parsed, exp);
  }

  // ─── Method keyword detection (keyword-only, longest-keyword-wins) ───
  function detectMethodKeyword(parsed) {
    const methodNodes = GRAPH.nodes.filter(n => n.type === 'method');
    let bestMethodId = null, bestLen = 0;
    for (const method of methodNodes) {
      for (const accepted of method.accept || []) {
        const clean = accepted.trim().toLowerCase();
        if (!/^[a-z]+( [a-z]+)*$/.test(clean)) continue;
        if (matchesAccept(parsed.raw, accepted)) {
          if (clean.length > bestLen) { bestLen = clean.length; bestMethodId = method.id; }
        }
      }
    }
    return bestMethodId;
  }

  // ─── Conclusion detection (tutor decides completion on its own) ───
  function isRatioPair(a, b, pair) {
    return Math.abs(a - pair[0]) < EPS && Math.abs(b - pair[1]) < EPS;
  }

  // "3/4" or "3:4" — textual ratio/fraction form matching a problem ratio
  function sideIsRatioForm(text, pair) {
    const m = String(text).trim().match(/^(\d+(?:\.\d+)?)[/:](\d+(?:\.\d+)?)$/);
    if (!m) return false;
    return isRatioPair(+m[1], +m[2], pair);
  }

  function detectConclusion(parsed, session) {
    const concl = getNode(CONCLUSION_ID);
    if (!concl) return null;
    const norm = parsed.normalized;

    const negated = /not proportional|not equal|≠|isn't|are not|is not|doesn't hold/.test(norm);

    // bare yes/no → conclusion only at the conclusion node, or between steps
    if (isBareYesNo(parsed)) {
      const atConcl = session.currentNodeId === CONCLUSION_ID;
      const noCurrent = !session.currentNodeId;
      const hasProgress = session.trail.length > 0;
      if (atConcl || (noCurrent && hasProgress)) {
        return { detected: true, correct: !/^(no|nope)\b/.test(norm) };
      }
      return null; // mid-step yes/no → not a conclusion
    }

    // definitive: ratio-equality claim between the two problem ratios
    for (const c of parsed.claims) {
      if (c.kind === 'ratio_eq') {
        const fwd = isRatioPair(c.a, c.b, CTX.first) && isRatioPair(c.c, c.d, CTX.second);
        const rev = isRatioPair(c.a, c.b, CTX.second) && isRatioPair(c.c, c.d, CTX.first);
        if (fwd || rev) return { detected: true, correct: c.isTrue };
      }
      if (c.kind === 'arith') {
        // both sides must be textual ratio/fraction forms of the two problem
        // ratios (e.g., "3/4 = 72/96") — value equality alone is not enough,
        // otherwise "72/96 = 0.75" (a mid-method step) would end the problem.
        const fwd = sideIsRatioForm(c.lhs, CTX.first) && sideIsRatioForm(c.rhs, CTX.second);
        const rev = sideIsRatioForm(c.lhs, CTX.second) && sideIsRatioForm(c.rhs, CTX.first);
        if (fwd || rev) return { detected: true, correct: c.isTrue };
      }
    }

    // accept-list match on the conclusion node
    if (matchesAcceptAny(parsed.raw, concl.accept)) {
      return { detected: true, correct: !negated && !/^(no|nope)\b/.test(norm) };
    }

    // explicit "proportional" keyword with both problem ratios present
    if (/\bproportional\b/.test(norm)) {
      const hasFirst = parsed.ratios.some(r => isRatioPair(r.a, r.b, CTX.first));
      const hasSecond = parsed.ratios.some(r => isRatioPair(r.a, r.b, CTX.second));
      if (hasFirst && hasSecond) return { detected: true, correct: !negated };
    }
    return null;
  }

  // ─── Global step search (silent method inference / skip-ahead) ───
  function findGlobalStepMatch(parsed, session) {
    if (isBareYesNo(parsed)) return null; // bare yes/no only matches the current node
    const steps = GRAPH.nodes.filter(n => n.type === 'step');
    const scored = steps.map(n => {
      let score = 0;
      const nm = methodOf(n.id);
      if (session.methodId && nm === session.methodId) score += 2;
      if (session.methodId && nm === session.methodId && session.currentNodeId) {
        const chain = methodChain(session.methodId);
        const ci = chain.indexOf(session.currentNodeId);
        const ni = chain.indexOf(n.id);
        if (ci >= 0 && ni > ci) score += 1;
      }
      return { node: n, score };
    }).sort((a, b) => b.score - a.score);

    const ordered = scored.map(x => x.node).filter(n => n.id !== session.currentNodeId);

    // Pass 1: accept-list matches only — the most specific intent wins, so
    // "0.75" hits the decimal step (exact accept) before fuzzy-matching the
    // simplify step via 3:4 ≈ 0.75.
    for (const node of ordered) {
      if (matchesAcceptAny(parsed.raw, node.accept)) {
        return { nodeId: node.id, methodId: methodOf(node.id) };
      }
    }
    // Pass 2: semantic verification against each node's expected values
    for (const node of ordered) {
      const exp = expectedFor(node);
      if (!exp) continue;
      const m = verifyAgainstExpected(parsed, exp);
      if (m.accepted) return { nodeId: node.id, methodId: methodOf(node.id) };
      // wrongClaim from a non-current node is ignored (no context to judge)
    }
    return null;
  }

  // ─── Main classifier ───
  function processStep(rawInput, session) {
    const parsed = parseStep(rawInput);
    const result = { verdict: null, parsed, nodeId: null, methodId: null, claim: null, approachOnly: false };

    // 1. Garbage gate
    if (isGarbage(parsed)) { result.verdict = 'GARBAGE'; return result; }

    // 2. Conclusion detection (tutor decides completion on its own)
    const concl = detectConclusion(parsed, session);
    if (concl && concl.detected) {
      result.verdict = concl.correct ? 'CONCLUSION_RIGHT' : 'CONCLUSION_WRONG';
      return result;
    }

    // 3. Current-node match (context wins — includes immediate wrong-claim detection)
    if (session.currentNodeId) {
      const node = getNode(session.currentNodeId);
      if (node && node.type === 'step') {
        const m = matchNode(parsed, node);
        if (m.accepted) {
          result.verdict = 'ACCEPT';
          result.nodeId = node.id;
          result.methodId = methodOf(node.id);
          return result;
        }
        if (m.wrongClaim) {
          result.verdict = 'WRONG_CLAIM';
          result.claim = m.claim;
          result.nodeId = node.id;
          result.methodId = methodOf(node.id);
          return result;
        }
      }
    }

    // Reject reversed versions of the problem ratios instead of treating their
    // numbers as an unordered match for another graph step.
    const reversedRatio = parsed.ratios.find(r =>
      (isRatioPair(r.a, r.b, [CTX.first[1], CTX.first[0]]) ||
       isRatioPair(r.a, r.b, [CTX.second[1], CTX.second[0]]))
    );
    if (reversedRatio) {
      result.verdict = 'WRONG_CLAIM';
      result.claim = {
        kind: 'value',
        got: `${reversedRatio.a}:${reversedRatio.b}`,
        expected: `${CTX.first[0]}:${CTX.first[1]}`,
        text: `${reversedRatio.a}:${reversedRatio.b}`
      };
      result.nodeId = session.currentNodeId;
      result.methodId = session.methodId;
      return result;
    }

    // 4. Any explicit false claim anywhere → immediate correction
    const falseClaim = parsed.claims.find(c => !c.isTrue);
    if (falseClaim) {
      result.verdict = 'WRONG_CLAIM';
      result.claim = falseClaim;
      result.nodeId = session.currentNodeId;
      result.methodId = session.methodId;
      return result;
    }

    // 5. Method keyword fast path (only before any method is locked in)
    if (!session.methodId) {
      const mk = detectMethodKeyword(parsed);
      if (mk) {
        result.verdict = 'ACCEPT';
        result.methodId = mk;
        result.approachOnly = true;
        return result;
      }
    }

    // 6. Global step search — silent method inference / skip-ahead
    const g = findGlobalStepMatch(parsed, session);
    if (g) {
      result.verdict = 'ACCEPT';
      result.nodeId = g.nodeId;
      result.methodId = g.methodId;
      return result;
    }

    // 7. True math, but irrelevant to this problem
    if (parsed.claims.some(c => c.isTrue)) {
      result.verdict = 'IRRELEVANT_TRUE';
      return result;
    }

    // 8. Relevant words but nothing checkable
    result.verdict = 'UNPARSED';
    return result;
  }

  // ─── Session state transition (single source of truth) ───
  function applyResult(session, result) {
    switch (result.verdict) {
      case 'ACCEPT':
        session.failStreak = 0;
        if (result.approachOnly) {
          session.methodId = methodOf(result.methodId) || result.methodId;
          session.currentNodeId = firstStepOf(session.methodId);
        } else {
          session.trail.push({ input: result.parsed.raw, nodeId: result.nodeId, methodId: result.methodId });
          if (result.methodId) session.methodId = result.methodId;
          session.currentNodeId = successorOf(result.nodeId);
        }
        break;
      case 'WRONG_CLAIM':
        session.failStreak++;
        break;
      case 'CONCLUSION_RIGHT':
        session.completed = true;
        break;
      // IRRELEVANT_TRUE / GARBAGE / UNPARSED / CONCLUSION_WRONG → no state change
    }
    return session;
  }

  // ─── Human-readable explanations ───
  function fmt(v) {
    if (v === null || v === undefined || isNaN(v)) return '?';
    const r = Math.round(v * 1e6) / 1e6;
    return String(r);
  }

  function explainClaim(c) {
    if (!c) return '';
    if (c.kind === 'arith') {
      return c.lhs.trim() + ' is ' + fmt(c.lhsVal) + ' and ' + c.rhs.trim() + ' is ' + fmt(c.rhsVal) +
        ' — so "' + c.text + '" ' + (c.isTrue ? 'holds.' : "doesn't hold.");
    }
    if (c.kind === 'ratio_eq') {
      return 'Cross products: ' + c.a + '×' + c.d + ' = ' + fmt(c.a * c.d) + ' and ' + c.b + '×' + c.c +
        ' = ' + fmt(c.b * c.c) + ' — so "' + c.text + '" ' + (c.isTrue ? 'holds.' : "doesn't hold.");
    }
    if (c.kind === 'value') {
      return c.got + " isn't the value needed at this step.";
    }
    return "This step doesn't hold.";
  }

  function hintFor(session, nodeId) {
    const node = getNode(nodeId || (session && session.currentNodeId));
    if (node && node.hints && node.hints.length > 0) {
      const idx = session ? (session.failStreak % node.hints.length) : 0;
      return node.hints[idx];
    }
    return null;
  }

  // ─── Public API ───
  return {
    init, newSession, processStep, applyResult,
    parseStep, extractClaims, evalArithmetic,
    matchesAccept, normalizeText, getNode,
    explainClaim, hintFor, methodOf, successorOf,
    _internal: { RELEVANT_WORDS, MATH_INTENT, expectedFor, detectConclusion, detectMethodKeyword, isGarbage, isBareYesNo }
  };
});