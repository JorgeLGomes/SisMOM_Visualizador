#!/usr/bin/env node
/**
 * GISELE - Minificação do HTML monolítico (P1.3).
 *
 * Minifica `electron-app/figuras_SisMOM_v23.html` IN-PLACE (a cópia usada tanto
 * pelo electron-builder quanto pelo bundler standalone). O fonte legível na raiz
 * do repositório NÃO é tocado.
 *
 * Uso:
 *    node scripts/minify-html.js [origem] [destino]
 *    (padrão: electron-app/figuras_SisMOM_v23.html → mesmo arquivo)
 *
 * IMPORTANTE — segurança:
 *  - mangle:false (NÃO renomeia identificadores). O frontend monta o Web Worker
 *    de decodificação concatenando `decodeTIFF.toString()` + helpers por NOME;
 *    renomear quebraria essa montagem. Por isso só removemos comentários e
 *    espaços em branco do JS, sem compress/mangle agressivos.
 *  - processScripts restrito a JS: os blocos <script type="application/json">
 *    (dados GeoJSON inline das miscelâneas) ficam intactos.
 *  - Falha de minificação NUNCA quebra o build: em erro, mantém o arquivo
 *    original e sai com código 0 (apenas avisa).
 */
'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const SRC = process.argv[2] || path.join(root, 'figuras_SisMOM_v23.html');
const DST = process.argv[3] || SRC;

(async () => {
  let minify;
  try {
    ({ minify } = require('html-minifier-terser'));
  } catch (e) {
    console.warn('[minify] html-minifier-terser indisponível — pulando minificação (HTML mantido sem alterar).');
    process.exit(0);
  }

  let html;
  try {
    html = fs.readFileSync(SRC, 'utf8');
  } catch (e) {
    console.warn('[minify] não foi possível ler ' + SRC + ' — pulando.');
    process.exit(0);
  }

  const before = Buffer.byteLength(html, 'utf8');

  try {
    // ── Mascara os blocos <script type="application/json"> (dados GeoJSON inline)
    // antes de minificar. O html-minifier-terser tenta rodar minifyJS nesses
    // blocos e quebra (JSON não é JS válido). Mascarar com placeholders garante
    // que os dados passem intactos. A regex fecha em </script> OU no fim do
    // arquivo — cobrindo um bloco final eventualmente sem </script>.
    const jsonBlocks = [];
    const masked = html.replace(
      /<script\b[^>]*type=["']application\/json["'][\s\S]*?(?:<\/script>|$)/gi,
      (m) => { jsonBlocks.push(m); return `__GISELE_JSON_BLOCK_${jsonBlocks.length - 1}__`; }
    );

    let out = await minify(masked, {
      collapseWhitespace: true,
      conservativeCollapse: false,
      removeComments: true,
      removeRedundantAttributes: false,
      minifyCSS: true,
      minifyJS: {
        compress: false,                 // sem compressão agressiva
        mangle: false,                   // CRÍTICO: não renomear (worker via toString)
        format: { comments: false },
      },
    });

    // Restaura os blocos JSON (função de replacement p/ não interpretar `$` no JSON).
    jsonBlocks.forEach((b, i) => { out = out.replace(`__GISELE_JSON_BLOCK_${i}__`, () => b); });

    if (!out || out.length < before * 0.3 || /__GISELE_JSON_BLOCK_/.test(out)) {
      // Resultado suspeito (muito menor que o esperado, ou placeholder não restaurado).
      console.warn('[minify] saída suspeita; mantendo o HTML original por segurança.');
      process.exit(0);
    }

    fs.writeFileSync(DST, out, 'utf8');
    const after = Buffer.byteLength(out, 'utf8');
    const pct = (100 * (1 - after / before)).toFixed(1);
    console.log(`[minify] ${(before / 1024).toFixed(0)} KB → ${(after / 1024).toFixed(0)} KB (-${pct}%); ${jsonBlocks.length} bloco(s) JSON preservado(s)`);
  } catch (e) {
    console.warn('[minify] erro ao minificar (' + (e && e.message) + ') — HTML mantido sem alterar.');
    process.exit(0);
  }
})();
