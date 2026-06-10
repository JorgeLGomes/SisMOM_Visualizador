const { app, BrowserWindow, Menu, shell, screen, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const pythonSpawner = require('./python-spawner');

// ─── Logging para diagnóstico ────────────────────────────────────────
// Escreve em %APPDATA%/GISELE/launch.log para facilitar suporte
function debugLog(msg) {
  try {
    const dir = path.join(app.getPath('userData'));
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(path.join(dir, 'launch.log'),
      new Date().toISOString() + '  ' + msg + '\n');
  } catch (_) {}
  console.log('[GISELE]', msg);
}

// ─── Multi-monitor: combina retângulos dos displays pedidos ─────────
// Os displays são ordenados pela posição física (top→bottom, left→right),
// que tipicamente coincide com a numeração do Windows em "Configurações > Tela".
function getCombinedBounds(displayIndices) {
  const all = [...screen.getAllDisplays()].sort((a, b) => {
    if (Math.abs(a.bounds.y - b.bounds.y) > 100) return a.bounds.y - b.bounds.y;
    return a.bounds.x - b.bounds.x;
  });

  debugLog('Detectei ' + all.length + ' display(s):');
  all.forEach((d, i) => {
    debugLog('  Display ' + (i + 1) + ': x=' + d.bounds.x + ' y=' + d.bounds.y +
      ' w=' + d.bounds.width + ' h=' + d.bounds.height +
      (d.internal ? ' [internal]' : '') + (d.id === screen.getPrimaryDisplay().id ? ' [primary]' : ''));
  });

  let xMin = Infinity, yMin = Infinity, xMax = -Infinity, yMax = -Infinity;
  let count = 0;
  for (const i of displayIndices) {
    const d = all[i - 1];
    if (!d) { debugLog('AVISO: display #' + i + ' não existe'); continue; }
    xMin = Math.min(xMin, d.bounds.x);
    yMin = Math.min(yMin, d.bounds.y);
    xMax = Math.max(xMax, d.bounds.x + d.bounds.width);
    yMax = Math.max(yMax, d.bounds.y + d.bounds.height);
    count++;
  }
  if (count === 0) { debugLog('Nenhum display válido em --displays'); return null; }
  const b = { x: xMin, y: yMin, width: xMax - xMin, height: yMax - yMin };
  debugLog('Bounds combinados: ' + JSON.stringify(b));
  return b;
}

// ─── Parse CLI args ─────────────────────────────────────────────────
function parseDisplaysArg() {
  const argv = process.argv;
  debugLog('process.argv = ' + JSON.stringify(argv));
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--displays=')) {
      return a.split('=')[1].split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
    }
    if (a === '--displays' && argv[i + 1]) {
      return argv[i + 1].split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
    }
  }
  return null;
}

function hasFlag(flag) { return process.argv.indexOf(flag) >= 0; }

// ─── Política de segurança (CORS) ─────────────────────────────────────
function corsStrict() { return hasFlag('--strict-cors'); }

// ─── Python helper (aceleracao opcional) ────────────────────────────
// Por padrao GISELE tenta subir um servidor Python local em 127.0.0.1:8765
// que acelera operacoes pesadas (extracao temporal, calculadora temporal,
// perfil, export GeoJSON de serie temporal). Se nao subir, frontend cai
// transparente no fallback JS. Use --no-python-helper para desabilitar.
function pythonHelperDisabled() { return hasFlag('--no-python-helper'); }

// IPC: renderer pergunta a URL atual do helper
ipcMain.handle('gisele-python:get-url', () => pythonSpawner.getUrl());
ipcMain.handle('gisele-python:is-available', () => pythonSpawner.isRunning());

// IPC: diálogo nativo "escolher pasta" (ferramenta de download de dados).
// Retorna o caminho escolhido ou null se o usuário cancelar.
ipcMain.handle('gisele-fs:choose-dir', async (e, opts) => {
  try {
    const win = BrowserWindow.fromWebContents(e.sender);
    const r = await dialog.showOpenDialog(win, {
      title: (opts && opts.title) || 'Escolher pasta para salvar os dados',
      defaultPath: (opts && opts.defaultPath) || app.getPath('downloads'),
      properties: ['openDirectory', 'createDirectory'],
      buttonLabel: 'Usar esta pasta',
    });
    if (r.canceled || !r.filePaths || !r.filePaths.length) return null;
    return r.filePaths[0];
  } catch (err) { debugLog('choose-dir err: ' + (err && err.message)); return null; }
});
// IPC: abre uma pasta no gerenciador de arquivos do SO
ipcMain.handle('gisele-fs:open-dir', (_e, p) => {
  try { if (p) { shell.openPath(String(p)); return true; } } catch (_) {}
  return false;
});

// ─── Config persistente em arquivo: pasta configuração/ em userData ───
// Export grava aqui por padrão; no início o renderer auto-importa o arquivo.
function configDir() {
  const d = path.join(app.getPath('userData'), 'configuração');
  try { fs.mkdirSync(d, { recursive: true }); } catch (_) {}
  return d;
}
const CONFIG_FILENAME = 'gisele-config.json';
ipcMain.handle('gisele-config:dir', () => { try { return configDir(); } catch (_) { return null; } });
ipcMain.handle('gisele-config:open', () => { try { shell.openPath(configDir()); return true; } catch (_) { return false; } });
ipcMain.handle('gisele-config:save', (_e, text) => {
  try {
    const f = path.join(configDir(), CONFIG_FILENAME);
    fs.writeFileSync(f, String(text == null ? '' : text), 'utf8');
    debugLog('config gravada: ' + f);
    return { ok: true, path: f };
  } catch (err) { debugLog('erro gravando config: ' + (err && err.message)); return { ok: false, error: String(err && err.message) }; }
});
ipcMain.handle('gisele-config:load', () => {
  try {
    const dir = configDir();
    let f = path.join(dir, CONFIG_FILENAME);
    if (!fs.existsSync(f)) {
      let cands = [];
      try { cands = fs.readdirSync(dir).filter((n) => /\.json$/i.test(n)); } catch (_) {}
      if (!cands.length) return { ok: true, found: false };
      cands = cands.map((n) => {
        let t = 0; try { t = fs.statSync(path.join(dir, n)).mtimeMs; } catch (_) {}
        return { n: n, t: t };
      }).sort((a, b) => b.t - a.t);
      f = path.join(dir, cands[0].n);
    }
    const text = fs.readFileSync(f, 'utf8');
    return { ok: true, found: true, path: f, text: text };
  } catch (err) { return { ok: false, error: String(err && err.message) }; }
});

// ─── Cria janela ────────────────────────────────────────────────────
function createWindow() {
  const displayIndices = parseDisplaysArg();
  const allDisplaysFlag = hasFlag('--all-displays');
  const noFrameFlag = hasFlag('--no-frame');

  let bounds = null;
  if (allDisplaysFlag) {
    const all = screen.getAllDisplays();
    bounds = getCombinedBounds(all.map((_, i) => i + 1));
    debugLog('--all-displays: cobrindo todos os ' + all.length + ' monitores');
  } else if (displayIndices) {
    debugLog('--displays solicitado: [' + displayIndices.join(',') + ']');
    bounds = getCombinedBounds(displayIndices);
  } else {
    debugLog('Nenhum --displays passado, usando janela padrão');
  }

  const opts = {
    title: 'GISELE - Gestão Integrada de Soluções Estratégicas e Inteligência',
    backgroundColor: '#0b1220',
    icon: path.join(__dirname, 'icon.ico'),
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: corsStrict() ? true : false,
      allowRunningInsecureContent: corsStrict() ? false : true
    }
  };

  if (bounds) {
    opts.show = false;
    if (noFrameFlag) opts.frame = false;
  } else {
    opts.width = 1440; opts.height = 900;
    opts.minWidth = 900; opts.minHeight = 600;
  }

  const win = new BrowserWindow(opts);
  Menu.setApplicationMenu(null);

  if (bounds) {
    win.setBounds(bounds, false);
    debugLog('setBounds aplicado: ' + JSON.stringify(win.getBounds()));
    win.show();
    setTimeout(() => {
      win.setBounds(bounds, false);
      debugLog('setBounds re-aplicado: ' + JSON.stringify(win.getBounds()));
    }, 300);
  }

  win.loadFile(path.join(__dirname, 'figuras_SisMOM_v23.html'));

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) { shell.openExternal(url); return { action: 'deny' }; }
    return { action: 'allow' };
  });

  // Atalhos de emergência
  win.webContents.on('before-input-event', (event, input) => {
    if (input.key === 'F11' && !input.alt && !input.control) {
      win.setFullScreen(!win.isFullScreen());
    } else if (input.control && input.key.toLowerCase() === 'q') {
      app.quit();
    }
  });
}

app.whenReady().then(async () => {
  debugLog('=== GISELE launch ===');
  debugLog('Versão Electron: ' + process.versions.electron);
  debugLog('Versão Chromium: ' + process.versions.chrome);
  debugLog('CORS mode: ' + (corsStrict() ? 'strict (--strict-cors)' : 'permissive (default, webSecurity=false)'));

  // Sobe o helper Python em paralelo com o createWindow — nao bloqueia o UI.
  // Se nao subir, frontend cai no fallback JS transparente.
  if (!pythonHelperDisabled()) {
    pythonSpawner.start(app).then(result => {
      if (result) {
        debugLog('Python helper UP em ' + result.url + ' (v' + result.version + ')');
        for (const w of BrowserWindow.getAllWindows()) {
          try { w.webContents.send('gisele-python:status', { available: true, url: result.url, version: result.version }); } catch (_) {}
        }
      } else {
        debugLog('Python helper indisponivel — fallback JS sera usado');
      }
    }).catch(e => debugLog('Python helper start ERROR: ' + e.message));
  } else {
    debugLog('Python helper desabilitado via --no-python-helper');
  }

  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('before-quit', () => {
  try { pythonSpawner.stop(); } catch (_) {}
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
