const { app, BrowserWindow, Menu, shell, screen } = require('electron');
const path = require('path');
const fs = require('fs');

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
    // Agrupa por linha (tolerância de 100px no Y)
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
// Aceita: --displays=1,2,5,6  OU  --displays 1,2,5,6
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
      webSecurity: false,
      allowRunningInsecureContent: true
    }
  };

  if (bounds) {
    // IMPORTANTE: x/y/width/height direto no constructor às vezes é ignorado
    // pelo Windows quando atravessa monitores. Usar show:false + setBounds depois.
    opts.show = false;
    if (noFrameFlag) opts.frame = false;
  } else {
    opts.width = 1440; opts.height = 900;
    opts.minWidth = 900; opts.minHeight = 600;
  }

  const win = new BrowserWindow(opts);
  Menu.setApplicationMenu(null);

  if (bounds) {
    // setBounds funciona de forma mais previsível em multi-monitor
    win.setBounds(bounds, false);
    debugLog('setBounds aplicado: ' + JSON.stringify(win.getBounds()));
    win.show();
    // Algumas placas dificultam o spanning; força de novo após show
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

  // Atalho de emergência para sair quando frame:false (sem botão fechar):
  // F11 sai, Ctrl+W fecha
  win.webContents.on('before-input-event', (event, input) => {
    if (input.key === 'F11' && !input.alt && !input.control) {
      win.setFullScreen(!win.isFullScreen());
    } else if (input.control && input.key.toLowerCase() === 'q') {
      app.quit();
    }
  });
}

app.whenReady().then(() => {
  debugLog('=== GISELE launch ===');
  debugLog('Versão Electron: ' + process.versions.electron);
  debugLog('Versão Chromium: ' + process.versions.chrome);
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
