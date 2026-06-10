// preload.js — bridge entre main (Node) e renderer (browser).
//
// Expoe window.GISELE_PYTHON com URL + flag isAvailable para o frontend
// decidir se chama o helper Python ou se usa o fallback JS.
//
// contextIsolation:true e nodeIntegration:false sao mantidos.

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('GISELE_PYTHON', {
  // Obtem URL atual do helper (null se nao subiu)
  getUrl: () => ipcRenderer.invoke('gisele-python:get-url'),

  // Verifica disponibilidade no momento (bate /health do main)
  isAvailable: () => ipcRenderer.invoke('gisele-python:is-available'),

  // Subscribe a eventos de status do helper (UP/DOWN)
  onStatusChange: (cb) => {
    const listener = (_event, status) => cb(status);
    ipcRenderer.on('gisele-python:status', listener);
    return () => ipcRenderer.removeListener('gisele-python:status', listener);
  },
});

// Bridge de sistema de arquivos (ferramenta de download de dados):
// diálogo nativo de escolha de pasta + abrir pasta no gerenciador do SO.
contextBridge.exposeInMainWorld('GISELE_FS', {
  chooseDir: (opts) => ipcRenderer.invoke('gisele-fs:choose-dir', opts || {}),
  openDir: (p) => ipcRenderer.invoke('gisele-fs:open-dir', p),
});

// Bridge de configuração em arquivo (pasta configuração/ em userData).
contextBridge.exposeInMainWorld('GISELE_CONFIG', {
  save: (text) => ipcRenderer.invoke('gisele-config:save', text),
  load: () => ipcRenderer.invoke('gisele-config:load'),
  dir: () => ipcRenderer.invoke('gisele-config:dir'),
  open: () => ipcRenderer.invoke('gisele-config:open'),
});
