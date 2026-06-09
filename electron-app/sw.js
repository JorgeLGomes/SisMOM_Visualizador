/* ============================================================================
 * GISELE — Service Worker (P2.2)
 * ----------------------------------------------------------------------------
 * Cache-first para os ativos estáticos da aplicação, com fallback de rede.
 * Objetivo: startup quase instantâneo em visitas repetidas (web/PWA) e
 * funcionamento offline básico do shell.
 *
 * Observações importantes:
 *  - Em Electron o app abre via file://, onde service workers NÃO rodam — o
 *    registro no HTML já é ignorado nesse caso. Este SW só atua em http(s)/
 *    localhost (deploy web ou PWA instalada).
 *  - Requisições cross-origin (ex.: tiles/GeoTIFF do FTP do CPTEC/INPE) são
 *    deixadas passar direto para a rede; o cache desses dados já é tratado
 *    pelo proxy Python e pelos caches em memória do frontend.
 * ============================================================================ */

'use strict';

// Suba esta versão a cada release para invalidar o cache antigo.
const CACHE_VERSION = 'v2.13.0';
const CACHE_NAME = 'gisele-static-' + CACHE_VERSION;

// Shell mínimo pré-cacheado na instalação. Mantido enxuto de propósito: o HTML
// principal é grande, então o ganho maior vem de servi-lo do cache nas revisitas.
const PRECACHE_URLS = [
  './',
  './figuras_SisMOM_v23.html',
  './manifest.webmanifest',
  './sismom-icon-192.png',
  './sismom-icon-512.png',
];

// Padrões de ativos same-origin que valem cache-first em runtime.
const RUNTIME_CACHEABLE = [
  /\/vendor\/.*\.(?:js|css)$/i,        // Leaflet etc.
  /\/miscelaneas\/.*\.(?:geojson|json|csv)$/i,
  /\.(?:png|svg|webp|ico|woff2?)$/i,   // ícones, fontes, imagens
];

// ─── install: pré-cacheia o shell ───────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      // addAll é atômico; usamos add individual tolerante a falhas para não
      // abortar a instalação se um ativo opcional faltar (ex.: ícone renomeado).
      .then((cache) => Promise.all(
        PRECACHE_URLS.map((u) => cache.add(u).catch(() => null))
      ))
      .then(() => self.skipWaiting())
  );
});

// ─── activate: remove caches de versões anteriores ──────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k.startsWith('gisele-static-') && k !== CACHE_NAME)
            .map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ─── fetch: estratégia por tipo ─────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Só lidamos com GET. POST (endpoints do helper Python) passa direto.
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Cross-origin (FTP/INPE, CDNs externos): network-only, sem interceptar.
  if (url.origin !== self.location.origin) return;

  // Navegação (documento HTML): network-first com fallback ao cache, para que
  // uma nova versão publicada seja pega quando há rede, mas o app ainda abra
  // offline a partir do shell cacheado.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((resp) => {
          cachePut(req, resp.clone());
          return resp;
        })
        .catch(() => caches.match(req).then((c) => c || caches.match('./figuras_SisMOM_v23.html')))
    );
    return;
  }

  // Ativos estáticos same-origin: cache-first com revalidação em segundo plano.
  if (RUNTIME_CACHEABLE.some((re) => re.test(url.pathname))) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const network = fetch(req)
          .then((resp) => { cachePut(req, resp.clone()); return resp; })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  // Demais GETs same-origin: tenta cache, cai na rede.
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req))
  );
});

// Guarda no cache apenas respostas OK e "básicas" (same-origin).
function cachePut(req, resp) {
  try {
    if (!resp || !resp.ok || (resp.type && resp.type !== 'basic')) return;
    caches.open(CACHE_NAME).then((cache) => cache.put(req, resp)).catch(() => {});
  } catch (_) { /* no-op */ }
}
