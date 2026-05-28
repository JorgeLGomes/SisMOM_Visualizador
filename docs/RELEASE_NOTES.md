# GISELE 2.0.0

Build: `20260528-0250-calc`
Data: 2026-05-28

## Novidades principais (vs 1.0.0)

### Modo GeoTIFF (novo)
- Aba **GeoTIFF** ao lado de PNG/GIF, com pipeline próprio
- Decodificador TIFF inline (sem dependências externas) — LZW, Deflate, PackBits, float32/int16/uint8, predictor 2, tiles+strips, multi-tiepoint (GrADS)
- Detecção iterativa de sentinelas (NoData) + fallback por percentil 1%/99% para grids com escalas absurdas
- **15 paletas científicas**: Viridis, Plasma, Inferno, Magma, Cividis, Jet, Turbo, Cinza, RdBu, RdYlBu, Spectral, BrBG, Seismic, Coolwarm, Terrain, Ocean

### Multi-painel com mapa-base
- Suporta layouts 1/2/3/4 painéis no modo GeoTIFF
- Cada painel Mi tem seu próprio mapa-base (canvas) com tiles XYZ (Esri Satélite, OSM Ruas, OpenTopoMap)
- Controle de opacidade do raster sobre o mapa, por painel
- Seleção do painel ativo via pin "Painel Mi" no canto do mapa

### Painel direito (sidebar)
- Controles agrupados em seções colapsáveis: Arquivo / Visual, NoData / Clip, Camadas, Calculadora
- Edições no painel afetam **apenas o painel Mi ativo** (gtSlotState por slot)
- Camadas extras (GeoTIFF + GeoJSON) com reordenação, opacidade, visibilidade
- Calculadora de raster: A op B (+, −, ×, ÷) ou A op escalar, gera nova camada derivada

### Filtros e clipping
- UNDEF manual (lista de sentinelas, ex: `-999, -9999`)
- Clip ≥ / Clip ≤ para mascarar fora de faixa
- Recálculo automático de min/max ignorando mascarados

### HUD e navegação
- Valor sob o cursor (lat/lon + valor da célula) na barra inferior
- Pan/zoom no canvas raster (mesmo sem mapa-base)
- Aspect ratio preservado em todos os redimensionamentos

### Performance
- **Cache LRU** de TIFFs decodificados (URL → decoded), imageData (URL+opts → ImageData), blob URL (URL+opts → blob:)
- Dedup in-flight de fetches (mesma URL pedida em paralelo compartilha promessa)
- Reuse de canvas scratch
- Skip de `setTileProvider`/`fitTo` quando inalterado
- Resultado: 2ª passada da animação fica praticamente instantânea após a 1ª caching

### Rotas distintas PNG/TIF por modelo
- Modelo pode declarar `tem_png` / `tem_tif` (formato disponível no FTP)
- Variável pode declarar `disp_png` / `disp_tif`
- Modelos sem TIF são automaticamente filtrados da aba GeoTIFF
- Templates separados de URL/nome para PNG e TIF, com toggle "usar o mesmo do PNG"

### Default ao abrir
- Sempre inicia em PNG/GIF + modelo Eta (estado da aba GeoTIFF preservado em localStorage)

### Empacotamento Electron
- `webSecurity: false` para fetch direto do FTP (CORS bypass)
- `package.json` v2.0.0 com arquivos PWA (manifest, icons múltiplos)
- Scripts `build.bat` e `build.sh` automatizados: sincronizam HTML da raiz, instalam deps, limpam dist/, geram instalador

## Como gerar a distribuição

Veja `electron-app/LEIA-ME-build.txt`. Resumo:

**Windows:**
```
cd electron-app
build.bat
```
Saída em `electron-app/dist/`:
- `GISELE Setup 2.0.0.exe` — instalador NSIS
- `GISELE-2.0.0-portable.exe` — portátil

**Linux:**
```
cd electron-app
chmod +x build.sh && ./build.sh
```
Saída em `electron-app/dist/`:
- `GISELE-2.0.0.AppImage`
- `sismom-visualizador_2.0.0_amd64.deb`

## Verificações pós-build

- [ ] Instalador NSIS executa e cria atalho
- [ ] App abre em PNG/GIF com Eta carregado
- [ ] Troca para GeoTIFF mostra o TIF do passo atual
- [ ] "Mostrar mapa" habilita tiles e opacidade
- [ ] Animação completa uma vez (cache populado)
- [ ] Animação 2ª volta é fluida
- [ ] Volta para PNG/GIF mostra a imagem PNG
- [ ] Configurar > Exportar/Importar funciona
- [ ] Portátil (sem instalação) abre normalmente

## Pendências conhecidas

- Pasta local com varredura (webkitdirectory) — feature solicitada, não implementada
- Paleta/min/max default por variável (persistência) — Fase 3 pendente
- Controles de paleta por painel Mi no header — Fase 4 pendente
- Assinatura digital do .exe — requer certificado pago (~ USD 200/ano), distribuído sem assinatura por ora
- Web Worker para `aplicarPaleta` — 1ª passada da animação ainda é CPU-bound em modelos grandes (Eta)

## Histórico de versões

- **2.0.0** (2026-05-28): Modo GeoTIFF completo, multi-painel com mapa, cache, paletas extras, calculadora.
- **1.0.0** (2026-05-25): Versão inicial PNG/GIF apenas.
