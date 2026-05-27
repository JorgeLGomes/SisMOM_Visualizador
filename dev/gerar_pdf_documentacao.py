#!/usr/bin/env python3
"""
Gera o PDF de documentação da plataforma SisMOM Visualizador (GeoTIFF).
Salva em docs/SisMOM_Visualizador_GeoTIFF.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from pathlib import Path

OUT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador/docs/SisMOM_Visualizador_GeoTIFF.pdf')
OUT.parent.mkdir(parents=True, exist_ok=True)

# ─── Estilos ─────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

NAVY = colors.HexColor('#0b1e3a')
CYAN = colors.HexColor('#0a6e8a')
GRAY_DARK = colors.HexColor('#384858')
GRAY_LIGHT = colors.HexColor('#e6ecf2')
ACCENT = colors.HexColor('#1a8b5e')

styles.add(ParagraphStyle(name='CoverTitle',     parent=styles['Title'],   fontSize=28, leading=34, alignment=TA_CENTER, textColor=NAVY, spaceAfter=10))
styles.add(ParagraphStyle(name='CoverSubtitle',  parent=styles['Title'],   fontSize=16, leading=22, alignment=TA_CENTER, textColor=GRAY_DARK, spaceAfter=4))
styles.add(ParagraphStyle(name='CoverMeta',      parent=styles['Normal'],  fontSize=11, leading=16, alignment=TA_CENTER, textColor=GRAY_DARK))
styles.add(ParagraphStyle(name='H1',             parent=styles['Heading1'],fontSize=18, leading=22, textColor=NAVY, spaceBefore=18, spaceAfter=10))
styles.add(ParagraphStyle(name='H2',             parent=styles['Heading2'],fontSize=14, leading=18, textColor=CYAN, spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle(name='H3',             parent=styles['Heading3'],fontSize=12, leading=16, textColor=GRAY_DARK, spaceBefore=8, spaceAfter=4))
styles.add(ParagraphStyle(name='Body',           parent=styles['BodyText'],fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name='BodyTight',      parent=styles['BodyText'],fontSize=10.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=4))
styles.add(ParagraphStyle(name='BulletItem',     parent=styles['BodyText'],fontSize=10.5, leading=14, leftIndent=14, bulletIndent=4, spaceAfter=3))
styles.add(ParagraphStyle(name='CodeBlock',      parent=styles['Code'],    fontSize=9, leading=12, fontName='Courier', textColor=NAVY, leftIndent=10, spaceAfter=8, backColor=GRAY_LIGHT))
styles.add(ParagraphStyle(name='Caption',        parent=styles['BodyText'],fontSize=9, leading=12, textColor=GRAY_DARK, alignment=TA_CENTER, spaceAfter=10))
styles.add(ParagraphStyle(name='Quote',          parent=styles['BodyText'],fontSize=10, leading=14, leftIndent=18, rightIndent=8, textColor=GRAY_DARK, borderColor=CYAN, borderPadding=4))

def p(txt, style='Body'): return Paragraph(txt, styles[style])
def h1(t): return p(t, 'H1')
def h2(t): return p(t, 'H2')
def h3(t): return p(t, 'H3')
def hr(): return HRFlowable(width='100%', thickness=0.6, color=GRAY_LIGHT, spaceBefore=4, spaceAfter=8)
def code(txt): return Paragraph('<font face="Courier">' + txt.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>') + '</font>', styles['CodeBlock'])
def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(it, styles['BodyTight']), leftIndent=10, value='•') for it in items],
        bulletType='bullet', leftIndent=12, bulletFontSize=10, spaceAfter=8
    )

def make_table(data, col_widths=None, header=True):
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN',   (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 5),
        ('RIGHTPADDING',  (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.3, GRAY_LIGHT),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f6f9fc')]),
    ]
    if header:
        style += [
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ]
    t.setStyle(TableStyle(style))
    return t

# ─── Conteúdo ────────────────────────────────────────────────────────
story = []

# CAPA
story += [
    Spacer(1, 5*cm),
    p('SisMOM Visualizador', 'CoverTitle'),
    p('Plataforma de Visualização Meteorológica<br/>com Suporte a GeoTIFF', 'CoverSubtitle'),
    Spacer(1, 1.5*cm),
    HRFlowable(width='40%', thickness=1.5, color=CYAN, hAlign='CENTER'),
    Spacer(1, 1.2*cm),
    p('Análise dos Produtos Entregues<br/>Detalhes de Implementação · Manual de Utilização', 'CoverMeta'),
    Spacer(1, 4*cm),
    p('CPTEC · INPE · MCTI', 'CoverMeta'),
    p('Maio de 2026', 'CoverMeta'),
    PageBreak(),
]

# ─── 1. SUMÁRIO EXECUTIVO ─────────────────────────────────────────────
story += [
    h1('1. Sumário Executivo'),
    p(
        'O <b>SisMOM Visualizador</b> é uma aplicação single-page HTML, distribuída '
        'como executável Electron (Windows) e AppImage/.deb (Linux), para visualização '
        'das figuras de saída dos modelos meteorológicos do CPTEC. A versão atual '
        'incorpora um conjunto extenso de novas funcionalidades centradas na '
        'visualização de campos em formato <b>GeoTIFF</b>, mantendo plena '
        'compatibilidade com o fluxo PNG/GIF original.'
    ),
    p('<b>Principais entregas desta versão:</b>'),
    bullets([
        '<b>Decoder GeoTIFF</b> próprio, embutido inline, sem dependências externas — suporta TIFF baseline (LZW, Deflate, PackBits, sem compressão), float32/uint16/uint8/int16, predictor 2, tiles e strips, com extração automática de bbox a partir de ModelPixelScale + ModelTiepoint (clássico) ou multi-tiepoint (formato GrADS).',
        '<b>Cinco paletas científicas</b> (Viridis, Jet, RdBu, Cinza, Turbo) implementadas como interpolação de stops, com aplicação adaptativa de NoData e clipping configurável.',
        '<b>Mapa-base custom</b> em canvas, com projeções Plate Carrée e Web Mercator, três provedores de tiles (Esri World Imagery, OpenStreetMap, OpenTopoMap) e fallback offline com costa simplificada da América do Sul + 17 capitais.',
        '<b>Dashboard GeoTIFF</b> acessível por aba no header (PNG/GIF | GeoTIFF), reusando inline a UI do modal local, conectado ao slot 0 do estado global e à animação play/pause/step.',
        '<b>Sistema de camadas</b> empilháveis (GeoTIFF e GeoJSON) com reordenação, ocultação, opacidade por camada, paleta e min/max independentes, colorbars sobrepostas, e detecção iterativa de até 5 sentinels NoData implícitos.',
        '<b>Calculadora de camadas</b> (raster algebra) com operadores +, −, ×, ÷ entre camadas ou camada × escalar (ex.: m → mm).',
        '<b>Interface ergonômica</b>: painel lateral colapsável em accordion, HUD com navegação e amostragem de valor sob o cursor, tabs de modo, botões edge nas duas barras, aspect ratio preservado em redimensionamentos.',
    ]),
    p(
        'Toda a entrega é <b>bicópia em lockstep</b>: o HTML em <font face="Courier">figuras_SisMOM_v23.html</font> '
        'e em <font face="Courier">electron-app/figuras_SisMOM_v23.html</font> são mantidos bit a bit idênticos via '
        'scripts Python de patch direcionado, com validação por <font face="Courier">node --check</font> e smoke tests.'
    ),
    PageBreak(),
]

# ─── 2. VISÃO GERAL DA PLATAFORMA ─────────────────────────────────────
story += [
    h1('2. Visão Geral da Plataforma'),
    h2('2.1 Arquitetura'),
    p(
        'A aplicação é um <b>single-file HTML</b> (~400 KB) com CSS e JavaScript embutidos em '
        'uma IIFE (Immediately Invoked Function Expression). Não há dependências externas '
        'em tempo de execução: nenhum CDN, nenhuma biblioteca via <font face="Courier">&lt;script src&gt;</font>. '
        'Todo o código executa offline a partir de <font face="Courier">file://</font> ou ao ser '
        'empacotado pelo Electron.'
    ),
    p('<b>Camadas lógicas:</b>'),
    bullets([
        '<b>Configuração de modelos</b> (<font face="Courier">DEFAULT_MODELOS</font>) — cada modelo descreve URL FTP, template de arquivo, variáveis, frequência e horizonte.',
        '<b>Estado global</b> (<font face="Courier">state</font>) — slots Mi com modelo/variável/data/passo, layout 1/2/3/4 painéis, animação por passos.',
        '<b>Renderização PNG/GIF</b> — &lt;img&gt; com double-buffering e race-cancellation, pré-cache de N passos.',
        '<b>Renderização GeoTIFF</b> — fetch + decoder TIFF inline + paleta + canvas, com camadas empilhadas e mapa-base opcional.',
        '<b>Persistência</b> — <font face="Courier">localStorage</font> guarda preferências, modelos custom, modo ativo, estado de accordion. <font face="Courier">sessionStorage</font> guarda flags de desbloqueio 2FA.',
        '<b>Empacotamento</b> — Electron (Windows .exe, Linux AppImage/.deb) via electron-builder.',
    ]),
    h2('2.2 Modos de operação'),
    p(
        'Duas abas no header alternam entre <b>PNG/GIF</b> (modo clássico, com painéis M1..Mn '
        'animados) e <b>GeoTIFF</b> (dashboard único conectado ao slot 0). O modo é '
        'persistido em <font face="Courier">localStorage[\'sismom_app_mode\']</font>.'
    ),
    h2('2.3 Pipeline de visualização GeoTIFF'),
    p('Quando um GeoTIFF é carregado (via FTP, file picker local, ou camada extra):'),
    bullets([
        '<b>fetch</b> → ArrayBuffer (ou FileReader.arrayBuffer para local)',
        '<b>decodeTIFF</b> → objeto com <font face="Courier">{width, height, data: Float32Array, bbox, nodata, nodataExtras, min, max, scale}</font>',
        '<b>Detecção iterativa de sentinels</b> — até 5 passes, ignora valores absurdos (NoData implícito) e fallback por percentil 1%/99% em amostra de 10 mil pixels',
        '<b>aplicarPaleta</b>(decoded, opts) → ImageData RGBA, mascarando NoData/clip',
        '<b>createImageBitmap</b> → bitmap pronto para canvas',
        '<b>drawImage</b> no canvas raster OU empurra no SisMOM_Map como overlay',
    ]),
    PageBreak(),
]

# ─── 3. FUNCIONALIDADES ENTREGUES ─────────────────────────────────────
story += [
    h1('3. Funcionalidades Entregues'),
    h2('3.1 Decoder GeoTIFF inline'),
    p('Implementado do zero em JavaScript puro, sem dependência de UTIF, geotiff.js ou similares.'),
    p('<b>Cobertura:</b>'),
    bullets([
        '<b>Header</b>: little-endian (II) e big-endian (MM), magic number 42',
        '<b>Compressão</b>: 1 (sem), 5 (LZW), 8 e 32946 (Deflate, via DecompressionStream nativo), 32773 (PackBits)',
        '<b>SampleFormat</b>: 1 (uint), 2 (int), 3 (float)',
        '<b>BitsPerSample</b>: 8, 16, 32 (incluindo 64 para double)',
        '<b>Layout</b>: strips e tiles (TileWidth/TileLength/TileOffsets)',
        '<b>Predictor 2</b> (horizontal differencing) para compressão de inteiros',
        '<b>GeoKeys</b>: ModelPixelScale (33550), ModelTiepoint (33922) — 1 ou múltiplos tiepoints',
        '<b>GDAL_NODATA</b> (42113) — string ASCII parseada para float',
        '<b>Normalização de longitude</b> 0..360 → −180..180 — aplicada apenas quando todas as longitudes estão em [0, 360] e alguma > 180',
    ]),
    p('<b>NÃO cobre</b> (limitações conscientes): JPEG-in-TIFF, BigTIFF (&gt; 4 GB), CCITT, projeções não-geográficas (UTM, sinusoidal).'),

    h2('3.2 Paletas de cores'),
    p('Cinco paletas científicas, implementadas como interpolação linear de stops de cor (RGB) para 256 amostras:'),
    make_table([
        ['Paleta', 'Aplicação típica', 'Tipo'],
        ['Viridis', 'Default; perceptualmente uniforme', 'Sequencial'],
        ['Jet',     'Familiar em meteorologia tropical', 'Sequencial (não-uniforme)'],
        ['RdBu',    'Anomalias centradas em zero',       'Divergente'],
        ['Cinza',   'Inspeção crua, contraste',          'Sequencial'],
        ['Turbo',   'Substituto moderno de Jet',         'Sequencial'],
    ], col_widths=[3*cm, 8.5*cm, 4.5*cm]),
    Spacer(1, 4),
    p('A função <font face="Courier">aplicarPaleta(decoded, opts)</font> aceita opções de paleta, min/max custom, nodataExtras, clipBelow e clipAbove. Pixels mascarados retornam alpha=0 (transparentes).'),

    h2('3.3 Mapa-base'),
    p('Módulo <b>SisMOM_Map</b> próprio, em canvas 2D, com duas projeções:'),
    bullets([
        '<b>Plate Carrée</b> — lat/lon linear, sem tiles, com costa SA + 17 capitais + grade lat/lon',
        '<b>Web Mercator</b> — projeção padrão de tiles XYZ; ativa quando se escolhe um provider',
    ]),
    p('<b>Três provedores de tiles</b> (sem API key):'),
    make_table([
        ['Provedor', 'URL template', 'Uso típico'],
        ['Esri World Imagery', 'arcgisonline.com/.../{z}/{y}/{x}', 'Satélite (default)'],
        ['OpenStreetMap', 'tile.openstreetmap.org/{z}/{x}/{y}.png', 'Ruas'],
        ['OpenTopoMap', 'a.tile.opentopomap.org/{z}/{x}/{y}.png', 'Topográfico'],
    ], col_widths=[4*cm, 8*cm, 4*cm]),
    Spacer(1, 4),
    p(
        'Cache de até 400 tiles em RAM. Atribuição automática no canto inferior esquerdo do canvas, '
        'conforme provider ativo. Pan/zoom respeitam aspect ratio do canvas, com clamp de lonSpan ≤ 360°.'
    ),

    PageBreak(),

    h2('3.4 Sistema de camadas'),
    p(
        'Toda renderização raster passa por um array unificado <font face="Courier">overlays[]</font> no '
        '<b>SisMOM_Map</b>. A camada base (do slot 0 ou arquivo aberto) é apenas mais uma '
        'entry com flag <font face="Courier">isPrimary: true</font> (que adiciona a moldura tracejada da bbox). '
        'Pode ser reordenada, ocultada e ter sua opacidade ajustada como qualquer outra.'
    ),
    p('<b>Camadas extras:</b>'),
    bullets([
        '<b>GeoTIFF</b> (.tif/.tiff): paleta, min/max, UNDEF, clip, opacidade independentes',
        '<b>GeoJSON</b> (.geojson/.json): cor cíclica de paleta de 8 cores, suporte a Polygon/MultiPolygon/LineString/MultiLineString',
    ]),
    p('Controles do painel lateral operam sobre a <b>camada ativa</b> (clique no chip seleciona). Cada camada armazena suas próprias propriedades em <font face="Courier">layer.props</font>: paleta, autoMinMax, customMin/customMax, undefRaw, clipBelow, clipAbove, effMin/effMax recalculados após filtros.'),

    h2('3.5 HUD inferior e amostragem'),
    p(
        'Barra flutuante no canto inferior esquerdo do canvas com botões <b>+ − ⟲</b> (zoom in/out/reset) '
        'e display de <b>lat°, lon° · valor</b> sob o cursor. Funciona tanto no mapa (Mercator) '
        'quanto no canvas raster puro. A amostragem do valor respeita NoData explícito, NoData '
        'implícito (heurística) e filtros UNDEF/clip da camada base.'
    ),

    h2('3.6 Colorbar e pilha de colorbars'),
    p(
        'Colorbar canvas com gradient da paleta corrente, 5 ticks (min, 25 %, 50 %, 75 %, max) com '
        'formatação adaptativa (fixed/exponential conforme magnitude). Acima do HUD inferior, '
        'uma pilha mostra mini-colorbars de <b>cada camada raster visível</b> (nome + gradient + '
        'min…max), refletindo a ordem das camadas no mapa.'
    ),

    h2('3.7 Calculadora de camadas (raster algebra)'),
    p(
        'Linha de controles na seção CAMADAS permite criar uma nova camada a partir de uma '
        'expressão A <i>op</i> B, onde B pode ser outra camada GeoTIFF (mesma dimensão) ou um '
        'valor escalar. Operadores: + − × ÷.'
    ),
    p('Exemplos típicos:'),
    bullets([
        '<b>Conversão de unidades</b>: prec_em_metros × 1000 → prec_em_mm',
        '<b>Conversão de temperatura</b>: temp_kelvin − 273.15 → temp_celsius',
        '<b>Anomalia</b>: temp_2025 − temp_2024 → diferença',
        '<b>Razão</b>: prec_total ÷ dias_chuva → intensidade média',
    ]),
    p('Tratamento de NoData: qualquer fonte com pixel mascarado gera NoData no resultado; divisão por zero também.'),

    h2('3.8 Interface ergonômica'),
    bullets([
        '<b>Tabs de modo</b> no header: [PNG/GIF] [GeoTIFF], persistidas em localStorage',
        '<b>Painel lateral direito</b> colapsável (botão ‹/›), com seções em <b>accordion</b> (Arquivo/Visual, NoData/Clip, Camadas) — estado por seção persistido',
        '<b>Botão edge</b> análogo na sidebar esquerda, reusando toggleSidebar existente',
        '<b>Aspect ratio</b> preservado em qualquer redimensionamento do canvas (pan/zoom recalcula latSpan/mercYSpan)',
        '<b>Chips de camadas</b> com nomes truncados (ellipsis), tooltip no hover, controles ↑↓👁✕ na lateral',
    ]),

    PageBreak(),
]

# ─── 4. FERRAMENTAS E TECNOLOGIAS ─────────────────────────────────────
story += [
    h1('4. Ferramentas e Tecnologias'),
    h2('4.1 Stack de execução'),
    make_table([
        ['Camada', 'Tecnologia', 'Versão / Observação'],
        ['Linguagem', 'JavaScript (ES2017+)', 'IIFE, async/await, Float32Array'],
        ['Runtime browser', 'Chromium (Electron)', '~v122+ esperado'],
        ['Markup', 'HTML5 + CSS3', 'Single-file, sem build step'],
        ['Empacotamento Win', 'electron-builder (NSIS + portable)', 'icon.ico'],
        ['Empacotamento Linux', 'AppImage + .deb', 'compilado em WSL/Docker'],
        ['CI/CD', 'GitHub Actions', 'matrix windows-latest + ubuntu-latest'],
        ['Persistência', 'localStorage / sessionStorage', 'Por-origem, sem servidor'],
    ], col_widths=[4*cm, 6*cm, 6*cm]),

    h2('4.2 APIs do navegador usadas'),
    bullets([
        '<b>Canvas 2D</b> — renderização do raster, mapa, colorbars',
        '<b>fetch + ArrayBuffer</b> — leitura de GeoTIFFs do FTP e de arquivos locais',
        '<b>DataView</b> — parsing binário de tags TIFF',
        '<b>DecompressionStream(\'deflate\')</b> — descompressão Deflate sem dependência',
        '<b>createImageBitmap</b> — bitmaps GPU-friendly para canvas overlay',
        '<b>FileReader / File.arrayBuffer</b> — upload local',
        '<b>ResizeObserver</b> — redraw em mudança de tamanho do canvas',
        '<b>MutationObserver</b> — sincronização de UI entre controles',
        '<b>Web Crypto (HMAC-SHA-1)</b> — TOTP do sistema 2FA (entrega anterior)',
    ]),

    h2('4.3 Endpoints externos'),
    make_table([
        ['Serviço', 'Endpoint', 'Restrições'],
        ['Esri World Imagery', 'server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/...', 'Atribuição obrigatória'],
        ['OpenStreetMap', 'tile.openstreetmap.org/...', 'Uso pesado exige User-Agent'],
        ['OpenTopoMap', 'a.tile.opentopomap.org/...', 'CC-BY-SA'],
        ['CPTEC FTP', 'ftp1.cptec.inpe.br/pesquisa/SisMOM/sismom_fig/...', 'Sem CORS; exige webSecurity:false no Electron'],
    ], col_widths=[4*cm, 8*cm, 4*cm]),

    h2('4.4 Bibliotecas dispensadas (refatoração para inline)'),
    p('Durante o desenvolvimento, foram avaliadas e <b>rejeitadas</b> as seguintes bibliotecas externas — todas substituídas por implementação inline própria, mantendo o requisito de zero CDN e zero dependência empacotada:'),
    make_table([
        ['Lib', 'Substituto', 'Motivo'],
        ['geotiff.js (~210 KB)', 'decodeTIFF próprio (~12 KB)', 'Tamanho 18× menor; cobre os formatos GrADS/CPTEC'],
        ['UTIF.js (~50 KB)', 'decodeTIFF próprio', 'Não precisava do parser TIFF genérico'],
        ['Leaflet (~140 KB)', 'SisMOM_Map próprio (~22 KB)', 'Bloqueio de download corporativo; controles próprios bastam'],
        ['qrcode.js / Google Charts', 'Gerador QR inline (ISO 18004)', 'Entrega anterior (2FA), restrição de offline'],
        ['Plotly.js', 'Canvas 2D', 'Não precisamos de gráficos interativos'],
    ], col_widths=[4.5*cm, 5.5*cm, 6*cm]),

    PageBreak(),
]

# ─── 5. MANUAL DE UTILIZAÇÃO ──────────────────────────────────────────
story += [
    h1('5. Manual de Utilização'),
    h2('5.1 Instalação'),
    p('<b>Windows</b>: baixe o instalador .exe ou a versão portátil do release do GitHub. Execute. O ícone fica disponível no menu Iniciar.'),
    p('<b>Linux</b>: baixe o .AppImage e dê permissão de execução (<font face="Courier">chmod +x</font>), ou instale o .deb (<font face="Courier">sudo dpkg -i sismom_visualizador_*.deb</font>).'),
    p('<b>Browser (modo dev)</b>: abra <font face="Courier">figuras_SisMOM_v23.html</font> direto no Chrome/Edge. Recursos de mapa via FTP exigirão CORS permitido — preferível usar o Electron.'),

    h2('5.2 Primeira execução'),
    p('Na abertura, o painel mostra o modo PNG/GIF com 1 painel M1, modelo Eta · 3 km e data corrente. Para entrar no modo GeoTIFF, clique na aba <b>[GeoTIFF]</b> no canto superior esquerdo do header.'),

    h2('5.3 Abrindo um GeoTIFF local'),
    bullets([
        'No modo GeoTIFF, clique em <b>Abrir arquivo…</b> no painel direito (seção ARQUIVO / VISUAL)',
        'Selecione um arquivo .tif/.tiff. O arquivo é decodificado e exibido com paleta Viridis (default) e min/max automáticos',
        'Se o arquivo tiver georreferência (bbox), o toggle <b>Mostrar mapa</b> fica habilitado. Marque-o para sobrepor o raster ao mapa-base (Esri World Imagery por default)',
        'Use o slider de <b>Opacidade</b> para ajustar a transparência da camada ativa',
    ]),

    h2('5.4 Trocando paleta e ajustando escala'),
    bullets([
        'Combo <b>Paleta</b>: alterna entre Viridis, Jet, RdBu, Cinza, Turbo',
        'Campos <b>Min</b> e <b>Max</b>: começam em modo auto (somente leitura). Clique em <b>Editar escala</b> para fixar valores manuais; clique em <b>Auto</b> para voltar ao automático',
        'Mudanças refletem imediatamente no raster, na colorbar inferior e na mini-colorbar da pilha (canto inferior esquerdo do canvas)',
    ]),

    h2('5.5 Mascarando valores'),
    p('Seção <b>NODATA / CLIP</b>:'),
    bullets([
        '<b>UNDEF</b>: digite um ou vários valores separados por vírgula (ex.: <font face="Courier">-999, -9999</font>). Pixels iguais a esses valores ficam transparentes',
        '<b>Clip ≥</b>: pixels com valor abaixo do limite ficam mascarados',
        '<b>Clip ≤</b>: pixels com valor acima do limite ficam mascarados',
        '<b>Limpar</b>: remove todos os filtros',
    ]),
    p('Para o GeoTIFF que tem GDAL_NODATA explícito, o decoder já mascara automaticamente. Para arquivos com sentinels implícitos (ex.: −999000000), a detecção heurística os identifica e o min/max já vem ajustado.'),

    h2('5.6 Camadas extras'),
    bullets([
        'Botão <b>+ Adicionar GeoTIFF/GeoJSON…</b>: abre o seletor de arquivos (.tif/.tiff/.geojson/.json)',
        'Chips listam todas as camadas em ordem; <b>↑/↓</b> reordenam; <b>👁</b> oculta/mostra; <b>✕</b> remove',
        'Clique no chip para selecionar como <b>camada ativa</b> — os controles de paleta/min/max/UNDEF/clip passam a afetar apenas ela',
        'Botão <b>Limpar</b> remove todas as extras (com confirmação); a base permanece',
    ]),

    h2('5.7 Calculadora'),
    p('Na seção CAMADAS, a linha <b>Calc:</b> permite criar nova camada via operação:'),
    bullets([
        'Selecione a camada A no primeiro combo',
        'Escolha o operador (<font face="Courier">+ − × ÷</font>)',
        'No segundo combo, selecione outra camada B <i>ou</i> mantenha <b>(valor escalar)</b>',
        'Se for escalar, digite o número no input ao lado',
        'Clique <b>Calcular</b>. A nova camada aparece nos chips com nome descritivo, ex.: <font face="Courier">(prec.tif × 1000)</font>',
    ]),

    h2('5.8 Navegação no mapa'),
    bullets([
        '<b>Pan</b>: clique e arraste no mapa',
        '<b>Zoom</b>: rolagem do mouse (centrada no cursor); ou botões <b>+</b> e <b>−</b> do HUD inferior',
        '<b>Reset</b>: botão <b>⟲</b> do HUD reposiciona o viewport na bbox da camada base',
        '<b>HUD</b>: mostra lat°, lon° e valor sob o cursor em tempo real',
        '<b>Trocar camada de fundo</b>: combo <b>Camada</b> alterna entre Satélite (Esri), Ruas (OSM), Topo (OpenTopoMap), ou Sem tiles',
    ]),

    h2('5.9 Animação por passos'),
    p(
        'No modo GeoTIFF, o sistema reconhece a aba e usa a URL derivada do modelo: '
        'a extensão .png/.gif/.jpg é substituída por .tif automaticamente. O timeline da '
        'sidebar esquerda (PASSOS DE TEMPO, ANIMAÇÃO) continua funcionando — aperte <b>Animar</b> '
        'e o painel GeoTIFF avança quadro a quadro, decodificando cada arquivo do FTP em tempo real.'
    ),
    p('<b>Atenção</b>: arquivos grandes (&gt; 5 MB) podem tornar a animação picotada. Para inspeção quadro a quadro, prefira <b>Próximo passo</b> manual.'),

    PageBreak(),
]

# ─── 6. LIMITAÇÕES E ROADMAP ─────────────────────────────────────────
story += [
    h1('6. Limitações Conhecidas e Roadmap'),
    h2('6.1 Limitações atuais'),
    make_table([
        ['Limitação', 'Workaround / Caminho futuro'],
        ['Sem suporte a JPEG-in-TIFF', 'Pode ser adicionado via decoder JPEG nativo'],
        ['Sem BigTIFF (> 4 GB)', 'Raro em saídas operacionais; pode estender header'],
        ['Sem reprojeção UTM/sinusoidal', 'Adicionar proj4 lib ou conversão server-side'],
        ['1 painel GeoTIFF (não M1..Mn)', 'Use camadas extras para empilhar comparações'],
        ['Animação grande pode travar', 'Pré-cache assíncrono de N passos (próxima iteração)'],
        ['CORS no FTP exige webSecurity:false', 'Configurado no main.js; ou usar proxy server-side'],
        ['Calculadora exige mesma dimensão A/B', 'Reamostragem bilinear (próxima iteração)'],
        ['Sem pasta com varredura local', 'Hoje só arquivo único; webkitdirectory está planejado'],
    ], col_widths=[8*cm, 8*cm]),

    h2('6.2 Roadmap proposto'),
    bullets([
        '<b>Pasta local com varredura</b>: input <font face="Courier">webkitdirectory</font> + lista de .tif/.tiff navegáveis',
        '<b>Multi-painel no modo GeoTIFF</b>: replicar layout 1/2/3/4 do PNG, cada painel com seu próprio slot',
        '<b>Pré-cache assíncrono</b> dos próximos N passos durante animação',
        '<b>Reamostragem</b> automática para calculadora aceitar camadas de dimensões diferentes',
        '<b>Comparação split-screen</b>: modo extra nas tabs ([PNG] [GeoTIFF] [Comparação])',
        '<b>Exportação</b> da camada calculada como GeoTIFF (download local)',
        '<b>Suporte a ModelTransformation</b> (tag 34264, matriz afim 4×4)',
        '<b>Indicadores cartográficos</b>: setas de clip nos extremos da colorbar',
    ]),

    PageBreak(),
]

# ─── 7. APÊNDICE ─────────────────────────────────────────────────────
story += [
    h1('7. Apêndice'),
    h2('7.1 Estrutura de arquivos do projeto'),
    code(
        'C:\\Projetos\\Visualizador\\\n'
        '├── figuras_SisMOM_v23.html        # HTML principal (raiz) ~396 KB\n'
        '├── BRIEFING_SESSAO.md             # Documento de transferência\n'
        '├── SisMOM.bat / SisMOM.sh         # Launchers\n'
        '├── electron-app/\n'
        '│   ├── figuras_SisMOM_v23.html    # Cópia idêntica para Electron\n'
        '│   ├── main.js                    # webSecurity:false configurado\n'
        '│   ├── package.json               # electron-builder config\n'
        '│   └── icon.ico\n'
        '├── dev/                           # Scripts Python de patch\n'
        '│   ├── geotiff_module.js          # Módulo decoder standalone\n'
        '│   ├── map_module.js              # Módulo mapa standalone\n'
        '│   ├── test_geotiff.mjs           # 8 testes unitários do decoder\n'
        '│   ├── test_map.mjs               # Smoke tests do mapa\n'
        '│   ├── patch_*.py                 # Patches aplicados em lockstep\n'
        '│   └── inspect_tiff.mjs           # Inspetor de tags TIFF\n'
        '├── docs/\n'
        '│   └── SisMOM_Visualizador_GeoTIFF.pdf   # Este documento\n'
        '└── .github/workflows/release.yml  # CI/CD'
    ),

    h2('7.2 Padrão de patches em lockstep'),
    p(
        'Toda mudança no HTML é aplicada simultaneamente nas duas cópias '
        '(raiz e electron-app) via scripts Python idempotentes em <font face="Courier">dev/patch_*.py</font>. '
        'Cada script: define âncoras de string únicas, substitui pelo conteúdo novo, valida '
        'identidade bit-a-bit das duas cópias e roda <font face="Courier">node --check</font> '
        'no JavaScript extraído. Esse padrão previne divergência silenciosa.'
    ),

    h2('7.3 Validação'),
    p('Cada feature passou por:'),
    bullets([
        '<b>node --check</b> do JS extraído do HTML',
        '<b>diff -q</b> entre as duas cópias do HTML — devem ser idênticas',
        '<b>Smoke tests</b> em <font face="Courier">.mjs</font> para módulos isoláveis (decoder, mapa)',
        '<b>Testes de regressão</b> com arquivos reais: Prec-0001.tif (GrADS Pacífico), temp-0010.tif (GrADS global), prec_eta3km.tif (Eta 3 km regional), Eta10_C00_PREC.tif (múltiplos sentinels)',
    ]),

    h2('7.4 Tamanho final'),
    make_table([
        ['Componente', 'Tamanho', 'Observação'],
        ['HTML principal', '~396 KB', 'Auto-contido, sem dependências externas'],
        ['main.js', '1.5 KB', 'Bootstrap do Electron'],
        ['package.json', '~2 KB', 'electron-builder'],
        ['Total entregue (.exe)', '~85 MB', 'Inclui runtime Chromium'],
        ['Total entregue (.AppImage)', '~95 MB', 'Inclui runtime Chromium'],
    ], col_widths=[6*cm, 4*cm, 6*cm]),

    Spacer(1, 1*cm),
    hr(),
    p('<i>Documento gerado automaticamente pela toolchain do projeto. Para a versão sempre atualizada, consulte <font face="Courier">BRIEFING_SESSAO.md</font> na raiz do repositório.</i>', 'Caption'),
]

# ─── Build PDF ────────────────────────────────────────────────────────
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GRAY_DARK)
    canvas.drawRightString(A4[0] - 1.5*cm, 1*cm, f'Página {doc.page}')
    canvas.drawString(1.5*cm, 1*cm, 'SisMOM Visualizador — Documentação')
    canvas.setStrokeColor(GRAY_LIGHT)
    canvas.setLineWidth(0.4)
    canvas.line(1.5*cm, 1.3*cm, A4[0] - 1.5*cm, 1.3*cm)
    canvas.restoreState()

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=1.8*cm,
    title='SisMOM Visualizador — Documentação',
    author='CPTEC / INPE / MCTI',
)
doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=add_page_number)
sz = OUT.stat().st_size
print("PDF gerado: " + str(OUT) + " (" + str(sz) + " bytes)")
