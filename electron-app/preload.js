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
