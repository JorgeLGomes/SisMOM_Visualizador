#!/usr/bin/env node
/**
 * GISELE - Bundler do pacote STANDALONE (cross-platform).
 *
 * Cria dist/GISELE-${version}-standalone/ com tudo que o usuário precisa
 * para rodar o app DIRETO no browser sem instalar nada. Também gera o .zip
 * correspondente.
 *
 * Executado automaticamente após qualquer dist:win/linux/mac via hook
 * postdist:* do package.json.
 *
 * Pode ser invocado manualmente:
 *    npm run dist:standalone
 *    node scripts/build-standalone.js
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const root = path.resolve(__dirname, '..');
const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const version = pkg.version || '0.0.0';
const standDir = path.join(root, 'dist', `GISELE-${version}-standalone`);
const zipPath = path.join(root, 'dist', `GISELE-${version}-standalone.zip`);

function log(msg) { process.stdout.write('  ' + msg + '\n'); }

// Garante dist/
fs.mkdirSync(path.join(root, 'dist'), { recursive: true });

// Limpa standalone antigo
if (fs.existsSync(standDir)) {
    fs.rmSync(standDir, { recursive: true, force: true });
}
fs.mkdirSync(standDir, { recursive: true });

console.log(`\n[standalone] Montando pacote GISELE ${version} standalone...`);

// Arquivos a copiar: [origem, destino-no-standalone]
const files = [
    [path.join(root, 'figuras_SisMOM_v23.html'), 'figuras_SisMOM_v23.html'],
    [path.join(root, '..', 'sw.js'),             'sw.js'],
    [path.join(root, 'manifest.webmanifest'),    'manifest.webmanifest'],
    [path.join(root, 'sismom-icon-192.png'),     'sismom-icon-192.png'],
    [path.join(root, 'sismom-icon-512.png'),     'sismom-icon-512.png'],
    [path.join(root, '..', 'SisMOM.bat'),        'SisMOM.bat'],
    [path.join(root, '..', 'SisMOM.sh'),         'SisMOM.sh'],
];

for (const [src, dst] of files) {
    if (fs.existsSync(src)) {
        fs.copyFileSync(src, path.join(standDir, dst));
        log(`OK ${dst}`);
    } else {
        log(`(missing) ${path.basename(src)} — pulando`);
    }
}

// Permissão exec no .sh (se possível neste SO)
try { fs.chmodSync(path.join(standDir, 'SisMOM.sh'), 0o755); } catch (_) {}

// Inclui o servidor HTTP local junto, como bônus
const serverSrcDir = path.resolve(root, '..', 'tools', 'servir_dados');
if (fs.existsSync(serverSrcDir)) {
    const serverDstDir = path.join(standDir, 'tools', 'servir_dados');
    fs.mkdirSync(serverDstDir, { recursive: true });
    for (const f of fs.readdirSync(serverSrcDir)) {
        const s = path.join(serverSrcDir, f);
        const d = path.join(serverDstDir, f);
        if (fs.statSync(s).isFile()) fs.copyFileSync(s, d);
    }
    try { fs.chmodSync(path.join(serverDstDir, 'servir_dados.sh'), 0o755); } catch (_) {}
    log('OK tools/servir_dados/ (incluído)');
}

// LEIA-ME.txt
const readme = `GISELE ${version} - Versao STANDALONE
=====================================================

Esta pasta contem o aplicativo como HTML puro, que roda
direto no navegador, SEM precisar instalar nada.

COMO USAR
----------
 Windows:
   Duplo-clique em SisMOM.bat (abre como janela de app no Edge/Chrome)
   OU duplo-clique em figuras_SisMOM_v23.html (navegador padrao)

 macOS:
   chmod +x SisMOM.sh && ./SisMOM.sh
   OU duplo-clique em figuras_SisMOM_v23.html (Safari/Chrome)

 Linux:
   chmod +x SisMOM.sh && ./SisMOM.sh
   OU duplo-clique em figuras_SisMOM_v23.html

LIMITACAO IMPORTANTE
---------------------
Ao rodar como HTML direto no navegador via file://, o navegador
pode bloquear o download dos arquivos GeoTIFF do FTP do CPTEC
por causa de CORS (politica de seguranca). Se isso acontecer:

 1. Use a versao instalada (.exe / .dmg / .AppImage / .deb).
    O Electron app vem com webSecurity:false e nao tem CORS.

 2. OU rode o SERVIDOR HTTP LOCAL incluido nesta pasta:
       cd tools/servir_dados
       ./servir_dados.sh /caminho/da/pasta-de-dados   (Linux/macOS)
       servir_dados.bat "C:\\dados\\meteorologia"      (Windows)

    No GISELE, configure templates com URLs:
       http://localhost:8765/Eta3km/{yyyy}/{mm}/{dd}{hh}/

ARQUIVOS NESTA PASTA
--------------------
  figuras_SisMOM_v23.html      o app principal
  manifest.webmanifest         metadata PWA
  sismom-icon-192.png          icone PWA 192x192
  sismom-icon-512.png          icone PWA 512x512
  SisMOM.bat                   launcher Windows (Edge/Chrome --app)
  SisMOM.sh                    launcher Linux/macOS
  tools/servir_dados/          servidor HTTP local (opcional)
  LEIA-ME.txt                  este arquivo
`;
fs.writeFileSync(path.join(standDir, 'LEIA-ME.txt'), readme, 'utf8');
log('OK LEIA-ME.txt');

// Zipa
if (fs.existsSync(zipPath)) fs.unlinkSync(zipPath);
const zipBase = path.basename(standDir);
const zipParent = path.dirname(standDir);

function tryZip() {
    // Estratégia 1: PowerShell Compress-Archive (Windows)
    if (process.platform === 'win32') {
        try {
            execSync(
                `powershell -NoProfile -Command "Compress-Archive -Path '${standDir}\\*' -DestinationPath '${zipPath}' -Force"`,
                { stdio: 'ignore' }
            );
            return true;
        } catch (_) { /* fallthrough */ }
    }
    // Estratégia 2: comando 'zip' (Linux/macOS)
    try {
        execSync(`zip -qr "${path.basename(zipPath)}" "${zipBase}"`, { cwd: zipParent, stdio: 'ignore' });
        return true;
    } catch (_) { /* fallthrough */ }
    // Estratégia 3: comando 'tar' que muitos suportam .zip
    try {
        execSync(`tar -a -cf "${path.basename(zipPath)}" "${zipBase}"`, { cwd: zipParent, stdio: 'ignore' });
        return true;
    } catch (_) {}
    return false;
}

if (tryZip()) {
    const stat = fs.statSync(zipPath);
    log(`OK ${path.basename(zipPath)} (${(stat.size / 1024).toFixed(1)} KB)`);
} else {
    log('AVISO: nao foi possivel criar o .zip (sem PowerShell, zip ou tar). Pasta crua disponivel.');
}

console.log(`[standalone] Pronto: ${standDir}`);
