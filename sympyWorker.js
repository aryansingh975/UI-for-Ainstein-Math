// sympyWorker.js — talks to one long-running Python SymPy process (sympy_worker.py).
//
// validateWork(studentWork, equation) -> Promise<validation result>
// - The Python process is started on first use and reused for every request.
// - If a check takes too long (e.g. a pathological expression), the process is
//   killed and restarted, and that request fails with a timeout.
// - If Python or SymPy isn't installed, requests fail cleanly; server.js then
//   returns Jev's answer without validation.

const { spawn } = require('node:child_process');
const { join } = require('node:path');
const readline = require('node:readline');

const PYTHON = process.env.PYTHON || 'python3';
const SCRIPT = join(__dirname, 'sympy_worker.py');
const TIMEOUT_MS = Number(process.env.SYMPY_TIMEOUT_MS || 5000);

let proc = null;
let ready = null;          // Promise that resolves when the worker prints {"ready": true}
let nextId = 1;
const pending = new Map(); // id -> { resolve, reject, timer }

function failAll(error) {
  for (const { reject, timer } of pending.values()) {
    clearTimeout(timer);
    reject(error);
  }
  pending.clear();
}

function start() {
  proc = spawn(PYTHON, [SCRIPT], {
    cwd: __dirname,
    stdio: ['pipe', 'pipe', 'inherit'],
    env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONDONTWRITEBYTECODE: '1' }
  });
  const thisProc = proc;

  ready = new Promise((resolveReady, rejectReady) => {
    const lines = readline.createInterface({ input: thisProc.stdout });
    lines.on('line', line => {
      let msg;
      try { msg = JSON.parse(line); } catch { return; }
      if (msg.ready) { resolveReady(); return; }
      const job = pending.get(msg.id);
      if (!job) return;
      pending.delete(msg.id);
      clearTimeout(job.timer);
      if (msg.error) job.reject(new Error(`SymPy error: ${msg.error}`));
      else job.resolve(msg.result);
    });
    thisProc.on('error', err => {          // e.g. python3 not found
      rejectReady(err);
      failAll(err);
      if (proc === thisProc) proc = null;
    });
    thisProc.on('exit', code => {
      rejectReady(new Error(`SymPy worker exited (code ${code})`));
      failAll(new Error(`SymPy worker exited (code ${code})`));
      if (proc === thisProc) proc = null;
    });
  });
  ready.catch(() => {}); // handled per request
}

function restart() {
  if (proc) proc.kill();
  proc = null;
}

async function validateWork(studentWork, equation = null) {
  if (!proc) start();
  await ready;

  const id = nextId++;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error('SymPy check timed out'));
      restart(); // the worker is stuck on this input; start fresh next time
    }, TIMEOUT_MS);
    pending.set(id, { resolve, reject, timer });
    proc.stdin.write(JSON.stringify({ id, student_work: studentWork, equation }) + '\n');
  });
}

function stopWorker() {
  restart();
}

module.exports = { validateWork, stopWorker };
