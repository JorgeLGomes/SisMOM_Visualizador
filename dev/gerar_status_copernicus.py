#!/usr/bin/env python3
"""
Gera o PDF de STATUS DE ADEQUACAO do GISELE a plataforma COPERNICUS (MPSP/INPE).

Base: ADEQUACAO_COPERNICUS.md, atualizado para o estado atual do GISELE (v2.14.0).
Saida: docs/GISELE_Status_Adequacao_Copernicus.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from pathlib import Path
from datetime import date

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'GISELE_Status_Adequacao_Copernicus.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)

# Fonte com glifo de quadrado (cheio) para os marcadores coloridos de status
SQ_FONT = None
for _fp in [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    r'C:\Windows\Fonts\arial.ttf',
    r'C:\Windows\Fonts\seguisym.ttf',
    '/Library/Fonts/Arial Unicode.ttf',
]:
    try:
        if os.path.exists(_fp):
            pdfmetrics.registerFont(TTFont('SqFont', _fp)); SQ_FONT = 'SqFont'; break
    except Exception:
        pass

SQUARE = '■'  # quadrado preto cheio
def sq(hexcolor):
    if SQ_FONT:
        return '<font name="%s" color="%s">%s</font>' % (SQ_FONT, hexcolor, SQUARE)
    return '<font color="%s">&bull;</font>' % hexcolor

NAVY   = colors.HexColor('#0b1e3a')
CYAN   = colors.HexColor('#0a6e8a')
GRAY_D = colors.HexColor('#384858')
GRAY_M = colors.HexColor('#6a7c8e')
GRAY_L = colors.HexColor('#e6ecf2')
GRAY_BG= colors.HexColor('#f6f9fc')
OK_HEX = '#1a7a43'; MID_HEX = '#9a5a00'; NO_HEX = '#a32222'
OK_BG  = colors.HexColor('#e6f4ea'); OK_FG  = colors.HexColor(OK_HEX)
MID_BG = colors.HexColor('#fff4e0'); MID_FG = colors.HexColor(MID_HEX)
NO_BG  = colors.HexColor('#fdeaea'); NO_FG  = colors.HexColor(NO_HEX)

styles = getSampleStyleSheet()
S = lambda name, **kw: styles.add(ParagraphStyle(name=name, **kw))
S('CoverTitle',    parent=styles['Title'],  fontSize=26, leading=32, alignment=TA_CENTER, textColor=NAVY,  spaceAfter=8)
S('CoverSubtitle', parent=styles['Title'],  fontSize=14, leading=20, alignment=TA_CENTER, textColor=GRAY_D, spaceAfter=4)
S('CoverMeta',     parent=styles['Normal'], fontSize=11, leading=16, alignment=TA_CENTER, textColor=GRAY_M)
S('H1',  parent=styles['Heading1'], fontSize=17, leading=21, textColor=NAVY, spaceBefore=16, spaceAfter=9)
S('H2',  parent=styles['Heading2'], fontSize=13, leading=17, textColor=CYAN, spaceBefore=11, spaceAfter=5)
S('Body',  parent=styles['BodyText'], fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=7)
S('Item',  parent=styles['BodyText'], fontSize=10,   leading=13.5, spaceAfter=2)
S('Cell',  parent=styles['BodyText'], fontSize=8.6,  leading=11)
S('CellB', parent=styles['BodyText'], fontSize=8.6,  leading=11, textColor=NAVY)
S('CellH', parent=styles['BodyText'], fontSize=8.8,  leading=11, textColor=colors.white)
S('Tip',   parent=styles['BodyText'], fontSize=9.6,  leading=13, leftIndent=10, rightIndent=8, spaceAfter=7, textColor=GRAY_D, backColor=GRAY_BG, borderPadding=6, borderColor=CYAN)

def p(txt, style='Body'): return Paragraph(txt, styles[style])
def h1(t): return p(t, 'H1')
def h2(t): return p(t, 'H2')
def hr(): return HRFlowable(width='100%', thickness=0.6, color=GRAY_L, spaceBefore=4, spaceAfter=8)
def bullets(items):
    return ListFlowable([ListItem(p(i, 'Item'), leftIndent=10, value='•') for i in items],
                        bulletType='bullet', start='•', leftIndent=12, bulletColor=CYAN)

_STMAP = {'OK': ('Atende', OK_BG, OK_FG, OK_HEX),
          'MID': ('Parcial', MID_BG, MID_FG, MID_HEX),
          'NO': ('Ausente', NO_BG, NO_FG, NO_HEX)}

def status_table(rows, widths):
    data = [[p('Requisito (spec)', 'CellH'), p('GISELE hoje', 'CellH'), p('Status', 'CellH'), p('Ação de adequação', 'CellH')]]
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), CYAN),
        ('GRID', (0, 0), (-1, -1), 0.4, GRAY_L),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_BG]),
    ]
    for i, r in enumerate(rows, start=1):
        label, bg, fg, hexc = _STMAP[r[2]]
        cell = Paragraph(sq(hexc) + ' ' + label, ParagraphStyle('st%d' % i, fontSize=8.6, leading=11, textColor=fg))
        data.append([p(r[0], 'CellB'), p(r[1], 'Cell'), cell, p(r[3], 'Cell')])
        style.append(('BACKGROUND', (2, i), (2, i), bg))
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle(style))
    return t

def counts(n_ok, n_mid, n_no, suffix=''):
    return ('%d ' % n_ok) + sq(OK_HEX) + (' &nbsp;&middot;&nbsp; %d ' % n_mid) + sq(MID_HEX) + (' &nbsp;&middot;&nbsp; %d ' % n_no) + sq(NO_HEX) + suffix

def _footer(canvas, doc_):
    canvas.saveState()
    canvas.setStrokeColor(GRAY_L); canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.5*cm, A4[0]-2*cm, 1.5*cm)
    canvas.setFont('Helvetica', 8.5); canvas.setFillColor(GRAY_M)
    canvas.drawString(2*cm, 1.1*cm, 'GISELE → COPERNICUS — Status de Adequação')
    canvas.drawRightString(A4[0]-2*cm, 1.1*cm, 'Página %d' % doc_.page)
    canvas.restoreState()

doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm, topMargin=1.8*cm, bottomMargin=2*cm,
                        title='GISELE - Status de Adequacao COPERNICUS')
story = []

story += [
    Spacer(1, 4.5*cm),
    p('GISELE → Plataforma COPERNICUS', 'CoverTitle'),
    p('Status de Adequação — situação atual e lacunas', 'CoverSubtitle'),
    Spacer(1, 1*cm),
    p('Visualizador (Card 1) · Editor Vetorial (Card 2) · Gerador de Iframes (Card 3) · Portal de Importação (Card 4)', 'CoverMeta'),
    Spacer(1, 0.5*cm),
    p('MPSP · INPE · CPTEC', 'CoverMeta'),
    Spacer(1, 3.5*cm),
    p('Referência: ADEQUACAO_COPERNICUS.md · GISELE v2.14.0', 'CoverMeta'),
    p('Atualizado em ' + date.today().strftime('%d/%m/%Y'), 'CoverMeta'),
]
story.append(PageBreak())

story.append(h1('1. Contexto e objetivo'))
story.append(p(
    'A plataforma COPERNICUS (MPSP/INPE) é <b>cloud-native</b>: substitui o servidor de mapas '
    'monolítico por um fluxo <b>FastAPI (gateway) + MinIO/COG + PostGIS + TiTiler + endpoint MVT + '
    'STAC/pgSTAC</b>, com <b>segurança JWT do Login Único gov.br</b>, URLs assinadas, Redis e Celery, '
    'CRS sem reprojeção destrutiva e <b>cadeia de custódia auditável</b> (two-person rule, Meta 1 do MPSP).'
))
story.append(p(
    'Este documento consolida o <b>status atual</b> do GISELE frente a essa especificação — o que já '
    '<b>atende</b>, o que é <b>parcial/adaptável</b> e o que está <b>ausente</b> (a construir) — por '
    'módulo e nos eixos transversais, além do roteiro faseado de adequação.'
))
story.append(p('<b>Legenda:</b> ' + sq(OK_HEX) + ' Atende &nbsp;&middot;&nbsp; ' + sq(MID_HEX) + ' Parcial / adaptável &nbsp;&middot;&nbsp; ' + sq(NO_HEX) + ' Ausente (a construir).', 'Item'))

story.append(h2('2. Posição atual do GISELE (v2.14.0)'))
story.append(p(
    'O GISELE é hoje um <b>visualizador geoespacial client-side de alto nível</b> (HTML único + '
    'JavaScript, empacotado em Electron; canvas próprio <i>SisMOM_Map</i>), com decodificador GeoTIFF '
    'próprio, paletas, contornos, modo PNG/GIF do CPTEC e um <i>helper</i> Python opcional (FastAPI + '
    'rasterio) que apenas acelera amostragem/perfil. <b>Não há</b> COG/MinIO, TiTiler, PostGIS, MVT, '
    'STAC, autenticação, multiusuário, auditoria, object storage ou fila assíncrona.'
))
story.append(Paragraph(
    '<b>Veredito:</b> a sobreposição real é o papel de <b>Visualizador (Card 1)</b>, onde o GISELE é '
    'forte. Cards 2, 3 e 4 e os eixos transversais são essencialmente <b>back-end novo (greenfield)</b>. '
    'A adequação é menos "refatorar o GISELE" e mais "construir a plataforma de servidor" e posicionar '
    'o GISELE (ou sua UX) como o front-end do Card 1.', styles['Tip']))

story.append(PageBreak())
story.append(h1('3. Status por módulo'))

story.append(h2('Card 1 — Visualizador &nbsp; ' + counts(7, 6, 3, ' &nbsp;(de 16)')))
story.append(status_table([
    ['Stack React + MapLibre GL', 'Vanilla JS + canvas próprio', 'MID', 'Decisão estratégica (§5): migrar para MapLibre ou manter o canvas consumindo as mesmas APIs.'],
    ['Raster via TiTiler + COG (MinIO)', 'Decodifica GeoTIFF no cliente', 'MID', 'Mover raster para COG/MinIO + TiTiler; visualizador passa a consumir tiles (já desenha XYZ).'],
    ['Valor do pixel via /point', 'HUD de valor sob o cursor', 'MID', 'Trocar leitura local pelo endpoint /point do TiTiler.'],
    ['Vetores via MVT (PostGIS)', 'GeoJSON/KML/SHP no cliente', 'MID', 'Endpoint MVT no FastAPI; MapLibre renderiza MVT nativamente.'],
    ['Catálogo STAC / busca CQL2', 'Config manual de modelos', 'NO', 'Integrar stac-fastapi/pgSTAC; TOC vira navegação STAC.'],
    ['Segurança JWT gov.br + roles', 'Sem autenticação', 'NO', 'Gateway valida JWT; vetor filtrado por role; raster por URL assinada.'],
    ['Time-slider temporal', 'Animação + série temporal', 'OK', 'Reaproveitar; ligar ao eixo temporal do STAC.'],
    ['Comparação por swipe', 'Multipainel lado a lado (1-4)', 'MID', 'Adicionar cortina/swipe (multipainel já cobre boa parte).'],
    ['Painel de IA Explicável (XAI)', '—', 'NO', 'Novo painel que consome artefatos XAI (privilégio VIEW_XAI).'],
    ['Identificação de feições (clique)', 'Popup de atributos', 'OK', 'Já implementado (misc/monit/pontos).'],
    ['Medição distância/área', 'Régua/área/retângulo/perfil', 'OK', 'Já implementado (Haversine/esférica).'],
    ['Opacidade granular', 'Slider por camada', 'OK', 'Já implementado.'],
    ['Exportação visual PNG/vídeo', 'PNG + vídeo MP4/WebM', 'OK', 'Já implementado.'],
    ['Exportação PDF cartográfico', 'PDF (mapa+legenda+escala+norte)', 'OK', 'Implementado na v2.13 (era lacuna no doc base).'],
    ['Spatial bookmarks', 'Visões salvas (viewport/camadas)', 'OK', 'Implementado na v2.13 (era lacuna no doc base).'],
    ['Filtros espaciais on-the-fly', 'Recorte por polígono no export', 'MID', 'Estender para filtro de exibição.'],
], widths=[4.6*cm, 4.0*cm, 2.1*cm, 6.3*cm]))
story.append(Paragraph(
    '<b>Atualizações desde o doc base (02/06):</b> a <b>exportação PDF</b> e os <b>spatial bookmarks</b> '
    'deixaram de ser lacunas — passaram a <b>Atende</b>. A v2.14 acrescentou ferramentas de análise '
    '(<b>perfil vertical, perfil temporal, corte vertical 3D e Skew-T log-P com CAPE/CINE</b>) que, '
    'embora não exigidas pela spec, reforçam a maturidade de interface do Card 1 — ativo a preservar. '
    'O esforço do Card 1 concentra-se na <b>troca do motor de dados</b> (TiTiler/MVT/STAC) e na '
    '<b>segurança</b>, não nas ferramentas de usuário.', styles['Tip']))

story.append(PageBreak())
story.append(h2('Card 2 — Editor Vetorial ("QGIS leve") &nbsp; ' + counts(0, 2, 7)))
story.append(status_table([
    ['Desenho de geometrias (vértices, split, merge)', 'Desenho polígono/linha + polígonos do usuário', 'MID', 'UI de desenho reusável; falta split/merge no servidor.'],
    ['Transação RESTful (só da geometria)', 'Tudo em memória/localStorage', 'NO', 'API REST FastAPI + PostGIS.'],
    ['Reprojeção ST_Transform no servidor', 'Render preserva origem (cliente)', 'NO', 'Reprojetar 3857 -> CRS canônico no FastAPI.'],
    ['Snapping via /vertices-near', '—', 'NO', 'Endpoint + UI de snap.'],
    ['Formulário de atributos validado', 'Formulário de atributos (pontos)', 'MID', 'Reaproveitar; validar contra schema do servidor.'],
    ['Lock otimista + lock espacial Redis', '—', 'NO', 'Versão por linha + lock em Redis.'],
    ['Validação topológica (ST_IsValid)', '—', 'NO', 'No PostGIS.'],
    ['Auditoria (camadas_history, diff JSON)', '—', 'NO', 'Tabelas temporais + trilho jwt.sub/timestamp/delta.'],
    ['Permissão can_edit revalidada no servidor', '—', 'NO', 'No PUT/DELETE.'],
], widths=[4.8*cm, 4.0*cm, 2.1*cm, 6.1*cm]))

story.append(h2('Card 3 — Gerador de Painéis e Iframes &nbsp; ' + counts(0, 2, 4)))
story.append(status_table([
    ['URL assinada (JWT: bbox/layers/exp/jti)', 'Export de arquivo (GeoJSON/PNG)', 'NO', 'Tokenização + mini-visualizador embarcável.'],
    ['Blocklist Redis (revoked:jti) + kill switch', '—', 'NO', 'Revogação na borda + dashboard.'],
    ['Cache HTTP/CDN por (jti,z,x,y)', 'Cache de tiles/blobs no cliente', 'MID', 'Mover cache para a borda/CDN.'],
    ['Seletor bbox + layers + TTL + white-list', 'Seleção de área (export)', 'MID', 'UI de empacotamento.'],
    ['Marca d’água dinâmica (canvas + /preview)', '—', 'NO', 'Overlay + watermark no TiTiler.'],
    ['Verificação de Origin/domains', '—', 'NO', 'No bundle e no gateway.'],
], widths=[4.8*cm, 4.0*cm, 2.1*cm, 6.1*cm]))

story.append(PageBreak())
story.append(h2('Card 4 — Portal de Importação e Aprovação &nbsp; ' + counts(0, 3, 5)))
story.append(status_table([
    ['Upload resiliente (TUS/tusd)', 'Lê de FTP/arquivo local', 'NO', 'Serviço TUS -> bucket de quarentena.'],
    ['Fluxo assíncrono (Celery/Redis)', 'Helper Python síncrono', 'NO', 'Fila Celery.'],
    ['Conversão GDAL -> COG (/vsis3)', 'Decodifica no cliente', 'NO', 'Workers GDAL.'],
    ['Quarentena -> publicação sem mover bytes (STAC)', '—', 'NO', 'Prefixos /quarantine /published + transação atômica.'],
    ['Two-person rule (autor + aprovador)', '—', 'NO', 'Fila de aprovação + audit_logs.'],
    ['Anti-duplicação (BBox GIST + SHA-256)', '—', 'NO', 'Índice + verificação.'],
    ['Extração .zip em container descartável', 'Leitor ZIP no cliente (shapefile)', 'MID', 'Mover para sandbox Docker no servidor.'],
    ['Resultados de IA como GeoJSON (XAI)', 'Importa GeoJSON local', 'MID', 'Mesma esteira, sem conversão COG.'],
], widths=[4.8*cm, 4.0*cm, 2.1*cm, 6.1*cm]))

story.append(h2('Eixos transversais (comuns aos 4 módulos)'))
story.append(status_table([
    ['Back-end FastAPI gateway', 'Só helper opcional de amostragem', 'NO', 'Construir o gateway/serviço único.'],
    ['Armazenamento MinIO/COG + PostGIS', 'Arquivos/FTP + memória', 'NO', 'Provisionar MinIO e PostGIS; migrar dados.'],
    ['Entrega de tiles TiTiler/MVT', 'Canvas próprio', 'NO', 'Adotar TiTiler + endpoint MVT.'],
    ['Catálogo STAC/pgSTAC', 'Config manual', 'NO', 'Adotar pgSTAC.'],
    ['Segurança JWT gov.br + URLs assinadas', 'Inexistente', 'NO', 'Integrar Login Único + assinatura.'],
    ['Redis + Celery', 'Inexistente', 'NO', 'Provisionar.'],
    ['CRS sem reprojeção destrutiva', 'Preserva origem no render', 'MID', 'Alinhado no display; falta ST_Transform na escrita.'],
    ['Governança/auditoria/two-person/Meta 1', 'Inexistente', 'NO', 'Trilhas de auditoria + políticas desde a Fase 1.'],
], widths=[4.8*cm, 4.0*cm, 2.1*cm, 6.1*cm]))

story.append(PageBreak())
story.append(h1('4. O que já está pronto × o que falta'))
story.append(h2('Ativos do GISELE a preservar (Card 1)'))
story.append(bullets([
    'Ferramentas de medição (distância Haversine, área esférica, perfil de linha).',
    'Identificação de feições por clique (popup de atributos).',
    'Controles de opacidade, paleta e contornos por camada.',
    'Animação temporal e série temporal num ponto (base para o time-slider STAC).',
    'Exportação de imagem (PNG), vídeo (MP4/WebM) e <b>PDF cartográfico</b>.',
    'Multipainel 1-4 (base para o swipe) e <b>spatial bookmarks</b>.',
    'Análise termodinâmica/vertical (v2.14): perfil vertical, perfil temporal, corte vertical 3D e <b>Skew-T log-P com CAPE/CINE</b>.',
    'Parsers próprios (GeoTIFF/KML/Shapefile) e conectores de fontes (CPTEC/INPE/aviationweather).',
]))
story.append(h2('Lacunas a construir (greenfield de servidor)'))
story.append(bullets([
    '<b>Backbone:</b> gateway FastAPI, PostGIS, MinIO (COG), Redis, Celery.',
    '<b>Entrega de dados:</b> TiTiler (raster), endpoint MVT (vetor), catálogo STAC/pgSTAC.',
    '<b>Segurança:</b> JWT gov.br, filtros por role, URLs assinadas com TTL, blocklist/kill switch.',
    '<b>Card 2:</b> API REST de geometria, ST_Transform, snapping, locks, validação topológica, auditoria.',
    '<b>Card 3:</b> tokenização de recortes, mini-visualizador embarcável, marca d’água, verificação de Origin.',
    '<b>Card 4:</b> upload TUS, quarentena, conversão GDAL->COG, two-person rule, anti-duplicação.',
    '<b>Governança:</b> cadeia de custódia auditável e Meta 1 do MPSP — embutida desde a Fase 1.',
]))

story.append(PageBreak())
story.append(h1('5. Decisão estratégica e roteiro faseado'))
story.append(h2('Bifurcação do Card 1'))
story.append(bullets([
    '<b>(A)</b> GISELE como front-end mantendo o canvas próprio, consumindo TiTiler/MVT/STAC atrás do gateway JWT. Reusa ~100% das ferramentas; mais rápido para um piloto; risco de divergir da spec (que pede MapLibre).',
    '<b>(B)</b> Reescrever o Card 1 em React + MapLibre, portando a UX do GISELE. Aderência total; MVT/WebGL/swipe nativos; mais caro.',
    '<b>(C) Híbrido (recomendado):</b> começar por (A) para validar o back-end com um front existente e migrar para (B) quando estável.',
]))
story.append(h2('Fases'))
story.append(status_table([
    ['Fase 0 — Decisões e fundação', 'Caminho do Card 1, CRS canônico, roles, contrato do JWT, volumetria.', 'NO', 'Pré-requisito de tudo.'],
    ['Fase 1 — Backbone', 'PostGIS, MinIO, Redis, FastAPI gateway, Celery + esqueleto de auth.', 'NO', 'Governança embutida desde aqui.'],
    ['Fase 2 — Entrega de dados', 'TiTiler sobre COG, endpoint MVT, STAC/pgSTAC; piloto de rasters CPTEC -> COG.', 'NO', ''],
    ['Fase 3 — Segurança/assinatura', 'URLs assinadas, filtros por role, blocklist revoked:jti, Origin.', 'NO', ''],
    ['Fase 4 — Card 1 (adaptar GISELE)', 'Consumir tiles/MVT/STAC; manter ferramentas; + swipe/bookmarks/PDF/XAI.', 'MID', 'Parte das ferramentas já existe.'],
    ['Fase 5 — Card 2 (Editor Vetorial)', 'REST de geometria, ST_Transform, snap, locks, topologia, histórico.', 'NO', 'Reusar UI de desenho.'],
    ['Fase 6 — Card 4 (Importação)', 'TUS, Celery+GDAL->COG, publicação atômica, two-person, anti-duplicação.', 'NO', ''],
    ['Fase 7 — Card 3 (Iframes)', 'Empacotador de recorte, mini-visualizador, marca d’água, kill switch.', 'NO', ''],
    ['Fase 8 — Governança/compliance', 'Cadeia de custódia, auditoria dupla, Meta 1, pentest de URLs/revogação.', 'NO', 'Transversal.'],
], widths=[4.4*cm, 7.2*cm, 2.1*cm, 3.3*cm]))

story.append(PageBreak())
story.append(h1('6. Riscos, decisões em aberto e síntese'))
story.append(bullets([
    '<b>Canvas próprio × MapLibre:</b> maior risco de retrabalho — decidir cedo (caminho A/B/C).',
    '<b>Volumetria de raster:</b> define custo de TiTiler/MinIO e estratégia de COG/overviews.',
    '<b>JWT gov.br (Login Único):</b> integração e homologação específicas.',
    '<b>Rigor probatório do MPSP</b> (cadeia de custódia, two-person, auditoria): requisito transversal — não pode ser adicionado "depois".',
    '<b>GISELE client-side puro não atende</b> sozinho multiusuário, segurança por role e auditoria: só com o back-end.',
]))
story.append(p(
    '<b>Síntese.</b> A adequação não é uma refatoração do GISELE: é a <b>construção da plataforma de '
    'servidor COPERNICUS</b> (FastAPI/PostGIS/MinIO/TiTiler/STAC/JWT/Redis/Celery), com o GISELE — ou '
    'sua UX — assumindo o papel do <b>Visualizador (Card 1)</b>, onde já é forte. O caminho de menor '
    'risco é o <b>híbrido (C)</b>: desriscar o back-end com o front existente e migrar para '
    'React+MapLibre quando estável, construindo os Cards 2, 3 e 4 como serviços novos sobre o mesmo '
    'backbone, com governança/auditoria embutidas desde o início.'
))
story.append(hr())
story.append(p('Documento de status gerado a partir de ADEQUACAO_COPERNICUS.md, atualizado ao estado do GISELE v2.14.0.', 'Item'))

doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
print('PDF gerado:', OUT, '| fonte do quadrado:', SQ_FONT or 'fallback')
