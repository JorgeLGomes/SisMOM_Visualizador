#!/usr/bin/env node
/**
 * SisMOM - Servidor HTTP local de dados (Node.js).
 *
 * Equivalente Node do servir_dados.py. Use se você tem Node mas não tem
 * Python — ou se já está usando Electron e quer reusar o runtime.
 *
 * Uso:
 *   node servir_dados.js --dir /caminho/pasta --port 8765
 *
 * CORS aberto, MIME correto pra TIF, listing de diretório no browser.
 */
'use strict';

const http = require('http');
const fs   = require('fs');
const path = require('path');

// ─── Args ────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
let port = 8765, dir = '.', bind = '127.0.0.1';
for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--port' || a === '-p') { port = parseInt(args[++i], 10); }
    else if (a === '--dir'  || a === '-d') { dir = args[++i]; }
    else if (a === '--bind' || a === '-b') { bind = args[++i]; }
    else if (a === '--help' || a === '-h') {
        console.log('Uso: node servir_dados.js [--dir PATH] [--port N] [--bind ADDR]');
        process.exit(0);
    }
}

const ROOT = path.resolve(dir);
try {
    if (!fs.statSync(ROOT).isDirectory()) throw new Error('não é diretório');
} catch (e) {
    console.error(`ERRO: "${ROOT}" ${e.message || 'não é um diretório'}.`);
    process.exit(1);
}

// ─── MIME types ──────────────────────────────────────────────────────
const MIME = {
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.tif': 'image/tiff', '.tiff': 'image/tiff',
    '.json': 'application/json',
    '.geojson': 'application/json',
    '.html': 'text/html; charset=utf-8',
    '.txt':  'text/plain; charset=utf-8',
    '.csv':  'text/csv; charset=utf-8',
    '.svg':  'image/svg+xml',
    '.webmanifest': 'application/manifest+json',
};

function setCors(res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', '*');
    res.setHeader('Cache-Control', 'no-cache');
}

function renderListing(relUrl, items) {
    const rows = items
        .map(it => `<li><a href="${encodeURIComponent(it.name) + (it.dir ? '/' : '')}">` +
                   `${it.dir ? '📁 ' : '📄 '}${it.name}</a></li>`)
        .join('\n');
    return `<!doctype html><meta charset="utf-8">
<title>${relUrl}</title>
<style>body{font-family:ui-monospace,Menlo,monospace;background:#0b1220;color:#e0e6f0;padding:24px}
a{color:#60a5fa;text-decoration:none}a:hover{text-decoration:underline}
ul{list-style:none;padding:0}li{padding:4px 0}h1{font-size:18px;font-weight:700;color:#aab}
</style><h1>📂 ${relUrl}</h1><ul>${rows}</ul>`;
}

// ─── Servidor ────────────────────────────────────────────────────────
const server = http.createServer((req, res) => {
    setCors(res);
    if (req.method === 'OPTIONS') { res.writeHead(200); res.end(); return; }
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); res.end('Method not allowed'); return; }

    let urlPath;
    try {
        urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
    } catch (_) { res.writeHead(400); res.end('400'); return; }

    // Anti path-traversal: resolve e checa se ainda começa com ROOT
    const target = path.normalize(path.join(ROOT, urlPath));
    if (!target.startsWith(ROOT)) { res.writeHead(403); res.end('403 Forbidden'); return; }

    fs.stat(target, (err, st) => {
        if (err) { res.writeHead(404); res.end('404 Not Found'); return; }
        if (st.isDirectory()) {
            // redireciona p/ adicionar / se faltou
            if (!urlPath.endsWith('/')) {
                res.writeHead(301, { Location: urlPath + '/' }); res.end(); return;
            }
            fs.readdir(target, { withFileTypes: true }, (e, ents) => {
                if (e) { res.writeHead(500); res.end('500'); return; }
                const items = ents
                    .map(d => ({ name: d.name, dir: d.isDirectory() }))
                    .sort((a, b) => (a.dir === b.dir) ? a.name.localeCompare(b.name) : (a.dir ? -1 : 1));
                if (urlPath !== '/') items.unshift({ name: '..', dir: true });
                const html = renderListing(urlPath, items);
                res.setHeader('Content-Type', MIME['.html']);
                res.writeHead(200);
                res.end(html);
            });
            return;
        }
        if (!st.isFile()) { res.writeHead(404); res.end('404'); return; }
        const ext = path.extname(target).toLowerCase();
        res.setHeader('Content-Type', MIME[ext] || 'application/octet-stream');
        res.setHeader('Content-Length', String(st.size));
        if (req.method === 'HEAD') { res.writeHead(200); res.end(); return; }
        res.writeHead(200);
        fs.createReadStream(target).pipe(res);
    });
});

server.on('error', (e) => {
    if (e.code === 'EADDRINUSE') {
        console.error(`\nERRO: porta ${port} já está em uso. Use --port N para outra.`);
    } else if (e.code === 'EACCES') {
        console.error(`\nERRO: sem permissão para abrir porta ${port}.`);
    } else {
        console.error('\nERRO:', e.message);
    }
    process.exit(1);
});

server.listen(port, bind, () => {
    const bar = '='.repeat(62);
    console.log(bar);
    console.log(' GISELE — Servidor local de dados (Node.js)');
    console.log(bar);
    console.log(` Diretório:  ${ROOT}`);
    console.log(` URL base:   http://localhost:${port}/`);
    console.log(` Interface:  ${bind}  (127.0.0.1 = só esta máquina)`);
    console.log(' CORS:       habilitado');
    console.log('');
    console.log(' Use no template do modelo (Configurar > Editar):');
    console.log(`   http://localhost:${port}/Eta3km/{yyyy}/{mm}/{dd}{hh}/`);
    console.log('');
    console.log(' Ctrl+C para parar.');
    console.log(bar);
});

process.on('SIGINT', () => { console.log('\nServidor parado.'); process.exit(0); });
