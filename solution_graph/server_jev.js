const http = require('node:http');
const { readFile } = require('node:fs/promises');
const { extname, relative, resolve, sep } = require('node:path');
const { validateWork, stopWorker } = require('./sympyWorker'); // NEW: SymPy

const ROOT = __dirname;
const PORT = Number(process.env.PORT || 3000);
const HOST = '127.0.0.1';
const MODEL = process.env.JEV_MODEL || 'typesafe/jev-router';
const MAX_BODY_BYTES = 16 * 1024;
const CONFIDENCE_THRESHOLD = 0.7;
const PROBLEM_ID = 'g10-quad-ex001';
const PROBLEM_TEXT = 'Solve the quadratic equation x^2 - 5x + 6 = 0.';
const PROBLEM_EQUATION = 'x**2 - 5*x + 6 = 0'; // NEW: SymPy syntax, used to check the student's maths

// NEW: files that must never be served as static content
const PRIVATE_FILES = new Set(['server.js', 'sympyWorker.js', 'sympy_worker.py', 'sympy_validator.py', 'requirements.txt']);

const METHODS = {
  factoring: {
    nodeId: 'm1_factor',
    description: 'Factor the quadratic, then set each factor equal to zero.'
  },
  quadratic_formula: {
    nodeId: 'm2_formula',
    description: 'Use the quadratic formula.'
  },
  completing_the_square: {
    nodeId: 'm3_square',
    description: 'Complete the square.'
  },
  graphical: {
    nodeId: 'm4_graph',
    description: 'Graph the quadratic and read its x-intercepts.'
  },
  sum_and_product_of_roots: {
    nodeId: 'm5_vieta',
    description: 'Use the sum and product of the roots.'
  },
  trial_and_factor_theorem: {
    nodeId: 'm6_trial',
    description: 'Test possible roots and use the factor theorem.'
  }
};

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

function interpretJevResponse(response) {
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
  const methodInfo = METHODS[selected];
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

async function classifyMethod(studentWork) {
  if (!process.env.OPENROUTER_API_KEY) {
    throw Object.assign(new Error('The Jev API key is not configured.'), { status: 503, code: 'not_configured' });
  }

  const task = {
    model: 'jev',
    state: { problem: PROBLEM_TEXT, student_work: studentWork },
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
          content: 'Classify the method shown by the student work, without judging whether the math is correct. Return the exact method option key, a confidence number from 0 to 1, and whether the method is off graph. Set off_graph to true only when none of the listed methods applies.'
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
              method: { type: 'string', enum: Object.keys(METHODS) },
              confidence: { type: 'number', minimum: 0, maximum: 1 },
              off_graph: { type: 'boolean' }
            },
            required: ['method', 'confidence', 'off_graph'],
            additionalProperties: false
          }
        }
      },
      temperature: 0,
      max_tokens: 220
    }),
    signal: AbortSignal.timeout(20000)
  });

  if (!upstream.ok) {
    console.error(`OpenRouter Jev request failed with HTTP ${upstream.status}.`);
    throw Object.assign(new Error('Jev could not classify this response. Please try again.'), { status: 502, code: 'upstream_error' });
  }

  const payload = await upstream.json();
  const content = payload.choices && payload.choices[0] && payload.choices[0].message && payload.choices[0].message.content;
  return interpretJevResponse(parseModelJson(content));
}

// ---------------------------------------------------------------------------
// NEW: Jev (which method) + SymPy (is the maths correct), run in parallel
// ---------------------------------------------------------------------------
function methodLabel(methodKey) {
  return String(methodKey || '').replace(/_/g, ' ');
}

// Jev result + SymPy result -> one answer for the UI.
// SymPy's verdict on correctness comes first; Jev's method guides the rest.
function combineResults(method, validation) {
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
  if (sympyOk && validation.solved) {
    return {
      status: 'solved',
      feedback: `Correct! x = ${validation.roots_claimed.join(' or x = ')}.`,
      method,
      validation
    };
  }

  const missingRoot = sympyOk && validation.missing_roots.length
    ? ` You found x = ${validation.roots_claimed.join(', ')}. There is one more root to find.`
    : '';

  // 3. No mistakes — now use Jev's classification.
  if (jevOk && method.status === 'selected') {
    const prefix = checkedLines ? 'Correct so far.' : 'Looks good.';
    return {
      status: 'on_track',
      feedback: `${prefix} You are using ${methodLabel(method.methodKey)}.${missingRoot}`,
      method,
      validation
    };
  }
  if (jevOk && method.status === 'off_graph') {
    return {
      status: 'off_graph',
      feedback: `${checkedLines ? 'Your working is correct, but I' : 'I'} don't recognise this method. Which method are you using?${missingRoot}`,
      options: Object.keys(METHODS),
      method,
      validation
    };
  }
  if (jevOk && method.status === 'uncertain') {
    return {
      status: 'uncertain',
      feedback: `${checkedLines ? 'Correct so far. ' : ''}Which method are you using?${missingRoot}`,
      options: Object.keys(METHODS),
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

async function checkStudentWork(studentWork) {
  const [jevResult, sympyResult] = await Promise.allSettled([
    classifyMethod(studentWork),
    validateWork(studentWork, PROBLEM_EQUATION)
  ]);

  const method = jevResult.status === 'fulfilled'
    ? jevResult.value
    : { status: 'unavailable', reason: jevResult.reason && jevResult.reason.code || 'classification_error' };
  if (jevResult.status === 'rejected') console.error('Jev:', jevResult.reason && jevResult.reason.message);

  const validation = sympyResult.status === 'fulfilled'
    ? sympyResult.value
    : { status: 'unavailable' };
  if (sympyResult.status === 'rejected') console.error('SymPy:', sympyResult.reason && sympyResult.reason.message);

  return combineResults(method, validation);
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
  if (body.problemId !== PROBLEM_ID || typeof body.studentWork !== 'string' || !body.studentWork.trim()) {
    sendJson(response, 400, { status: 'invalid_request', message: 'A supported problem and student response are required.' });
    return null;
  }
  if (body.studentWork.length > 2000) {
    sendJson(response, 413, { status: 'invalid_request', message: 'The response is too long.' });
    return null;
  }
  return body.studentWork.trim();
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, `http://${HOST}`);

  // Unchanged: Jev method classification only
  if (request.method === 'POST' && url.pathname === '/api/jev/method') {
    try {
      const studentWork = await readStudentWork(request, response);
      if (studentWork === null) return;

      const result = await classifyMethod(studentWork);
      sendJson(response, 200, result);
    } catch (error) {
      const status = error.status || 502;
      const code = error.code || 'classification_error';
      const message = status === 503
        ? 'Jev is not configured. Set OPENROUTER_API_KEY in .env and restart the server.'
        : status === 400 || status === 413
          ? error.message
          : 'Jev could not classify this response. Please try again.';
      sendJson(response, status, { status: code, message });
    }
    return;
  }

  // NEW: Jev method + SymPy correctness in one call
  if (request.method === 'POST' && url.pathname === '/api/check') {
    try {
      const studentWork = await readStudentWork(request, response);
      if (studentWork === null) return;

      const result = await checkStudentWork(studentWork);
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
      const studentWork = await readStudentWork(request, response);
      if (studentWork === null) return;

      sendJson(response, 200, await validateWork(studentWork, PROBLEM_EQUATION));
    } catch (error) {
      const status = error.status === 400 || error.status === 413 ? error.status : 503;
      sendJson(response, status, {
        status: status === 503 ? 'sympy_unavailable' : 'invalid_request',
        message: status === 503 ? 'SymPy is not available. Is Python with sympy installed?' : error.message
      });
    }
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
  METHODS, canonicalMethod, interpretJevResponse, parseModelJson, classifyMethod, server,
  checkStudentWork, combineResults // NEW
};
