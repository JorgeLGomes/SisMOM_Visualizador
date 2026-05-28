const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'GISELE - Gestão Integrada de Soluções Estratégicas e Inteligência',
    backgroundColor: '#0b1220',
    icon: path.join(__dirname, 'icon.ico'),
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      // Permite fetch a URLs HTTPS externas sem CORS bloqueando (caso do FTP do CPTEC).
      // Como o app é carregado de arquivo local e o tráfego é só leitura de figuras,
      // o risco é baixo. Sem isto, decodificar GeoTIFFs do servidor não funciona.
      webSecurity: false,
      allowRunningInsecureContent: true
    }
  });

  Menu.setApplicationMenu(null);
  win.loadFile(path.join(__dirname, 'figuras_SisMOM_v23.html'));

  // Abre links externos (ex.: figuras no FTP do CPTEC) no navegador padrao.
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) { shell.openExternal(url); return { action: 'deny' }; }
    return { action: 'allow' };
  });
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
