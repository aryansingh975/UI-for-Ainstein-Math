// Test the solution graph matching logic (synced with app.js)
const graph = require('./solution_graph/g08-hegp107-ex001.solution-graph.json');

// Replicate the matching functions from app.js
function normalizeText(value) {
  return String(value).toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/\s*:\s*/g, ':')
    .replace(/\s*×\s*/g, '*')
    .replace(/\s*x\s*/g, '*')
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

// ─── Input Relevance Gate (synced with app.js) ───
const RELEVANT_WORDS = new Set([
  // sentence / connective words
  'i','a','an','the','and','or','so','if','then','thus','hence','therefore',
  'is','are','am','was','were','be','been','being','do','does','did','done',
  'can','will','would','should','shall','may','might','must',
  'we','us','our','you','your','my','me','it','its','they','them','their',
  'this','that','these','those','there','here','of','to','for','with','by',
  'in','on','at','as','from','into','both','each','per',
  'get','got','have','has','had','give','gives','given','use','used','using',
  'check','see','find','found','try','tries','trying','want','wants','let',
  'lets','think','okay','ok','yes','no','not','now','first','next','last',
  'final','because','since','when','make','makes','made','means','mean',
  'know','known','suppose','supposed','maybe','please',
  // math / topic vocabulary
  'equal','equals','same','identical','match','matches','matched','matching',
  'ratio','ratios','proportional','proportion','proportions',
  'fraction','fractions','numerator','denominator','numerators','denominators',
  'hcf','gcd','highest','common','factor','factors','factorization',
  'factorise','factorize','factorised','factorized','prime','primes',
  'simplest','simple','simplify','simplified','simplifies','simplifying',
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

function hasIrrelevantWords(normalizedInput, normalizedAccepted) {
  const inputWords = normalizedInput.split(/[^a-z]+/).filter(Boolean);
  if (inputWords.length === 0) return false; // pure math — nothing to check

  const acceptedWords = normalizedAccepted.split(/[^a-z]+/).filter(Boolean);
  const acceptedIsKeyword = /^[a-z]+$/.test(normalizedAccepted) && normalizedAccepted.length >= 3;

  for (const word of inputWords) {
    if (RELEVANT_WORDS.has(word)) continue;
    if (acceptedWords.some(aw =>
      (aw.length >= 3 && word.startsWith(aw)) ||
      (word.length >= 3 && aw.startsWith(word))
    )) continue;
    if (acceptedIsKeyword && word.startsWith(normalizedAccepted)) continue;
    return true; // off-topic word (e.g., "love", "paris", "hello")
  }
  return false;
}

function matchesAccept(rawInput, acceptedAnswer) {
  const normalizedInput = normalizeText(rawInput);
  const normalizedAccepted = normalizeText(acceptedAnswer);

  // Exact match after normalization
  if (normalizedInput === normalizedAccepted) return true;

  // ─── RELEVANCE GATE ───
  if (hasIrrelevantWords(normalizedInput, normalizedAccepted)) return false;

  // Method keyword matching (for method nodes)
  if (/^[a-z]+$/.test(normalizedAccepted) && normalizedAccepted.length >= 3) {
    if (normalizedInput.includes(normalizedAccepted)) return true;
    const inputWords = normalizedInput.split(' ');
    for (const word of inputWords) {
      if (word.startsWith(normalizedAccepted)) return true;
    }
  }

  // Simple numeric accept values like "24", "288", "0.75"
  if (/^[\d.]*$/.test(normalizedAccepted) && normalizedAccepted.length > 0) {
    const inputNumbers = normalizedInput.match(/(\d+(?:\.\d+)?)/g);

    if (normalizedInput === normalizedAccepted) return true;

    if (inputNumbers && inputNumbers.length === 1 && inputNumbers[0] === normalizedAccepted) {
      const words = normalizedInput.split(' ');
      if (words.length <= 3) {
        const nonNumericWords = words.filter(w => !/^\d+(?:\.\d+)?$/.test(w));
        if (nonNumericWords.every(w => w.length <= 6)) {
          return true;
        }
      }
    }
    return false;
  }

  // Ratio accept values like "3:4", "36:48", "72:96"
  if (/^\d+:\d+$/.test(normalizedAccepted)) {
    return normalizedInput === normalizedAccepted;
  }

  // Fraction accept values like "3/4", "72/96"
  if (/^\d+\/\d+$/.test(normalizedAccepted)) {
    return normalizedInput === normalizedAccepted;
  }

  // Complex expression accept values (e.g., "72/24=3 and 96/24=4")
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

  // Last resort: strip filler words and compare (text accepts only)
  if (/[a-z]/.test(normalizedAccepted)) {
    const stripped = normalizeText(stripConnectingWords(rawInput));
    if (stripped === normalizedAccepted) return true;
  }

  return false;
}

// Get node by id
function getNode(id) {
  return graph.nodes.find(n => n.id === id) || null;
}

// ─── Method detection (synced with app.js: KEYWORD-ONLY + LONGEST-KEYWORD-WINS) ───
function getMethodNodeIdFromInput(rawInput) {
  const text = rawInput.toLowerCase();
  const methodNodes = graph.nodes.filter(n => n.type === 'method');

  // The LONGEST matching keyword is the most specific intent, so it wins:
  // "prime factorization" (13 chars) beats "factor" (6 chars);
  // "reduce step by step" (19 chars) beats "reduce" (6 chars).
  let bestMethodId = null;
  let bestKeywordLen = 0;

  for (const method of methodNodes) {
    for (const accepted of method.accept) {
      const cleanAccepted = accepted.trim().toLowerCase();
      // Only letter/keyword accepts may select a method.
      if (!/^[a-z]+( [a-z]+)*$/.test(cleanAccepted)) continue;
      if (matchesAccept(text, accepted)) {
        if (cleanAccepted.length > bestKeywordLen) {
          bestKeywordLen = cleanAccepted.length;
          bestMethodId = method.id;
        }
      }
    }
  }
  return bestMethodId;
}

// Test cases: [input, nodeId, expected, description]
const tests = [
  ["3:4", "m1_s3", true, "Simple ratio match"],
  ["3 : 4", "m1_s3", true, "Ratio with spaces"],
  ["i love paris 3:4", "m1_s3", false, "Garbage sentence with 3:4 should be REJECTED"],
  ["i love paris", "m1_s3", false, "Pure garbage"],
  ["the ratio is 3:4", "m1_s3", false, "Sentence containing ratio should be REJECTED (strict)"],
  ["24", "m1_s1", true, "Simple number match"],
  ["hcf is 24", "m1_s1", true, "Number with light context"],
  ["i love paris 24", "m1_s1", false, "Garbage sentence with number should be REJECTED"],
  ["72/96", "m5_s1", true, "Fraction match"],
  ["3/4", "m5_s2", true, "Simplified fraction"],
  ["i love 3/4", "m5_s2", false, "Garbage with fraction should be REJECTED"],
  ["288", "m2_s2", true, "Cross product result"],
  ["3*96=288", "m2_s2", true, "Expression with result"],
  ["72/24=3 and 96/24=4", "m1_s2", true, "Division expression"],
  ["i love paris 72/24=3 and 96/24=4", "m1_s2", false, "Garbage around expression should be REJECTED"],
  ["yes", "conclusion", true, "Conclusion yes"],
  ["yes they are proportional", "conclusion", true, "Conclusion full sentence"],
  ["3:4 and 72:96 are proportional", "conclusion", true, "Conclusion with ratios"],
  ["no", "conclusion", false, "Wrong conclusion"],
  ["i love paris yes", "conclusion", false, "Garbage around conclusion should be REJECTED"],
  ["hello world", "conclusion", false, "Off-topic sentence should be REJECTED"],
  ["cross multiply", "m2_cross_multiply", true, "Method detection"],
  ["simplify", "m1_simplify", true, "Method detection simplify"],
  ["i want to simplify", "m1_simplify", true, "Natural phrasing with keyword accepted"],
  ["i love paris simplify", "m1_simplify", false, "Keyword buried in garbage should be REJECTED"],
  ["scale", "m3_scale", true, "Method detection scale"],
  ["decimal", "m4_decimal", true, "Method detection decimal"],
  ["fraction", "m5_fraction", true, "Method detection fraction"],
  ["prime", "m6_prime", true, "Method detection prime"],
  ["equivalent", "m7_equivalent", true, "Method detection equivalent"],
  ["reduce step by step", "m8_reduce", true, "Method detection reduce"],
  ["reduction", "m1_simplify", true, "Method detection reduce synonym"],
  ["36:48", "m8_s1", true, "Step-by-step reduction step 1"],
  ["18:24", "m8_s2", true, "Step-by-step reduction step 2"],
  ["9:12", "m8_s3", true, "Step-by-step reduction step 3"],
  ["3:4", "m8_s4", true, "Step-by-step reduction step 4"],
  // ─── Regression tests for reported bug: garbage must never match steps ───
  ["i love paris , #:4", "m4_s1", false, "Garbage '#:4' at decimal step 1 should be REJECTED"],
  ["i love paris , #:4", "m4_s2", false, "Garbage '#:4' at decimal step 2 should be REJECTED"],
  ["i love paris , #:4", "m4_s3", false, "Garbage '#:4' at decimal step 3 should be REJECTED"],
  ["i love paris , #:4", "m1_s3", false, "Garbage '#:4' at simplify step should be REJECTED"],
];

// Method detection tests at the START node: [input, expectedMethodIdOrNull, description]
const methodTests = [
  ["simplify", "m1_simplify", "Keyword selects simplify method"],
  ["hcf", "m1_simplify", "Keyword hcf selects simplify method"],
  ["cross multiply", "m2_cross_multiply", "Keyword selects cross multiply method"],
  ["cross multiplication", "m2_cross_multiply", "Keyword selects cross multiply method"],
  ["scale", "m3_scale", "Keyword selects scale method"],
  ["decimal", "m4_decimal", "Keyword selects decimal method"],
  ["fraction", "m5_fraction", "Keyword selects fraction method"],
  ["prime factorization", "m6_prime", "Keyword selects prime method"],
  ["equivalent", "m7_equivalent", "Keyword selects equivalent method"],
  ["reduce step by step", "m8_reduce", "Keyword selects reduce method"],
  // ─── Regression tests for reported bug: math input must NOT select a method ───
  ["3:4", null, "Ratio '3:4' must NOT be misread as decimal method"],
  ["0.75", null, "Number '0.75' must NOT select a method"],
  ["36:48", null, "Ratio '36:48' must NOT select a method"],
  ["i love paris , #:4", null, "Garbage '#:4' must NOT select a method"],
  ["i love paris", null, "Pure garbage must NOT select a method"],
  ["hello world", null, "Off-topic sentence must NOT select a method"],
];

let passed = 0;
let failed = 0;

console.log("=== SOLUTION GRAPH MATCHING TESTS ===\n");
for (const [input, nodeId, expected, desc] of tests) {
  const node = getNode(nodeId);
  if (!node) {
    console.log(`❌ Node ${nodeId} not found`);
    failed++;
    continue;
  }
  const result = node.accept.some(acc => matchesAccept(input, acc));
  const status = result === expected ? "PASS" : "FAIL";
  if (result === expected) passed++; else failed++;
  console.log(`${status} | "${input}" -> ${nodeId} | expected=${expected} got=${result} | ${desc}`);
}

console.log("\n=== METHOD DETECTION TESTS (START node) ===\n");
for (const [input, expected, desc] of methodTests) {
  const result = getMethodNodeIdFromInput(input);
  const status = result === expected ? "PASS" : "FAIL";
  if (result === expected) passed++; else failed++;
  console.log(`${status} | "${input}" -> expected=${expected} got=${result} | ${desc}`);
}

console.log(`\n=== RESULTS: ${passed} passed, ${failed} failed ===`);
process.exit(failed > 0 ? 1 : 0);