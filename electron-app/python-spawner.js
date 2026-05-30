// python-spawner.js — gerencia o subprocess do gisele-python-helper.
//
// Estrategia:
//   - Em dev: roda `python python-helper/server.py --port N` (precisa Python instalado).
//   - Em build empacotado: roda `gisele-python-helper.exe --port N` do extraResources.
//   - Probe /health com retry para confirmar que subiu.
//   - Kill no quit do app.
//
// O helper roda em loopback (127.0.0.1) para que so o Electron acesse.
// Porta default 8765; cai para a proxima livre se ocupada.

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

const DEFAULT_PORT = 8765;
const PROBE_INTERVAL_MS = 250;
const PROBE_MAX_ATTEMPTS = 60; // 15s

let childProc = null;
let helperPort = null;
let helperUrl = null;

function log(msg) {
  console.log('[python-helper] ' + msg);
}

// ─── Resolve o caminho do executavel/script ────────────────────────────
//
// Em dev (app rodando do source): usar `python` do PATH + server.py do source.
// Em build: o PyInstaller .exe vai em resources/python-helper/.
function resolveHelperCommand(electronApp) {
  const isPackaged = !!(electronApp && electronApp.isPackaged);

  if (isPackaged) {
    // app.getAppPath() -> resources/app/, queremos resources/
    const resourcesDir = path.dirname(electronApp.getAppPath());
    const exeName = process.platform === 'win32'
      ? 'gisele-python-helper.exe'
      : 'gisele-python-helper';
    const exePath = path.join(resourcesDir, 'python-helper', exeName);
    if (fs.existsSync(exePath)) {
      return { cmd: exePath, args: [], cwd: path.dirname(exePath) };
    }
    log('AVISO: gisele-python-helper.exe nao encontrado em ' + exePath);
    return null;
  }

  // Dev: roda do source
  const serverPy = path.join(__dirname, 'python-helper', 'server.py');
  if (!fs.existsSync(serverPy)) {
    log('AVISO: python-helper/server.py nao encontrado em ' + serverPy);
    return null;
  }
  // Tenta python3 antes (Linux/Mac); cai para python no Windows
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  return { cmd: pythonCmd, args: [serverPy], cwd: path.dirname(serverPy) };
}

// ─── Probe /health ─────────────────────────────────────────────────────
function probeHealth(port) {
  return new Promise((resolve) => {
    const req = http.get({ host: '127.0.0.1', port, path: '/health', timeout: 1000 }, (res) => {
      if (res.statusCode === 200) {
        let body = '';
        res.on('data', (c) => body += c);
        res.on('end', () => {
          try { resolve(JSON.parse(body)); }
          catch (_) { resolve(null); }
        });
      } else {
        resolve(null);
      }
    });
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
  });
}

async function waitForHealth(port) {
  for (let i = 0; i < PROBE_MAX_ATTEMPTS; i++) {
    const h = await probeHealth(port);
    if (h && h.ready) {
      log('helper UP em :' + port + ' (versao ' + (h.version || '?') + ')');
      return h;
    }
    await new Promise(r => setTimeout(r, PROBE_INTERVAL_MS));
  }
  log('TIMEOUT esperando /health em :' + port);
  return null;
}

// ─── Start ─────────────────────────────────────────────────────────────
async function start(electronApp, opts = {}) {
  const port = opts.port || DEFAULT_PORT;
  const cmd = resolveHelperCommand(electronApp);

  if (!cmd) {
    log('helper indisponivel — frontend usara fallback JS.');
    return null;
  }

  log('iniciando ' + cmd.cmd + ' ' + (cmd.args || []).join(' ') + ' --port ' + port);

  try {
    childProc = spawn(cmd.cmd, [...cmd.args, '--port', String(port), '--host', '127.0.0.1'], {
      cwd: cmd.cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
  } catch (e) {
    log('falha ao spawnar: ' + e.message);
    return null;
  }

  childProc.stdout.on('data', (data) => {
    const txt = data.toString().trim();
    if (txt) log('stdout: ' + txt);
  });
  childProc.stderr.on('data', (data) => {
    const txt = data.toString().trim();
    if (txt) log('stderr: ' + txt);
  });
  childProc.on('exit', (code, signal) => {
    log('helper EXIT code=' + code + ' signal=' + signal);
    childProc = null;
    helperUrl = null;
  });
  childProc.on('error', (err) => {
    log('helper ERROR: ' + err.message);
    childProc = null;
  });

  const health = await waitForHealth(port);
  if (!health) {
    log('helper nao ficou pronto — desligando subprocess');
    stop();
    return null;
  }

  helperPort = port;
  helperUrl = 'http://127.0.0.1:' + port;
  return { url: helperUrl, version: health.version };
}

// ─── Stop ──────────────────────────────────────────────────────────────
function stop() {
  if (childProc && !childProc.killed) {
    try {
      log('encerrando helper...');
      if (process.platform === 'win32') {
        // No Windows, child.kill() so trata SIGTERM (que python uvicorn nao captura);
        // taskkill mata a arvore de processos.
        const { exec } = require('child_process');
        exec('taskkill /F /T /PID ' + childProc.pid, () => {});
      } else {
        childProc.kill('SIGTERM');
        setTimeout(() => {
          if (childProc && !childProc.killed) childProc.kill('SIGKILL');
        }, 2000);
      }
    } catch (e) {
      log('erro ao matar helper: ' + e.message);
    }
  }
  childProc = null;
  helperUrl = null;
}

function getUrl() { return helperUrl; }
function getPort() { return helperPort; }
function isRunning() { return !!helperUrl; }

module.exports = { start, stop, getUrl, getPort, isRunning };
