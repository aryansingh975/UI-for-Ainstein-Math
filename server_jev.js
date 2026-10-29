const http = require('node:http');
const { readFile } = require('node:fs/promises');
const { readdirSync, readFileSync } = require('node:fs');
const { extname, join, relative, resolve, sep } = require('node:path');
const { validateWork, stopWorker } = require('./sympyWorker'); // NEW: SymPy

const ROOT = __dirname;
const PORT = Number(process.env.PORT || 3000);
const HOST = '127.0.0.1';
const MODEL = process.env.JEV_MODEL || 'typesafe/jev-router';
const MAX_BODY_BYTES = 16 * 1024;
const CONFIDENCE_THRESHOLD = 0.7;
// NEW: problems are loaded from solution_graph/**/graph.json (no hard-coded problem).
// A graph is used with Jev when graph_meta.use_jev is true. graph_meta.equation (SymPy syntax)
// enables equation checks; a method node's optional "jev_description" is sent to Jev instead of
// its normal description.
// NEW: files that must never be served as static content
const PRIVATE_FILES = new Set(['server.js', 'server_jev.js', 'sympyWorker.js', 'sympy_worker.py', 'sympy_validator.py', 'requirements.txt']);

function findGraphFiles(dir) {
  const found = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) found.push(...findGraphFiles(full));
    else if (entry.name === 'graph.json' || entry.name.endsWith('.solution-graph.json')) found.push(full);
  }
  return found;
}

function loadProblems() {
  const problems = {};
  for (const file of findGraphFiles(join(__dirname, 'solution_graph'))) {
    try {
      const graph = JSON.parse(readFileSync(file, 'utf8'));
      const meta = graph.graph_meta || {};
      if (!meta.problem_uuid) continue;
      const methods = {};
      for (const node of graph.nodes || []) {
        if (node.type !== 'method') continue;
        methods[node.id] = {
          nodeId: node.id,
          label: node.label || node.id,
          description: node.jev_description || `${node.label || node.id}: ${node.description || ''}`,
          equation: node.sympy_equation || null   // per-method equation when x means different things
        };
      }
      problems[meta.problem_uuid] = {
        id: meta.problem_uuid,
        text: meta.problem_text || '',
        equation: meta.equation || null,
        useJev: meta.use_jev === true,
        // false when solving for x is not the final answer (e.g. x = mother's age in one method)
        sympyCanFinish: meta.sympy_can_finish !== false,
        methods
      };
    } catch (error) {
      console.error(`Skipping ${file}: ${error.message}`);
    }
  }
  return problems;
}

const PROBLEMS = loadProblems();
console.log(`Loaded ${Object.keys(PROBLEMS).length} problems (${Object.values(PROBLEMS).filter(p => p.useJev).length} with Jev).`);

const MIME_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml'
};

function canonicalMethod(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/^(answer|method)_/, '')
    .replace(/[\s-]+/g, '_');
}

function parseModelJson(content) {
  if (typeof content !== 'string') throw new Error('Jev returned no text response.');
  const unfenced = content.replace(/^```(?:json)?\s*|\s*```$/g, '').trim();
  const start = unfenced.indexOf('{');
  const end = unfenced.lastIndexOf('}');
  if (start < 0 || end < start) throw new Error('Jev did not return a JSON response.');
  return JSON.parse(unfenced.slice(start, end + 1));
}

function interpretJevResponse(response, methods) {
  const offGraphValue = response && response.off_graph;
  const offGraph = typeof offGraphValue === 'boolean'
    ? Number(offGraphValue)
    : Number(offGraphValue && offGraphValue.noul);
  if (Number.isFinite(offGraph) && offGraph >= CONFIDENCE_THRESHOLD) {
    return { status: 'off_graph', confidence: offGraph };
  }

  const method = response && response.method;
  const choice = typeof method === 'string' ? method : method && method.type === 'choice' ? method.choice : null;
  if (!choice) return { status: 'uncertain' };

  const selected = canonicalMethod(choice);
  const methodInfo = methods[selected];
  if (!methodInfo) return { status: 'uncertain' };

  const probability = method.probabilities && Number(
    method.probabilities[choice] ?? method.probabilities[selected]
  );
  const methodConfidence = method && typeof method === 'object' ? method.confidence : undefined;
  const confidenceValue = response.confidence ?? methodConfidence ?? probability;
  const confidence = Number(confidenceValue);

  if (!Number.isFinite(confidence) || confidence < CONFIDENCE_THRESHOLD) {
    return { status: 'uncertain', confidence: Number.isFinite(confidence) ? confidence : null };
  }

  return {
    status: 'selected',
    methodKey: selected,
    methodId: methodInfo.nodeId,
    confidence
  };
}

async function readJsonBody(request) {
  const chunks = [];
  let size = 0;

  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) throw Object.assign(new Error('Request body is too large.'), { status: 413 });
    chunks.push(chunk);
  }

  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw Object.assign(new Error('Request body must be valid JSON.'), { status: 400 });
  }
}

function sendJson(response, status, body) {
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  response.end(JSON.stringify(body));
}

async function classifyMethod(problem, studentWork) {
  const METHODS = problem.methods;
  if (!process.env.OPENROUTER_API_KEY) {
    throw Object.assign(new Error('The Jev API key is not configured.'), { status: 503, code: 'not_configured' });
  }

  const task = {
    model: 'jev',
    state: { problem: problem.text, student_work: studentWork },
    questions: {
      method: {
        type: 'choice',
        question: 'Which solution method is the student using? Classify the approach only; do not judge whether the math is correct.',
        options: Object.fromEntries(Object.entries(METHODS).map(([key, method]) => [key, method.description]))
      },
      off_graph: {
        type: 'noul',
        question: 'Is the student using a solution method that is not listed in the method options?'
      }
    }
  };

  const upstream = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
      'Content-Type': 'application/json',
      'X-OpenRouter-Title': 'Ainstein Math Tutor'
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        {
          role: 'system',
          content: 'Classify which listed method the student work so far is following, without judging whether the math is correct. ' +
            'Give a probability from 0 to 1 for EVERY method option; the probabilities MUST add up to 1 (never all 0). ' +
            'Each option description lists the steps of that method. If the work so far only contains steps that several methods share ' +
            '(for example expanding brackets or simplifying), split the probability evenly between those methods; this is NOT off graph. ' +
            'Set off_graph to true only if the work clearly uses an approach that is not one of the listed methods.'
        },
        { role: 'user', content: JSON.stringify(task) }
      ],
      response_format: {
        type: 'json_schema',
        json_schema: {
          name: 'jev_method_classification',
          strict: true,
          schema: {
            type: 'object',
            properties: {
              probabilities: {
                type: 'object',
                properties: Object.fromEntries(Object.keys(METHODS).map(k => [k, { type: 'number', minimum: 0, maximum: 1 }])),
                required: Object.keys(METHODS),
                additionalProperties: false
              },
              off_graph: { type: 'boolean' }
            },
            required: ['probabilities', 'off_graph'],
            additionalProperties: false
          }
        }
      },
      // Only route to providers that honour response_format; otherwise the
      // router may pick one that ignores the schema and replies in prose.
      provider: { require_parameters: true },
      // Routed models may reason before answering, so leave room for that.
      reasoning: { effort: 'low' },
      temperature: 0,
      max_tokens: 2000
    }),
    signal: AbortSignal.timeout(20000)
  });

  if (!upstream.ok) {
    // Show OpenRouter's own reason (e.g. invalid key, no credits, model unavailable, rate limit)
    const reason = (await upstream.text().catch(() => '')).replace(/\s+/g, ' ').slice(0, 600);
    console.error(`OpenRouter Jev request failed with HTTP ${upstream.status}: ${reason}`);
    throw Object.assign(new Error(`OpenRouter HTTP ${upstream.status}: ${reason}`), { status: 502, code: 'upstream_error' });
  }

  const payload = await upstream.json();
  const content = payload.choices && payload.choices[0] && payload.choices[0].message && payload.choices[0].message.content;
  console.log('[Jev raw]', JSON.stringify(payload).slice(0, 1500));
  const finishReason = payload.choices && payload.choices[0] && payload.choices[0].finish_reason;
  if (finishReason === 'length') console.error(`Jev (${payload.model}) hit max_tokens before finishing its answer.`);
  const raw = parseModelJson(content);
  const probs = raw.probabilities || {};
  const rawTotal = Object.values(probs).reduce((a, b) => a + Number(b || 0), 0);
  if (rawTotal <= 0 && !raw.off_graph) return { status: 'uncertain', confidence: null, probabilities: probs };
  const total = rawTotal || 1;
  const normalised = Object.fromEntries(Object.entries(probs).map(([k, v]) => [k, Number(v || 0) / total]));
  const [choice, confidence] = Object.entries(normalised).sort((a, b) => b[1] - a[1])[0] || [null, 0];
  console.log('[Jev]', JSON.stringify(studentWork), '→', normalised);
  const result = interpretJevResponse({ off_graph: raw.off_graph, method: { type: 'choice', choice, probabilities: normalised, confidence } }, METHODS);
  return { ...result, probabilities: normalised };
}

// ---------------------------------------------------------------------------
// NEW: Jev (which method) + SymPy (is the maths correct), run in parallel
// ---------------------------------------------------------------------------
function methodLabel(problem, methodKey) {
  const m = problem.methods[methodKey];
  return m ? m.label.replace(/^Method \d+:\s*/, '') : String(methodKey || '').replace(/_/g, ' ');
}

// Jev result + SymPy result -> one answer for the UI.
// SymPy's verdict on correctness comes first; Jev's method guides the rest.
function combineResults(problem, method, validation) {
  const sympyOk = validation && validation.status !== 'unavailable';
  const jevOk = method && method.status !== 'unavailable';
  const checkedLines = sympyOk ? validation.lines.filter(l => l.status === 'valid').length : 0;

  // 1. A maths mistake always wins.
  if (sympyOk && validation.errors.length) {
    const e = validation.errors[0];
    return {
      status: 'fix_mistake',
      feedback: `There is a mistake in "${e.statement}". ${e.message || ''}`.trim(),
      method,
      validation
    };
  }

  // 2. Every root found and every line correct.
  if (sympyOk && validation.solved && problem.sympyCanFinish) {
    return {
      status: 'solved',
      feedback: `Correct! x = ${validation.roots_claimed.join(' or x = ')}.`,
      method,
      validation
    };
  }

  const missingRoot = sympyOk && problem.sympyCanFinish && validation.missing_roots.length
    ? ` You found x = ${validation.roots_claimed.join(', ')}. There is one more root to find.`
    : '';

  // 3. No mistakes — now use Jev's classification.
  if (jevOk && method.status === 'selected') {
    const prefix = checkedLines ? 'Correct so far.' : 'Looks good.';
    return {
      status: 'on_track',
      feedback: `${prefix} You are using ${methodLabel(problem, method.methodKey)}.${missingRoot}`,
      method,
      validation
    };
  }
  if (jevOk && method.status === 'off_graph') {
    return {
      status: 'off_graph',
      feedback: `${checkedLines ? 'Your working is correct, but I' : 'I'} don't recognise this method. Which method are you using?${missingRoot}`,
      options: Object.keys(problem.methods),
      method,
      validation
    };
  }
  if (jevOk && method.status === 'uncertain') {
    return {
      status: 'uncertain',
      feedback: `${checkedLines ? 'Correct so far. ' : ''}Which method are you using?${missingRoot}`,
      options: Object.keys(problem.methods),
      method,
      validation
    };
  }

  // 4. Jev unavailable — SymPy-only feedback.
  if (sympyOk) {
    return {
      status: checkedLines ? 'on_track' : 'unchecked',
      feedback: checkedLines ? `Correct so far.${missingRoot}` : 'I could not check this step. Try writing it as an equation.',
      method,
      validation
    };
  }

  return { status: 'unavailable', feedback: 'Checking is unavailable right now. Please try again.', method, validation };
}

// The SymPy equations to try for a problem: one per method when methods use x differently,
// otherwise the problem's single equation (or null = arithmetic checks only).
function candidateEquations(problem) {
  const perMethod = Object.values(problem.methods).map(m => m.equation).filter(Boolean);
  const all = [...new Set([...perMethod, problem.equation].filter(Boolean))];
  return all.length ? all : [null];
}

// Pick the SymPy result to report: the selected method's equation if Jev is sure,
// otherwise the reading that finds the work correct (and checks the most lines).
function pickValidation(problem, method, results) {
  const ok = results.filter(r => r.status === 'fulfilled').map(r => r.value);
  if (!ok.length) return { status: 'unavailable' };
  if (method && method.status === 'selected') {
    const eq = problem.methods[method.methodId] && problem.methods[method.methodId].equation;
    const match = eq && ok.find(v => v.equation === eq);
    if (match) return match;
  }
  const score = v => (v.errors.length ? -1000 * v.errors.length : 0) + v.lines.filter(l => l.status === 'valid').length;
  return ok.slice().sort((a, b) => score(b) - score(a))[0];
}

async function checkStudentWork(problem, studentWork) {
  const equations = candidateEquations(problem);
  const [jevResult, ...sympyResults] = await Promise.allSettled([
    classifyMethod(problem, studentWork),
    ...equations.map(eq => validateWork(studentWork, eq).then(v => ({ ...v, equation: eq })))
  ]);

  const method = jevResult.status === 'fulfilled'
    ? jevResult.value
    : { status: 'unavailable', reason: jevResult.reason && jevResult.reason.code || 'classification_error' };
  if (jevResult.status === 'rejected') console.error('Jev:', jevResult.reason && jevResult.reason.message);

  for (const r of sympyResults) if (r.status === 'rejected') console.error('SymPy:', r.reason && r.reason.message);
  const validation = pickValidation(problem, method, sympyResults);

  return combineResults(problem, method, validation);
}

async function serveStatic(request, response, pathname) {
  let decodedPath;
  try {
    decodedPath = decodeURIComponent(pathname);
  } catch {
    sendJson(response, 400, { error: 'Invalid path.' });
    return;
  }

  const requestedPath = decodedPath === '/' ? '/index.html' : decodedPath;
  const filePath = resolve(ROOT, `.${requestedPath}`);
  const relativePath = relative(ROOT, filePath);
  const segments = relativePath.split(sep);

  if (relativePath.startsWith('..') || segments.some(segment => segment.startsWith('.') || segment === '__pycache__') ||
      segments.some(segment => PRIVATE_FILES.has(segment)) || extname(filePath) === '.py') {
    sendJson(response, 404, { error: 'Not found.' });
    return;
  }

  try {
    const content = await readFile(filePath);
    response.writeHead(200, {
      'Content-Type': MIME_TYPES[extname(filePath)] || 'application/octet-stream',
      'X-Content-Type-Options': 'nosniff'
    });
    response.end(content);
  } catch {
    sendJson(response, 404, { error: 'Not found.' });
  }
}

// NEW: shared request validation for both API routes
async function readStudentWork(request, response) {
  const body = await readJsonBody(request);
  const problem = PROBLEMS[body.problemId];
  if (!problem || typeof body.studentWork !== 'string' || !body.studentWork.trim()) {
    sendJson(response, 400, { status: 'invalid_request', message: 'A supported problem and student response are required.' });
    return null;
  }
  if (body.studentWork.length > 2000) {
    sendJson(response, 413, { status: 'invalid_request', message: 'The response is too long.' });
    return null;
  }
  const methodId = typeof body.methodId === 'string' && problem.methods[body.methodId] ? body.methodId : null;
  return { problem, studentWork: body.studentWork.trim(), methodId };
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, `http://${HOST}`);

  // Unchanged: Jev method classification only
  if (request.method === 'POST' && url.pathname === '/api/jev/method') {
    try {
      const input = await readStudentWork(request, response);
      if (input === null) return;

      const result = await classifyMethod(input.problem, input.studentWork);
      sendJson(response, 200, result);
    } catch (error) {
      console.error('[Jev error]', error);
      const status = error.status || 502;
      const code = error.code || 'classification_error';
      const message = status === 503
        ? 'Jev is not configured. Set OPENROUTER_API_KEY in .env and restart the server.'
        : status === 400 || status === 413
          ? error.message
          : 'Jev could not classify this response. Please try again.';
      // DEBUG: include the real reason so it shows in the curl reply
      const detail = [error && error.name, error && error.message, error && error.cause && error.cause.message]
        .filter(Boolean).join(' | ');
      sendJson(response, status, { status: code, message, detail });
    }
    return;
  }

  // NEW: Jev method + SymPy correctness in one call
  if (request.method === 'POST' && url.pathname === '/api/check') {
    try {
      const input = await readStudentWork(request, response);
      if (input === null) return;

      const result = await checkStudentWork(input.problem, input.studentWork);
      sendJson(response, result.status === 'unavailable' ? 503 : 200, result);
    } catch (error) {
      const status = error.status === 400 || error.status === 413 ? error.status : 500;
      sendJson(response, status, {
        status: 'invalid_request',
        message: status === 500 ? 'Could not check this response. Please try again.' : error.message
      });
    }
    return;
  }

  // NEW: SymPy only (handy for testing without spending Jev calls)
  if (request.method === 'POST' && url.pathname === '/api/sympy/validate') {
    try {
      const input = await readStudentWork(request, response);
      if (input === null) return;

      const methodEq = input.methodId && input.problem.methods[input.methodId].equation;
      const equation = methodEq || input.problem.equation;
      sendJson(response, 200, { ...(await validateWork(input.studentWork, equation)), equation });
    } catch (error) {
      const status = error.status === 400 || error.status === 413 ? error.status : 503;
      sendJson(response, status, {
        status: status === 503 ? 'sympy_unavailable' : 'invalid_request',
        message: status === 503 ? 'SymPy is not available. Is Python with sympy installed?' : error.message
      });
    }
    return;
  }

  // NEW: which problems the server knows (and which use Jev)
  if (request.method === 'GET' && url.pathname === '/api/problems') {
    sendJson(response, 200, Object.values(PROBLEMS).map(p => ({
      id: p.id, text: p.text, useJev: p.useJev, hasEquation: Boolean(p.equation), methods: Object.keys(p.methods)
    })));
    return;
  }

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    sendJson(response, 405, { error: 'Method not allowed.' });
    return;
  }

  await serveStatic(request, response, url.pathname);
});

if (require.main === module) {
  server.listen(PORT, HOST, () => {
    console.log(`Ainstein is running at http://${HOST}:${PORT}`);
  });
  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => { stopWorker(); server.close(() => process.exit(0)); });
  }
}

module.exports = {
  PROBLEMS, canonicalMethod, interpretJevResponse, parseModelJson, classifyMethod, server,
  checkStudentWork, combineResults // NEW
};
