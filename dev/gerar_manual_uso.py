#!/usr/bin/env python3
"""
Gera o PDF MANUAL DE USO do SisMOM Visualizador.

Cobre instalação, abas PNG/GIF e GeoTIFF, configuração de modelos,
painel direito, calculadora, servidor HTTP local, atalhos, troubleshooting.

Saída: docs/GISELE_Manual_Uso.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from pathlib import Path
from datetime import date

OUT = Path('/sessions/optimistic-relaxed-davinci/mnt/Visualizador/docs/GISELE_Manual_Uso.pdf')
OUT.parent.mkdir(parents=True, exist_ok=True)

# ─── Paleta de cores ─────────────────────────────────────────────────
NAVY      = colors.HexColor('#0b1e3a')
CYAN      = colors.HexColor('#0a6e8a')
GRAY_D    = colors.HexColor('#384858')
GRAY_M    = colors.HexColor('#6a7c8e')
GRAY_L    = colors.HexColor('#e6ecf2')
GRAY_BG   = colors.HexColor('#f6f9fc')
ACCENT    = colors.HexColor('#1a8b5e')
WARN      = colors.HexColor('#a05500')

# ─── Estilos ─────────────────────────────────────────────────────────
styles = getSampleStyleSheet()
S = lambda name, **kw: styles.add(ParagraphStyle(name=name, **kw))
S('CoverTitle',    parent=styles['Title'],   fontSize=30, leading=36, alignment=TA_CENTER, textColor=NAVY,  spaceAfter=8)
S('CoverSubtitle', parent=styles['Title'],   fontSize=16, leading=22, alignment=TA_CENTER, textColor=GRAY_D, spaceAfter=4)
S('CoverMeta',     parent=styles['Normal'],  fontSize=11, leading=16, alignment=TA_CENTER, textColor=GRAY_M)
S('H1',  parent=styles['Heading1'], fontSize=18, leading=22, textColor=NAVY,   spaceBefore=18, spaceAfter=10)
S('H2',  parent=styles['Heading2'], fontSize=14, leading=18, textColor=CYAN,   spaceBefore=12, spaceAfter=6)
S('H3',  parent=styles['Heading3'], fontSize=12, leading=16, textColor=GRAY_D, spaceBefore=8,  spaceAfter=4)
S('Body',      parent=styles['BodyText'], fontSize=10.5, leading=15, alignment=TA_JUSTIFY, spaceAfter=8)
S('BodyTight', parent=styles['BodyText'], fontSize=10.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=4)
S('Item',      parent=styles['BodyText'], fontSize=10.5, leading=14, spaceAfter=3)
S('CodeBlk',   parent=styles['Code'],     fontSize=9,    leading=12, fontName='Courier', textColor=NAVY,
  leftIndent=10, spaceAfter=8, backColor=GRAY_BG, borderPadding=4)
S('Caption',   parent=styles['BodyText'], fontSize=9,    leading=12, textColor=GRAY_M, alignment=TA_CENTER, spaceAfter=10)
S('Tip',       parent=styles['BodyText'], fontSize=10,   leading=14, leftIndent=14, rightIndent=10, spaceAfter=8, textColor=GRAY_D, backColor=GRAY_BG, borderPadding=6, borderColor=CYAN)
S('Warn',      parent=styles['BodyText'], fontSize=10,   leading=14, leftIndent=14, rightIndent=10, spaceAfter=8, textColor=WARN,    backColor=colors.HexColor('#fff8ee'), borderPadding=6, borderColor=WARN)
S('FooterStyle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=GRAY_M, alignment=TA_CENTER)

def p(txt, style='Body'): return Paragraph(txt, styles[style])
def h1(t): return p(t, 'H1')
def h2(t): return p(t, 'H2')
def h3(t): return p(t, 'H3')
def hr(): return HRFlowable(width='100%', thickness=0.6, color=GRAY_L, spaceBefore=4, spaceAfter=8)
def code(txt):
    safe = txt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
    return Paragraph('<font face="Courier">' + safe + '</font>', styles['CodeBlk'])
def tip(txt):  return Paragraph('<b>Dica.</b> ' + txt, styles['Tip'])
def warn(txt): return Paragraph('<b>Atenção.</b> ' + txt, styles['Warn'])
def bullets(items, style='Item'):
    return ListFlowable(
        [ListItem(Paragraph(it, styles[style]), leftIndent=10, value='•') for it in items],
        bulletType='bullet', leftIndent=14, bulletFontSize=10, spaceAfter=8
    )
def numbered(items, style='Item'):
    return ListFlowable(
        [ListItem(Paragraph(it, styles[style]), leftIndent=10) for it in items],
        bulletType='1', leftIndent=14, bulletFontSize=10, spaceAfter=8
    )
def tbl(data, col_widths=None, header=True):
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    s = [
        ('FONTNAME',    (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,0), (-1,-1), 9),
        ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING',(0,0), (-1,-1), 5),
        ('GRID',        (0,0), (-1,-1), 0.3, GRAY_L),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, GRAY_BG]),
    ]
    if header:
        s += [('BACKGROUND', (0,0), (-1,0), NAVY),
              ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
              ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold')]
    t.setStyle(TableStyle(s))
    return t

# ─── Documento ────────────────────────────────────────────────────────
def _draw_footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GRAY_M)
    canvas.drawCentredString(A4[0]/2, 1.2*cm, f"GISELE - Manual de Uso | pagina {doc_.page}")
    canvas.restoreState()

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title='GISELE - Manual de Uso',
    author='CPTEC/INPE'
)

# ─── Conteúdo ────────────────────────────────────────────────────────
story = []

# ===== CAPA =====
story += [
    Spacer(1, 5*cm),
    p('GISELE', 'CoverTitle'),
    p('Gestão Integrada de Soluções Estratégicas e Inteligência<br/>Manual de Uso', 'CoverSubtitle'),
    Spacer(1, 1.2*cm),
    p('Sistema Multiusuário de Detecção, Previsão e Monitoramento de Derrame de Óleo no Mar (SisMOM)<br/>CPTEC · INPE · MCTI', 'CoverMeta'),
    Spacer(1, 0.6*cm),
    p('CPTEC / INPE', 'CoverMeta'),
    Spacer(1, 4*cm),
    p('Versão 2.0.0 — build 20260528-0500-gisele', 'CoverMeta'),
    p(f'Atualizado em {date.today().strftime("%d/%m/%Y")}', 'CoverMeta'),
]
story.append(PageBreak())

# ===== SUMÁRIO =====
story.append(h1('Sumário'))
sumario = [
    '1. O que é o GISELE',
    '2. Instalação e primeira execução',
    '3. Visão geral da interface',
    '4. Aba PNG/GIF — uso básico',
    '5. Aba GeoTIFF — visualização científica',
    '6. Painel direito — árvore ERMA-style',
    '7. Configurando modelos e variáveis',
    '8. Templates de URL e placeholders',
    '9. Camadas e calculadora tripla (algébrica + per-layer + temporal)',
    '10. Ferramentas de medição e perfil',
    '11. Camadas Miscelâneas (referência geográfica)',
    '12. Exportar dados como GeoJSON (v2.6+)',
    '13. Servidor HTTP local de dados',
    '14. Atalhos de teclado',
    '15. Solução de problemas',
]
story.append(bullets(sumario))
story.append(PageBreak())

# ===== 1. O QUE É =====
story.append(h1('1. O que é o GISELE'))
story.append(p(
    'O GISELE é uma plataforma de visualização de modelos meteorológicos '
    'operacionais do CPTEC/INPE. Permite navegar passos de previsão (animação), comparar '
    'múltiplos modelos lado a lado, e analisar campos científicos em formato GeoTIFF — '
    'tudo em uma única janela, sem instalação de softwares de SIG pesados.'
))
story.append(h2('Capacidades principais'))
story.append(bullets([
    '<b>Visualização PNG/GIF:</b> imagens prontas do FTP do CPTEC, com animação de passos e layouts de 1 a 4 painéis.',
    '<b>Visualização GeoTIFF:</b> decodifica TIFs (LZW, Deflate, PackBits; float32/int16/uint8), aplica paleta de cores configurável, sobrepõe mapa-base com tiles satélite ou OSM.',
    '<b>Calculadora de camadas:</b> operações entre rasters (A op B ou A op escalar).',
    '<b>Configuração flexível:</b> usuário define modelos próprios via templates de URL com placeholders.',
    '<b>Cache inteligente:</b> animação acelera após a primeira passagem (decoded + imageData + blob URL em LRU caches).',
    '<b>Multi-plataforma:</b> Windows (instalador NSIS e portátil), Linux (AppImage, .deb), navegador (HTML standalone).',
]))
story.append(h2('Dois "modos" de visualização'))
story.append(p('Há duas abas no topo da janela:'))
story.append(tbl([
    ['Aba', 'Para que serve', 'Quando usar'],
    ['PNG/GIF', 'Mostra imagens já renderizadas pelo CPTEC (PNGs ou GIFs animados).', 'Inspeção rápida, navegação de várias variáveis lado a lado, observação operacional.'],
    ['GeoTIFF', 'Decodifica os arquivos GeoTIFF e renderiza com paleta + min/max ajustáveis, opcionalmente sobre mapa-base (tiles).', 'Análise quantitativa, comparação numérica, exportação de figuras customizadas.'],
], col_widths=[2.5*cm, 6.5*cm, 7*cm]))
story.append(PageBreak())

# ===== 2. INSTALAÇÃO =====
story.append(h1('2. Instalação e primeira execução'))
story.append(p('O GISELE é distribuído em três sistemas operacionais. Escolha o pacote correspondente à sua máquina.'))
story.append(h2('Windows — Instalador (.exe)'))
story.append(numbered([
    'Execute <b>GISELE Setup 2.0.0.exe</b>.',
    'O SmartScreen pode mostrar "Editor desconhecido". Clique em <i>Mais informações</i> &rarr; <i>Executar mesmo assim</i>.',
    'Escolha a pasta de instalação (ou aceite o padrão).',
    'Marque "Criar atalho na Área de Trabalho" se desejar.',
    'Conclua. O app abre automaticamente.',
]))
story.append(h2('Windows — Versão portátil (sem instalação)'))
story.append(p(
    'Use <b>GISELE-2.0.0-portable.exe</b>. Roda direto do pen drive ou de qualquer pasta — não instala nada, '
    'não toca no registro. Útil para testar antes de instalar ou para uso pontual.'
))

story.append(h2('macOS — Instalador (.dmg)'))
story.append(p('O GISELE é distribuído como <b>.dmg</b> para Intel (x64) e Apple Silicon (arm64 — M1/M2/M3). Use o arquivo correspondente ao seu Mac:'))
story.append(bullets([
    '<b>Apple Silicon (M1/M2/M3/M4):</b> <code>GISELE-2.0.0-arm64.dmg</code>',
    '<b>Intel Mac:</b> <code>GISELE-2.0.0-x64.dmg</code>',
    '<b>Em dúvida:</b> Menu Apple &rarr; Sobre Este Mac &rarr; veja "Chip".',
]))
story.append(numbered([
    'Duplo-clique no <b>.dmg</b> baixado para montar.',
    'Arraste o ícone do <b>GISELE</b> para a pasta <b>Applications</b>.',
    'Eject (ejetar) a imagem do .dmg da Área de Trabalho.',
    'Abra a pasta Aplicativos e duplo-clique no <b>GISELE</b>.',
    'Primeira abertura: o Gatekeeper pode bloquear ("não foi possível verificar o desenvolvedor"). Clique com botão direito (ou Ctrl+clique) no app &rarr; <b>Abrir</b> &rarr; confirme. Só uma vez.',
]))
story.append(warn(
    'O app não é notarizado pela Apple (Developer ID + notarização exige conta paga). '
    'Por isso o Gatekeeper avisa na primeira abertura. Após autorizar uma vez, abre normalmente.'
))
story.append(h2('macOS — .zip alternativo'))
story.append(p('Se preferir, use o <code>.zip</code> equivalente (mesmo binário, sem o instalador DMG):'))
story.append(bullets([
    '<code>GISELE-2.0.0-mac-arm64.zip</code> ou <code>GISELE-2.0.0-mac-x64.zip</code>',
    'Descompacte (duplo-clique). Mova <code>GISELE.app</code> para Applications.',
]))

story.append(h2('Linux'))
story.append(bullets([
    '<b>AppImage:</b> <code>chmod +x GISELE-2.0.0.AppImage &amp;&amp; ./GISELE-2.0.0.AppImage</code>. Pode exigir <code>sudo apt install libfuse2</code>.',
    '<b>.deb:</b> <code>sudo apt install ./gisele_2.0.0_amd64.deb</code> em Debian/Ubuntu.',
    '<b>Outros:</b> use o AppImage (roda em qualquer distro com glibc moderna).',
]))

story.append(h2('HTML standalone (qualquer SO, no navegador)'))
story.append(p(
    'Na pasta <b>GISELE-2.0.0-standalone/</b> (também distribuída como .zip), '
    'abra <b>figuras_SisMOM_v23.html</b> no navegador. Windows: duplo-clique em <b>SisMOM.bat</b> para janela de aplicativo. '
    'Linux/macOS: <code>./SisMOM.sh</code>.'
))
story.append(warn(
    'Limitação: em navegador via <code>file://</code>, o GeoTIFF pode falhar por CORS. Use a versão Electron para uso pleno, '
    'ou rode o servidor HTTP local (seção 10) e configure URLs <code>http://localhost:8765/...</code> nos templates.'
))

story.append(h2('Inicialização avançada — multi-monitor (Windows)'))
story.append(p(
    'O GISELE.exe (instalador ou portátil) aceita opções de linha de comando para abrir a janela cobrindo '
    'múltiplos monitores. Útil em videowalls, salas de operação ou estações com 2–8 telas.'
))
story.append(h3('Flags disponíveis'))
story.append(tbl([
    ['Flag', 'Efeito'],
    ['--displays=1,2,5,6', 'Abre a janela cobrindo exatamente os monitores listados (1-indexed, ordem física: cima→baixo, esquerda→direita).'],
    ['--all-displays', 'Cobre TODOS os monitores conectados.'],
    ['--no-frame', 'Remove a borda/barra de título (modo "kiosk", visual limpo para multi-monitor).'],
], col_widths=[5*cm, 11*cm]))
story.append(h3('Exemplos'))
story.append(p('Servidor com 8 monitores (2 linhas × 4 colunas), abrir cobrindo o quadrante superior-esquerdo:'))
story.append(code(
    '"C:\\Program Files\\GISELE\\GISELE.exe" --displays=1,2,5,6'
))
story.append(p('Cobrindo todos os 8 monitores em modo kiosk:'))
story.append(code(
    '"C:\\Program Files\\GISELE\\GISELE.exe" --all-displays --no-frame'
))
story.append(h3('Criando um atalho com a flag'))
story.append(numbered([
    'Botão direito na Área de Trabalho → <b>Novo → Atalho</b>.',
    'No "Local do item" cole: <code>"C:\\Program Files\\GISELE\\GISELE.exe" --displays=1,2,5,6</code>',
    'Próximo. Nomeie como "GISELE multi-monitor". Concluir.',
    'Pronto: duplo-clique abre o app cobrindo os 4 monitores.',
]))
story.append(tip(
    'A numeração dos monitores segue a ordenação física (top→bottom, left→right) detectada via <code>screen.getAllDisplays()</code>. '
    'Geralmente coincide com a numeração em <i>Configurações → Sistema → Tela</i> do Windows. '
    'Se a ordem estiver diferente do esperado, abra <code>%APPDATA%\\GISELE\\launch.log</code> — o log mostra todos os displays detectados com posição (x, y) e dimensões.'
))
story.append(h3('Atalhos de teclado dentro do app multi-monitor'))
story.append(tbl([
    ['Tecla', 'Ação'],
    ['F11', 'Alterna entre tela cheia e janela normal.'],
    ['Ctrl + Q', 'Fechar o app (essencial quando rodando com --no-frame).'],
    ['Alt + F4', 'Fechar (padrão Windows; também funciona).'],
], col_widths=[4*cm, 12*cm]))
story.append(h3('Diagnóstico'))
story.append(p(
    'A cada inicialização, o app grava um log de diagnóstico em '
    '<code>%APPDATA%\\GISELE\\launch.log</code>. O log contém: versões Electron/Chromium, todos os args recebidos '
    '(<code>process.argv</code>), todos os displays detectados, o retângulo combinado calculado, e o resultado '
    'de cada chamada <code>setBounds</code>. Útil para suporte técnico se a janela não cobrir os monitores esperados.'
))
story.append(PageBreak())

# ===== 3. VISÃO GERAL =====
story.append(h1('3. Visão geral da interface'))
story.append(p('A janela do app está dividida em quatro regiões:'))
story.append(tbl([
    ['Região', 'Conteúdo'],
    ['Cabeçalho (topo)', 'Logo, abas PNG/GIF e GeoTIFF, ícones: configurar (engrenagem), tema claro/escuro, ajuda, abrir GeoTIFF local.'],
    ['Barra lateral esquerda', 'Layout de mapas (1/2/3/4), controles de animação (Play, Stop, velocidade), tabela de passos de tempo, data da rodada do Mapa 1.'],
    ['Área central', 'Painéis Mi (M1, M2, M3, M4) com cabeçalho próprio (modelo, data, variável) e barra de zoom inferior. Cada painel mostra uma imagem ou GeoTIFF renderizado.'],
    ['Painel direito (sidebar)', 'Visível apenas em modo GeoTIFF: paleta, escala (min/max), NoData/Clip, lista de camadas, calculadora. Controla o painel Mi ativo.'],
], col_widths=[4.5*cm, 11.5*cm]))
story.append(h2('Tema claro / escuro'))
story.append(p('Clique no ícone de Sol/Lua no cabeçalho para alternar. A escolha persiste entre sessões.'))
story.append(PageBreak())

# ===== 4. ABA PNG/GIF =====
story.append(h1('4. Aba PNG/GIF — uso básico'))
story.append(p(
    'É a aba padrão ao abrir o app. Cada painel Mi mostra uma imagem PNG (ou GIF animado) baixada do FTP do CPTEC. '
    'O cabeçalho do painel tem três seletores:'
))
story.append(bullets([
    '<b>Modelo:</b> qual produto (Eta 3km, BESM T062, MOM6 Global, etc).',
    '<b>Data:</b> data e hora da rodada do modelo. O Mapa 1 sempre inicia na data corrente; demais painéis cascateiam.',
    '<b>Variável:</b> campo a visualizar (temperatura, precipitação, vento, etc.).',
]))
story.append(h2('Sincronização entre painéis'))
story.append(p(
    'O botão de elo (🔗) no cabeçalho dos painéis 2–4 sincroniza a data deles com o Mapa 1: ao mudar a rodada do M1, '
    'os outros acompanham. Desligue para ajustar datas independentes.'
))
story.append(h2('Animação'))
story.append(numbered([
    'Selecione o passo inicial na tabela de Passos de Tempo (à esquerda).',
    'Ajuste a velocidade (0.25s a 3s por frame).',
    'Clique em <b>Animar</b>. Use <b>Pausar</b> ou <b>Stop</b> para parar.',
    'Setas do teclado: ←/→ avançam/recuam um passo.',
]))
story.append(tip(
    'A primeira passagem da animação carrega cada passo do servidor (pode ser lento em modelos pesados como Eta). '
    'Após uma volta completa, os passos ficam em cache local e a 2ª volta fica instantânea.'
))
story.append(h2('Salvar vídeo da evolução temporal (MP4)'))
story.append(p(
    'Logo abaixo do seletor de velocidade existe o botão <b>Salvar vídeo (MP4)</b>. Disponível nas duas abas '
    '(PNG/GIF e GeoTIFF). Ao clicar:'
))
story.append(numbered([
    '<b>Fase 1 — Pré-busca:</b> a ferramenta varre todos os passos da rodada, monta as URLs via o template do modelo, e baixa as imagens em paralelo (popup mostra "Pré-buscando: X/Y").',
    '<b>Fase 2 — Gravação:</b> reproduz cada passo no canvas off-screen por ~400 ms, capturando via <code>MediaRecorder</code> a 30 fps em <code>video/mp4</code> (ou <code>video/webm</code> em browsers sem suporte ao MP4).',
    'Ao terminar, o arquivo <code>evolucao_&lt;modelo&gt;_&lt;variavel&gt;_&lt;timestamp&gt;.mp4</code> é baixado automaticamente.',
]))
story.append(bullets([
    'A região visível (zoom/pan) é preservada — o vídeo grava exatamente o crop que está na tela.',
    'A passagem é <b>uma única vez</b>, do primeiro passo ao último — sem looping circular como na animação normal.',
    'Layouts multi-painel (M1+M2+…) são gravados juntos no mesmo vídeo, com cada painel em sua posição.',
]))
story.append(tip(
    'Em variáveis com horizonte muito longo (ex.: Global PREC 720 h = 30 passos diários), a pré-busca pode demorar alguns segundos. '
    'O popup tem botão <b>Cancelar</b> que aborta a gravação e descarta o vídeo parcial.'
))
story.append(h2('Layouts'))
story.append(p('A coluna esquerda tem 4 botões de layout: 1, 2, 3 ou 4 painéis. O layout escolhido persiste entre sessões.'))
story.append(PageBreak())

# ===== 5. ABA GEOTIFF =====
story.append(h1('5. Aba GeoTIFF — visualização científica'))
story.append(p(
    'Clique na aba <b>GeoTIFF</b> no cabeçalho. A interface ganha duas mudanças:'
))
story.append(bullets([
    'Os painéis Mi continuam visíveis, mas agora cada um decodifica o GeoTIFF correspondente ao modelo/variável/data/passo selecionado.',
    'Aparece o <b>painel direito</b> (sidebar de 340px à direita) com todos os controles científicos.',
]))
story.append(h2('Selecionando o painel ativo'))
story.append(p(
    'Cada painel Mi tem um pequeno botão "<b>Painel M1</b>" (ou M2, M3, M4) no canto superior esquerdo da área de mapa. '
    'Clique para tornar esse painel o <b>ativo</b>. Borda ciano indica o painel selecionado, e o painel direito passa a operar sobre ele.'
))
story.append(h2('Mostrar mapa-base'))
story.append(numbered([
    'Espere o painel ativo terminar de carregar o TIF (a barra de cores aparece no painel direito).',
    'No painel direito, marque <b>"Mostrar mapa"</b>.',
    'Escolha o provedor de tiles: Satélite (Esri), Ruas (OSM), Topo (OpenTopoMap) ou Sem tiles.',
    'Use o slider de <b>Opacidade</b> para ajustar a transparência do raster sobre o mapa.',
]))
story.append(tip(
    'A configuração de mapa é POR painel. Você pode ter M1 com Satélite, M2 com OSM e M3 sem mapa. Cada um lembra sua configuração ao trocar o painel ativo.'
))
story.append(h2('Valor sob o cursor'))
story.append(p(
    'Passe o mouse sobre o mapa — na barra inferior aparece a latitude, longitude e o valor numérico do raster naquele ponto. '
    'Útil para conferir extremos ou comparar regiões.'
))
story.append(h2('Animação no modo GeoTIFF'))
story.append(p(
    'Funciona igual ao PNG/GIF, mas cada passo precisa fetch + decode + aplicação de paleta. A primeira passagem é mais lenta '
    '(decodificação custa centenas de ms para grids grandes); a segunda passagem é instantânea graças ao cache.'
))
story.append(PageBreak())

# ===== 6. PAINEL DIREITO =====
story.append(h1('6. Painel direito — árvore ERMA-style (v2.4+)'))
story.append(p(
    'A partir da versão 2.4 o painel direito foi reorganizado em uma <b>árvore estilo ERMA</b>, com quatro '
    'grupos colapsáveis que organizam todos os controles do painel Mi ativo. Tudo o que você ajusta afeta '
    'APENAS o painel Mi ativo.'
))
story.append(h2('Estrutura geral'))
story.append(p('Os quatro grupos da árvore são, de cima para baixo:'))
story.append(tbl([
    ['Grupo', 'Conteúdo'],
    ['📦 Background',
     'Tile provider do mapa-base do slot ativo: <i>Nenhum</i>, <i>Esri World Imagery</i> (satélite), '
     '<i>OpenStreetMap</i> e <i>OpenTopoMap</i>, escolhidos via <b>radios mutuamente exclusivos</b>. A seleção '
     'sincroniza com a checkbox "Mostrar mapa".'],
    ['🐠 Miscelânea',
     'Checkboxes para adicionar/remover camadas vetoriais pré-empacotadas (Plataformas offshore, Corais '
     'brasileiros, etc.). Marcar = adiciona a camada no slot; desmarcar = remove. A cor pode ser ajustada no '
     'chip da camada (ver seção 11).'],
    ['🗺️ Camadas',
     'Lista de camadas ativas no slot — primary (GeoTIFF do modelo) + extras (TIF, GeoJSON, resultado da '
     'calculadora). Cada nó tem ícones de cor, visibilidade (👁), remover (×) e — para rasters — um '
     'sub-menu <b>Configuração da Camada</b> (▸) que se expande inline.'],
    ['🛠️ Ferramentas',
     'Sub-nós para: <b>Adicionar GeoTIFF/GeoJSON</b>, <b>Adicionar Modelo</b> (formulário inline com '
     'modelo/variável/data), e <b>Calculadora</b> (expressão entre camadas).'],
], col_widths=[3.5*cm, 12.4*cm]))

story.append(h2('Botão Collapse folders / Expand folders'))
story.append(p(
    'No topo do painel há um botão que <b>recolhe ou expande todos os quatro grupos de uma vez</b>. Útil '
    'quando você tem várias camadas + Ferramentas abertas e quer voltar a uma visão limpa rapidamente. O '
    'rótulo alterna conforme o estado (todos abertos = "Collapse folders", todos fechados = "Expand folders").'
))

story.append(h2('Sub-menu "Configuração da Camada" (por nó)'))
story.append(p(
    'Cada camada raster (primary ou extra) tem um sub-menu <b>Configuração da Camada</b> que se abre '
    '<b>inline dentro do nó da camada</b>, em layout vertical, com os controles que antes ficavam soltos '
    'na sidebar:'
))
story.append(bullets([
    '<b>Paleta:</b> 15 paletas (Sequenciais: Viridis, Plasma, Inferno, Magma, Cividis, Jet, Turbo, Cinza; '
    'Divergentes: RdBu, RdYlBu, Spectral, BrBG, Seismic, Coolwarm; Topográficas: Terrain, Ocean).',
    '<b>Min / Max + Editar/Auto:</b> escala automática (percentil 5–95%) ou fixa.',
    '<b>UNDEF + Clip ≥/≤:</b> sentinels e thresholds de mascaramento.',
    '<b>Contornos:</b> liga/desliga marching squares, intervalo entre isolinhas, espessura, '
    'preservar shaded (<i>keepFill</i> default ON).',
    '<b>Calculadora per-layer:</b> linha "🧮 Calc: camada [op] [escalar] [Aplicar]" — aplica '
    '<code>op</code> (+, −, ×, ÷) entre a camada atual e um escalar. Resultado vira nova camada extra.',
]))
story.append(tip(
    'O painel de configuração é fisicamente <b>um único elemento DOM</b> (<code>#gtLayerConfigPanel</code>) '
    'movido por <code>appendChild</code> entre os nós conforme você expande/contrai. Listeners são '
    'preservados. Apenas <b>um sub-menu de configuração</b> fica aberto por vez — abrir outro fecha o '
    'anterior automaticamente.'
))
story.append(warn(
    'A versão anterior do manual descrevia um painel persistente de "Arquivo / Visual" na sidebar. <b>Essa '
    'área foi removida</b> — todos os controles de paleta/min-max/clip/contornos ficam agora <b>somente</b> '
    'dentro do sub-menu Configuração da Camada de cada nó.'
))

story.append(h2('Grupo Ferramentas — sub-nós'))
story.append(bullets([
    '<b>Adicionar GeoTIFF/GeoJSON:</b> botão que abre seletor de arquivo do disco; a camada entra como '
    'extra no slot.',
    '<b>Adicionar Modelo:</b> formulário inline (movido fisicamente para dentro do nó por '
    '<code>appendChild</code>) com seletores de modelo/variável/data/passo. Útil para empilhar uma '
    'previsão alternativa sobre a camada base sem trocar o modelo do slot.',
    '<b>Calculadora (expressão entre camadas):</b> tokens clicáveis Camada1..N + textarea para expressão '
    'algébrica (ex.: <code>Camada1 * 1000 + Camada2</code>) + botão Calcular. Avalia pixel a pixel '
    'propagando máscara NoData. Veja seção 9 para detalhes.',
]))
story.append(PageBreak())

# ===== 7. CONFIGURAR MODELOS =====
story.append(h1('7. Configurando modelos e variáveis'))
story.append(p(
    'Clique no ícone de <b>engrenagem</b> no cabeçalho para abrir o modal "Configurar modelos e variáveis". '
    'Por padrão está em modo <b>somente leitura</b>; clique em <b>Editar</b> (canto superior direito) para habilitar alterações.'
))
story.append(h2('Abas de modelo'))
story.append(p(
    'Cada modelo é uma aba. Acima das abas há ações:'
))
story.append(tbl([
    ['Botão', 'O que faz'],
    ['+ Novo modelo', 'Cria modelo do zero, com nome e templates genéricos.'],
    ['Clonar modelo', 'Duplica a aba atual (com variáveis e templates) como novo modelo "(cópia)" — útil para criar variantes.'],
    ['Remover modelo', 'Apaga o modelo da aba atual (deve restar pelo menos um).'],
    ['Restaurar padrão', 'Volta ao conjunto de modelos de fábrica (descarta personalização).'],
    ['Exportar / Importar', 'Salva/restaura toda a configuração (modelos + painéis) em arquivo .json.'],
], col_widths=[4*cm, 12*cm]))
story.append(h2('Campos por modelo'))
story.append(bullets([
    '<b>Escopo 1 / Escopo 2:</b> tokens que viram <code>{escopo1}</code> e <code>{escopo2}</code> nos templates (úteis para nível, componente, etc.).',
    '<b>Sufixo do arquivo:</b> extensão padrão (.png, .gif, .jpg, etc.).',
    '<b>Máx. Passos:</b> horizonte máximo da rodada em horas.',
    '<b>Template do endereço (PNG/GIF):</b> caminho até a pasta dos arquivos PNG/GIF, com placeholders de data.',
    '<b>Template Nome Arq. (PNG/GIF):</b> nome do arquivo, com placeholders de prefixo/passo/extensão.',
    '<b>Formatos disponíveis no FTP:</b> marque PNG/GIF e/ou GeoTIFF (.tif). Modelos sem TIF são automaticamente filtrados da aba GeoTIFF.',
    '<b>Templates TIF:</b> se marcar GeoTIFF, configure rota e nome próprios — ou marque "usar o mesmo do PNG" para reaproveitar.',
    '<b>Mapa-base padrão (GeoTIFF):</b> escolha qual tile provider entra automaticamente quando o modelo é carregado na aba GeoTIFF — opções <i>Nenhum</i>, <i>Esri World Imagery</i> (satélite), <i>OpenStreetMap</i> ou <i>OpenTopoMap</i> (relevo). Ao trocar de modelo no painel, o mapa-base é reaplicado; se você mudar manualmente o select da sidebar direita, sua escolha vale enquanto o modelo continuar o mesmo.',
]))
story.append(h2('Tabela de variáveis'))
story.append(p(
    'Cada linha é uma variável. Colunas: ID, Nome longo, Unidade, Frequência em horas, Horizonte máximo, Prefixo de arquivo, '
    'e checkboxes <b>PNG</b> e <b>TIF</b> indicando em quais formatos a variável está disponível. '
    'Variáveis sem TIF não aparecem no seletor da aba GeoTIFF.'
))
story.append(h2('Atalho: Preset FTP CPTEC'))
story.append(p(
    'Logo abaixo dos templates TIF existe o botão <b>Preset FTP CPTEC (PNG /fig/ → TIF /geotiff/)</b>. '
    'Ele preenche automaticamente os campos seguindo a convenção do FTP do CPTEC:'
))
story.append(bullets([
    'Marca <b>PNG/GIF</b> e <b>GeoTIFF</b> como disponíveis.',
    'Desmarca "usar o mesmo do PNG" para que o TIF tenha rota dedicada.',
    'Deriva o template de URL TIF substituindo <code>/fig/</code> por <code>/geotiff/</code> no template PNG existente.',
    'Define o nome do arquivo TIF como <code>{prefixo}-{F%4}.tif</code> (padrão do CPTEC).',
]))
story.append(tip(
    'Útil ao criar/clonar um novo modelo do CPTEC: preencha primeiro o template PNG, clique no preset, e o TIF fica pronto.'
))
story.append(h2('Trabalhar com .tif locais (sem FTP)'))
story.append(p(
    'Para inspecionar um GeoTIFF do disco, existem dois caminhos:'
))
story.append(bullets([
    '<b>Inspeção rápida:</b> no header, clique no ícone "Abrir GeoTIFF" para abrir o modal. Escolha o arquivo, '
    'selecione paleta e ajuste min/max — útil para validar um TIF sem envolvê-lo na configuração de modelo.',
    '<b>Como camada extra no painel ativo:</b> no painel direito (aba GeoTIFF), bloco <b>Camadas extras</b>, '
    'clique em <b>+ Adicionar GeoTIFF/GeoJSON…</b> e selecione o arquivo. Ele entra na lista de camadas como '
    'sobreposição ao primary do painel, com paleta/opacidade/contornos configuráveis individualmente.',
]))
story.append(p(
    'Em ambos os casos o decoder próprio do GISELE aceita TIFF baseline em qualquer dos formatos:'
))
story.append(tbl([
    ['Bits/sample', 'Sample format', 'Suportado'],
    ['8',   'UINT',     'Sim (imagem RGB ou grayscale)'],
    ['16',  'UINT/INT', 'Sim'],
    ['32',  'FLOAT',    'Sim (uso típico — saída de modelos)'],
    ['64',  'FLOAT',    'Sim'],
], col_widths=[3*cm, 4*cm, 9*cm]))
story.append(p(
    'Tags GeoTIFF reconhecidas: <code>ModelPixelScale (33550)</code>, <code>ModelTiepoint (33922)</code>, '
    '<code>GeoKeyDirectory (34735)</code>. Suporta <code>GTRasterTypeGeoKey</code> para distinguir pixel-is-point vs pixel-is-area '
    '(o GISELE ajusta o bbox automaticamente). NoData detectado via heurística de sentinels (range >1e6) com fallback por percentil 1/99.'
))
story.append(PageBreak())

# ===== 8. TEMPLATES DE URL =====
story.append(h1('8. Templates de URL e placeholders'))
story.append(p(
    'Os templates combinam texto literal com <b>placeholders</b> entre chaves. O app substitui antes de fazer <code>fetch</code>.'
))
story.append(h2('Endereço — placeholders de data da rodada'))
story.append(p('No CAMPO <i>Template do endereço</i>, os placeholders representam a data da rodada do modelo:'))
story.append(tbl([
    ['Placeholder', 'Significado', 'Exemplo'],
    ['{yyyy}', 'ano com 4 dígitos', '2026'],
    ['{mm}', 'mês com 2 dígitos', '05'],
    ['{dd}', 'dia com 2 dígitos', '27'],
    ['{hh}', 'hora UTC com 2 dígitos', '00'],
    ['{yyyymmddhh}', 'concatenação completa', '2026052700'],
    ['{escopo1}', 'tokens 1/2 do modelo', 'atmos'],
    ['{escopo2}', '', 'superficie'],
], col_widths=[4*cm, 6*cm, 5*cm]))
story.append(p('<b>Exemplo:</b>'))
story.append(code('https://ftp1.cptec.inpe.br/modelos/tempo/Eta3km/{yyyy}/{mm}/{dd}/{hh}/fig/'))
story.append(h2('Nome do arquivo — placeholders de previsão'))
story.append(p('No CAMPO <i>Template Nome Arq.</i>, a data refere-se à VALIDADE da previsão (rodada + horas):'))
story.append(tbl([
    ['Placeholder', 'Significado'],
    ['{prefixo}', 'prefixo do arquivo (vem da variável)'],
    ['{N} ou {N%3}', 'índice da figura (1, 2, 3...). %3 = padded a 3 dígitos (001).'],
    ['{F} ou {F%3}', 'horas de previsão (= índice × freq). %3 = 3 dígitos (012).'],
    ['{fct} ou {f%3}', 'idem F mas prefixado com "f" (ex: f024).'],
    ['{ext}', 'extensão (.png, .tif, etc.)'],
    ['{yyyy}, {mm}, {dd}, {hh}', 'data de validade (rodada + F horas).'],
], col_widths=[4*cm, 11*cm]))
story.append(p('<b>Exemplos:</b>'))
story.append(code(
    '{prefixo}-{F%3}{ext}            &rarr; prec-024.png<br/>'
    '{prefixo}{f%3}{ext}             &rarr; precf024.png<br/>'
    '{prefixo}-{yyyymmddhh}{ext}     &rarr; prec-2026052800.png'
))
story.append(tip(
    'A diferença entre N e F: para uma variável com Freq=3h, N=8 e F=24h (figura 8 = passo 24h). N é o número da imagem na sequência; F é a hora de previsão.'
))
story.append(PageBreak())

# ===== 9. CALCULADORA =====
story.append(h1('9. Camadas e calculadora dupla'))
story.append(h2('Adicionando camadas via árvore'))
story.append(p(
    'No grupo <b>🛠️ Ferramentas</b> da árvore, sub-nó '
    '<b>+ Adicionar GeoTIFF / GeoJSON / Shapefile…</b>, escolha um ou mais arquivos do disco. Cada arquivo vira uma '
    'camada nova dentro de <b>🗺️ Camadas</b>, sobreposta à camada base.'
))
story.append(p('Formatos aceitos (v2.6+):'))
story.append(bullets([
    '<b>.tif / .tiff</b> — GeoTIFF como camada raster (paleta + min/max + contornos).',
    '<b>.geojson / .json</b> — GeoJSON inteiro como camada vetorial.',
    '<b>.shp</b> — Shapefile standalone (só geometria, sem .dbf/.shx). Parser puro JS embarcado: Polygon, '
    'PolygonZ, PolygonM, detecção automática de outer/hole pela orientação dos anéis.',
    '<b>.zip</b> — ZIP contendo .shp (e opcionalmente .dbf/.shx/.prj ignorados). O .shp é extraído '
    'automaticamente via <code>DecompressionStream(\'deflate-raw\')</code> nativo do browser.',
]))
story.append(p('Cada nó de camada oferece:'))
story.append(bullets([
    '<b>👁 / ⊘</b> botão grande para <b>ligar/desligar</b> a camada. Cor cyan quando ligada, cinza quando desligada. '
    'A linha inteira fica com opacidade 50&#37; quando off.',
    '<b>×</b> remove a camada do slot.',
    '<b>▸ Configuração da Camada</b> (apenas para rasters) expande o sub-menu inline com paleta, '
    'min/max, contornos e calculadoras (algébrica + temporal).',
    'Para GeoJSONs/Shapefiles, um seletor de <b>cor</b> inline troca o estilo de stroke/fill em tempo real.',
]))
story.append(h2('Calculadora — duas modalidades'))
story.append(p(
    'A partir da v2.4 a calculadora aparece em <b>dois lugares</b> com semânticas diferentes:'
))

story.append(h2('A) Ferramentas → Calculadora (expressão entre camadas)'))
story.append(p(
    'No grupo <b>🛠️ Ferramentas</b>, sub-nó <b>🧮 Calculadora (expressão entre camadas)</b>. Use para '
    'composições que envolvem <b>múltiplas camadas</b> e operações algébricas livres.'
))
story.append(numbered([
    'Expanda o sub-nó. Aparece a lista de tokens clicáveis (Camada1, Camada2, ...) que correspondem às '
    'camadas atualmente no slot.',
    'Clique nos tokens para inseri-los no textarea, ou digite manualmente.',
    'Escreva a expressão usando: identificadores <code>Camada<i>N</i></code>, números (decimais com '
    '<code>.</code>), operadores <code>+ − * /</code>, e parênteses.',
    'Clique em <b>Calcular</b>. Uma nova camada extra é adicionada com o nome da expressão.',
]))
story.append(p('<b>Exemplos:</b>'))
story.append(code(
    'Camada1 * 1000<br/>'
    '(Camada1 + Camada2) / 2<br/>'
    'Camada1 - Camada2<br/>'
    'Camada3 * 0.01 + 273.15'
))
story.append(tip(
    'O parser é um <b>recursive-descent</b> próprio, sem <code>eval</code> nem <code>Function()</code>. '
    'Aceita apenas números, identificadores, parênteses e os quatro operadores básicos. Qualquer outro '
    'token gera erro.'
))

story.append(h2('B) Configuração da Camada → Calc per-layer (operador + escalar)'))
story.append(p(
    'No sub-menu <b>Configuração da Camada</b> de qualquer raster, há uma linha:'
))
story.append(code('🧮 Calc: camada  [+ / − / × / ÷ ]  [escalar]  [Aplicar]'))
story.append(p(
    'Use para aplicar uma <b>operação simples sobre uma camada só</b> — caso comum: conversão de unidade '
    '(multiplicar precipitação por 1000, somar 273.15 para Kelvin, etc.).'
))
story.append(numbered([
    'Abra <b>Configuração da Camada</b> no nó da camada-alvo (a camada que será operada).',
    'Escolha o operador no select (<code>+</code>, <code>−</code>, <code>×</code>, <code>÷</code>).',
    'Digite o escalar no input.',
    'Clique em <b>Aplicar</b>. Uma nova camada é adicionada ao slot — a camada original permanece intacta.',
]))
story.append(tip(
    'Internamente esta variante reusa o mesmo engine <code>gtCreateLayerFromExpression</code> da '
    'modalidade A, montando a expressão equivalente (ex.: <code>Camada2 * 1000</code>). Os pixels '
    'mascarados (NoData) são propagados normalmente.'
))

story.append(h2('C) Configuração da Camada → Calculadora Temporal (v2.6+)'))
story.append(p(
    'Na linha <b>⏱ Tempos</b> dentro de Configuração da Camada, expressões algébricas combinam '
    '<b>passos diferentes da mesma rodada</b> da camada-fonte (mesmo modelo + variável + data, varia apenas '
    'o passo). Útil para acumulados, médias, diferenças temporais, etc.'
))
story.append(p('<b>Sintaxe aceita:</b>'))
story.append(bullets([
    '<b>tN</b> — índice do passo (<code>t1</code>, <code>t2</code>, <code>t24</code>…). O índice multiplicado pela frequência da variável dá o horizonte em horas.',
    '<b>hN</b> — horas de previsão (<code>h6</code>, <code>h12</code>, <code>h72</code>…) — convertido para o índice mais próximo via <code>round(N/freq)</code>.',
    '<b>..</b> — range, <b>apenas dentro de funções</b> (<code>t1..t24</code>, <code>h6..h72</code>).',
    'Funções de redução: <b>sum, mean</b> (ou <code>avg</code>/<code>media</code>), <b>max, min, count</b>.',
    'Operadores <code>+ − × ÷</code>, parênteses, e escalares para conversão de unidade.',
]))
story.append(p('<b>Exemplos:</b>'))
story.append(code(
    'sum(t1..t24)              # precipitação acumulada nas primeiras 24 previsões<br/>'
    't24 - t1                  # diferença entre dois passos<br/>'
    'mean(h6..h72)             # média dos passos de 6h a 72h<br/>'
    'sum(t1..t10) * 1000       # acumulado × conversão de unidade<br/>'
    'max(t1..t72) - min(t1..t72)  # range térmico ao longo do horizonte'
))
story.append(p('<b>Comportamento da execução:</b>'))
story.append(numbered([
    'Parser coleta todos os <code>tN</code>/<code>hN</code> únicos requisitados (expandindo ranges).',
    'Valida que cada índice está dentro de <code>horizonte/frequência</code> da variável.',
    'Modal de progresso "Processando tN (passo +Xh)… i/N" + botão <b>Cancelar</b>.',
    'Fetch + decode sequencial via o mesmo pipeline da Série Temporal (cache de TIFs reutilizado).',
    'Avaliação per-pixel propagando máscara NoData: qualquer valor mascarado em qualquer operando '
    'resulta em pixel mascarado no resultado.',
    'Camada resultante é adicionada com paleta padrão e min/max automático.',
]))
story.append(tip(
    'Casos comuns: precipitação acumulada 24h <code>sum(t1..t24)</code>; média de 5 dias <code>mean(t1..t120)</code> '
    'em dado horário <code>h120/freq=24 → t5</code>; diferença pré/pós-evento <code>t72 - t24</code>. '
    'Para variáveis sem grade temporal (análise/observação freq=0), a calculadora alerta e não plota.'
))
story.append(PageBreak())

# ===== 10. FERRAMENTAS =====
story.append(h1('10. Ferramentas de medição e perfil'))
story.append(p(
    'Cada painel Mi (na aba GeoTIFF) tem uma barra de ferramentas no topo do mapa. As ferramentas operam '
    'em coordenadas geográficas reais (latitude/longitude) — os valores reportados são corrigidos para a '
    'curvatura da Terra usando a fórmula de Haversine.'
))
story.append(h2('Como ativar uma ferramenta'))
story.append(numbered([
    'Clique no ícone da ferramenta na barra do mapa (ela fica destacada).',
    'Clique no mapa para inserir vértices. Mover o mouse mostra o desenho em pré-visualização.',
    'Duplo-clique (ou Enter) finaliza a medição/desenho. Esc cancela.',
    'Pra voltar ao modo de navegação (pan), clique no ícone da mãozinha.',
]))
story.append(h2('Ferramentas disponíveis'))
story.append(tbl([
    ['Ícone', 'Ferramenta', 'O que mede / faz'],
    ['📏', 'Distância',     'Soma do comprimento dos segmentos da linha (Haversine, em km).'],
    ['▦',  'Área',          'Área do polígono fechado pelos cliques (km², esférica).'],
    ['▭',  'Retângulo',     'Caixa lat/lon definida por dois cliques diagonais; reporta a área.'],
    ['◯',  'Círculo',       'Raio definido a partir do centro; reporta raio em km e área em km².'],
    ['╱',  'Linha',         'Polilinha simples (anotação visual).'],
    ['T',  'Texto',          'Rótulo no mapa numa posição clicada.'],
    ['∿',  'Perfil',        'Amostra a camada ativa ao longo da polilinha e abre um gráfico.'],
    ['⏱', 'Série temporal', 'Clique único em um ponto — varre todos os passos do slot e abre gráfico tempo×valor.'],
], col_widths=[1.2*cm, 3.2*cm, 11.5*cm]))
story.append(h2('Ferramenta de perfil'))
story.append(p(
    'O perfil amostra valores do raster ativo (a camada destacada no painel direito) ao longo de uma '
    'polilinha. Após finalizar, abre uma janela com:'
))
story.append(bullets([
    'Gráfico de fundo branco, responsivo à largura da janela.',
    'Eixo X: distância acumulada em km desde o primeiro ponto. Eixo Y: valor do raster.',
    'Tooltip ao passar o mouse — mostra lat/lon, distância e valor exato do ponto.',
    'Botão <b>Salvar PNG</b> — exporta o gráfico em imagem para colar em relatórios.',
]))
story.append(tip(
    'O perfil sempre usa a <b>camada ativa</b>. Se quiser perfil de outra camada, clique no chip dela primeiro '
    'pra torná-la ativa, depois ative a ferramenta de perfil.'
))
story.append(h2('Série temporal num ponto'))
story.append(p(
    'Ativa pelo ícone do relógio. Clique <b>uma vez</b> em qualquer ponto do mapa. A ferramenta volta '
    'automaticamente para o modo Pan e abre uma janela "Série temporal" mostrando o progresso da '
    'amostragem (passo i/N).'
))
story.append(p(
    'Internamente, para cada passo da rodada (de <code>frequencia</code> até <code>horizonte</code>) a ferramenta '
    'constrói a URL do TIF via o mesmo pipeline da animação, baixa, decodifica e amostra o valor em '
    '(lat, lon). Quando termina, abre um gráfico com:'
))
story.append(bullets([
    'Eixo X: data/hora UTC da validade (rodada + N×Freq).',
    'Eixo Y: valor do raster na coordenada.',
    'Pontos azuis nos passos válidos (sem NoData).',
    'Tooltip ao passar o mouse — data, "+Nh da rodada", valor exato.',
    'Botão <b>Baixar CSV</b> (colunas: índice, passo_h, time_utc, lat, lon, valor).',
    'Botão <b>Salvar PNG</b> do gráfico.',
]))
story.append(tip(
    'Variáveis de análise/observação (frequência = 0) não têm grade temporal — a ferramenta alerta e não plota.'
))
story.append(h2('Zoom com a roda do mouse durante uso de ferramentas'))
story.append(p(
    'O zoom via scroll fica habilitado mesmo com uma ferramenta ativa — você pode ajustar a região antes '
    'do próximo clique. Pan (arrastar) também funciona; só os cliques são consumidos pela ferramenta.'
))
story.append(PageBreak())

# ===== 11. MISCELÂNEAS =====
story.append(h1('11. Camadas Miscelâneas (referência geográfica)'))
story.append(p(
    'O bloco <b>Miscelâneas</b> no painel direito permite adicionar camadas vetoriais de referência geográfica '
    'sobre os mapas — pontos (ex: plataformas de petróleo) ou polígonos (ex: áreas de coral). São camadas '
    'pré-empacotadas que vêm dentro da pasta <code>miscelaneas/</code> ao lado do HTML do GISELE.'
))
story.append(h2('Camadas inclusas no pacote'))
story.append(tbl([
    ['Camada', 'Tipo', 'Conteúdo'],
    ['Plataformas offshore (Brasil)', 'Pontos rotulados',
     'Plataformas de prospecção/produção de petróleo em águas brasileiras, com sigla visível no mapa e '
     'informações de operadora, bacia, campo, status, classificação do óleo e histórico de derramamentos.'],
    ['Corais (costa brasileira)', 'Polígonos',
     'Recifes coralinos ao longo da costa brasileira (Maranhão, Pernambuco/Alagoas, Sergipe/Bahia, '
     'Banco dos Abrolhos, Banco de Vitória/Trindade). Fonte: UNEP-WCMC Global distribution of warm-water '
     'coral reefs (2018), recortado para o bbox brasileiro.'],
], col_widths=[5*cm, 3*cm, 8*cm]))
story.append(h2('Adicionando uma camada (árvore ERMA v2.4+)'))
story.append(numbered([
    'Na árvore ERMA do painel direito, expanda o grupo <b>🐠 Miscelânea</b>.',
    'Marque o <b>checkbox</b> ao lado do item desejado (Plataformas offshore, Corais brasileiros, etc.). '
    'A camada é imediatamente adicionada ao slot — desmarcando, ela é removida.',
    'A camada também aparece como nó dentro do grupo <b>🗺️ Camadas</b>, com ícone de cor, olho (👁) para '
    'ocultar/mostrar e × para remover.',
    'A cor pode ser alterada inline no chip da camada (seletor de cor nativo do sistema).',
]))
story.append(h2('Estilização — hachura nos polígonos'))
story.append(p(
    'Polígonos da camada de corais são preenchidos com um padrão de hachura diagonal (linhas finas em '
    '~45°) sobre um fundo translúcido. Isso permite ver o campo do GeoTIFF por trás sem perder a indicação '
    'visual da região coralina. A hachura usa <code>CanvasPattern</code> com cache local — não impacta '
    'performance de pan/zoom.'
))
story.append(h2('Trocar a cor da camada'))
story.append(p(
    'Cada chip de camada Miscelânea tem um pequeno seletor de cor (input nativo do sistema). '
    'Clique nele para escolher uma nova cor:'
))
story.append(bullets([
    'O <b>stroke</b> (contorno) muda para a cor escolhida.',
    'O <b>fill</b> translúcido é recolor’d preservando o alpha original (ex: 18% de opacidade nos corais).',
    'A <b>hachura</b> e a cor dos <b>pontos</b> também adotam a nova cor.',
    'A mudança é instantânea — o mapa redesenha sem recarregar o arquivo.',
]))
story.append(h2('Clique no shape — janela de informação'))
story.append(p(
    'Em modo de navegação (mão aberta), clique em qualquer ponto ou polígono de uma camada Miscelânea. '
    'Uma janela branca abre no canto superior direito mostrando uma tabela com os atributos relevantes do shape '
    '(definidos em <code>infoProps</code> no manifest):'
))
story.append(bullets([
    'Plataformas: nome, operadora, bacia, campo, status, ano de início, classificação do óleo, histórico de derramamentos.',
    'Corais: nome regional (ex: "Banco dos Abrolhos / Sul da Bahia"), região, área em km², gênero/espécie/família taxonômica quando disponíveis.',
]))
story.append(tip(
    'Para polígonos a detecção é por <i>point-in-polygon</i> exato (incluindo respeito a buracos). Para pontos '
    'a tolerância é de ~10 pixels, então não precisa clicar com precisão milimétrica.'
))
story.append(h2('Adicionando suas próprias miscelâneas'))
story.append(p(
    'A pasta <code>miscelaneas/</code> contém um <code>manifest.json</code> que lista todas as camadas. '
    'Você pode adicionar suas próprias camadas GeoJSON editando esse manifest:'
))
story.append(code(
    '{\n'
    '  "version": 1,\n'
    '  "items": [\n'
    '    {\n'
    '      "id": "minha_camada",\n'
    '      "nome": "Minha camada (descrição)",\n'
    '      "arquivo": "meu_geojson.geojson",\n'
    '      "tipo": "geojson",\n'
    '      "labelProp": "nome",          // propriedade pro rótulo dos pontos\n'
    '      "infoProps": ["nome","x","y"],// propriedades mostradas no popup de info\n'
    '      "style": {\n'
    '        "stroke": "#ff7a00",        // cor do contorno\n'
    '        "fill": "rgba(255,122,0,0.20)", // fill translúcido (polígonos)\n'
    '        "fillColor": "#ff7a00",     // cor sólida dos pontos\n'
    '        "pointRadius": 5,            // raio do círculo dos pontos\n'
    '        "lineWidth": 1.2,            // espessura do stroke\n'
    '        "hatch": true,               // ativa hachura diagonal\n'
    '        "hatchColor": "#0aa37a",\n'
    '        "hatchSpacing": 7,\n'
    '        "hatchLineWidth": 1\n'
    '      }\n'
    '    }\n'
    '  ]\n'
    '}'
))
story.append(warn(
    'Para que funcione abrindo o HTML diretamente do disco (<code>file://</code>), o manifest e os GeoJSONs '
    'precisam estar embutidos no HTML como <code>&lt;script type="application/json" id="gt-misc-..."&gt;</code>. '
    'No GISELE empacotado isso já está feito; se você modificar o manifest manualmente, sirva pelo servidor '
    'HTTP local (seção 12) para que o <i>fetch</i> funcione.'
))
story.append(PageBreak())

# ===== 12. EXPORTAR GEOJSON =====
story.append(h1('12. Exportar dados como GeoJSON (v2.6+)'))
story.append(p(
    'No grupo <b>🛠️ Ferramentas</b> da árvore, o sub-nó <b>📤 Exportar GeoJSON</b> permite salvar a '
    '<b>camada ativa</b> como nuvem de pontos GeoJSON (uma <code>Feature</code> de tipo <code>Point</code> por pixel '
    'com <code>properties.value</code>). É possível recortar o raster por área desenhada ou por uma camada '
    'vetorial já carregada.'
))
story.append(h2('Opções de recorte'))
story.append(tbl([
    ['Botão', 'Comportamento'],
    ['🌐 Campo cheio (sem recorte)', 'Exporta todos os pixels do bbox da camada ativa.'],
    ['▦ Polígono (desenhar)',
     'Ativa modo de desenho — clique para vértices, duplo-clique finaliza e exporta. '
     'O polígono em construção aparece em amarelo translúcido.'],
    ['▭ Retângulo (clicar e arrastar)',
     'Clique e arraste para definir a caixa lat/lon. Soltar finaliza e exporta.'],
    ['🗂️ Por camada carregada (vetorial)',
     'Abre diálogo listando todas as camadas <i>geojson</i> no slot — Miscelâneas, Shapefiles importados '
     'e GeoJSONs adicionados. Cada item mostra a cor da camada, o nome, e <code>[Origem, N features]</code>. '
     'Selecione as máscaras com checkbox e clique Exportar.'],
    ['⏱ Clique no mapa para exportar evolução temporal',
     'Ativa modo de clique único. Após você clicar num ponto, a ferramenta varre todos os passos do slot '
     '(igual à série temporal), e salva o resultado como FeatureCollection com N Features Point (mesmas '
     'coords, 1 por passo) com <code>properties = { idx, passo_h, time_utc, value }</code>.'],
], col_widths=[5.2*cm, 11*cm]))
story.append(h2('Preview + confirmação (upload/camada vetorial)'))
story.append(p(
    'Quando a máscara vem de upload ou de uma camada vetorial já carregada, o GISELE primeiro '
    '<b>plota o(s) polígono(s) em ciano</b> sobre o mapa (linha 0,7 px, sem bolinhas) e abre um <b>card de '
    'confirmação</b> ancorado no canto superior direito, fora da área do mapa. Você vê o bbox, contagem '
    'de polígonos, e a área plotada para conferência antes da extração. <i>Enter</i> confirma, <i>Esc</i> '
    'cancela. Polígonos desenhados manualmente (▦/▭) não passam por essa confirmação — o desenho é o '
    'próprio feedback.'
))
story.append(h2('Formato de saída'))
story.append(p('Nuvem de pontos no padrão GeoJSON (RFC 7946):'))
story.append(code(
    '{<br/>'
    '  "type": "FeatureCollection",<br/>'
    '  "bbox": [west, south, east, north],<br/>'
    '  "metadata": {<br/>'
    '    "generator": "GISELE",<br/>'
    '    "layer": "Eta · prec",<br/>'
    '    "bbox": { "minX": ..., "minY": ..., "maxX": ..., "maxY": ... },<br/>'
    '    "gridSize": [W, H],<br/>'
    '    "exported": 12345,<br/>'
    '    "skippedNoData": 678,<br/>'
    '    "skippedOutsideMask": 9012,<br/>'
    '    "exportedAt": "2026-05-29T..."<br/>'
    '  },<br/>'
    '  "features": [<br/>'
    '    { "type": "Feature",<br/>'
    '      "geometry": { "type": "Point", "coordinates": [lon, lat] },<br/>'
    '      "properties": { "value": 12.345 } }<br/>'
    '  ]<br/>'
    '}'
))
story.append(p('Para a evolução temporal em um ponto, cada feature representa um passo:'))
story.append(code(
    '{ "type": "Feature",<br/>'
    '  "geometry": { "type": "Point", "coordinates": [lon, lat] },<br/>'
    '  "properties": { "idx": 1, "passo_h": 6, "time_utc": "...", "value": 12.345 } }'
))
story.append(h2('Detalhes técnicos'))
story.append(bullets([
    'Point-in-polygon por <b>ray casting</b> com suporte a furos (multi-polygon com holes respeitados).',
    'Bbox da máscara restringe a iteração — rápido em grids globais com máscara local.',
    'NoData filtrado automaticamente (<code>decoded.nodata</code> + <code>nodataExtras</code> + <code>isFinite</code>).',
    'Cap de segurança em <b>500.000 features</b> (avisa no console se atingido — útil pra evitar arquivos gigantes '
    'em campo global).',
    'Convenção top-down: row j=0 corresponde a <code>latMax</code>; centro do pixel: '
    '<code>lat = latMax − (j+0.5) × dLat</code>.',
    'Nome do arquivo automático: <code>gisele_&lt;camada&gt;_&lt;modo&gt;.geojson</code>.',
]))
story.append(tip(
    'Para usar um shapefile como máscara, primeiro carregue-o via <b>+ Adicionar GeoTIFF / GeoJSON / '
    'Shapefile…</b> — ele vira uma camada vetorial visível no mapa. Depois selecione-o em '
    '<b>🗂️ Por camada carregada</b>. O mesmo shape pode ser usado simultaneamente como referência visual '
    'e como máscara de extração.'
))
story.append(PageBreak())

# ===== 13. SERVIDOR LOCAL =====
story.append(h1('13. Servidor HTTP local de dados'))
story.append(p(
    'Os dados podem estar no servidor do CPTEC (URLs <code>https://ftp1.cptec.inpe.br/...</code>) ou na sua máquina local. '
    'Para usar dados locais — especialmente em <b>Safari/Firefox</b> que não permitem acesso direto a disco via <code>file://</code> — '
    'há um pequeno servidor HTTP que vem junto com o app, em <code>tools/servir_dados/</code>.'
))
story.append(p('Funciona em <b>Windows, Linux e macOS</b>. Requer <b>Python 3.6+</b> OU <b>Node.js 14+</b> (qualquer um basta).'))

story.append(h2('Windows'))
story.append(numbered([
    'Abra a pasta <code>tools/servir_dados/</code>.',
    'Arraste a pasta de dados sobre <code>servir_dados.bat</code>.',
    'A janela do terminal abre e fica rodando enquanto você usa o GISELE.',
    'Para parar: <code>Ctrl+C</code> ou fechar a janela.',
]))
story.append(p('<b>CLI alternativo:</b>'))
story.append(code('servir_dados.bat "C:\\dados\\meteorologia" 8765'))

story.append(h2('Linux (Ubuntu / Debian / Fedora / outros)'))
story.append(p('<b>1. Garanta o Python 3 (geralmente já vem instalado):</b>'))
story.append(code(
    'python3 --version       # deve mostrar 3.x<br/>'
    '# Se não tiver:<br/>'
    'sudo apt install python3        # Ubuntu/Debian<br/>'
    'sudo dnf install python3        # Fedora<br/>'
    'sudo pacman -S python           # Arch'
))
story.append(p('<b>2. Dê permissão de execução ao script (uma vez só):</b>'))
story.append(code('chmod +x /caminho/para/tools/servir_dados/servir_dados.sh'))
story.append(p('<b>3. Inicie o servidor apontando para a pasta dos dados:</b>'))
story.append(code(
    'cd /caminho/para/tools/servir_dados<br/>'
    './servir_dados.sh /home/usuario/dados/meteorologia<br/>'
    '# ou com porta customizada:<br/>'
    './servir_dados.sh /home/usuario/dados/meteorologia 9000'
))
story.append(p('Saída esperada:'))
story.append(code(
    '==============================================================<br/>'
    ' GISELE — Servidor local de dados<br/>'
    '==============================================================<br/>'
    ' Diretório:  /home/usuario/dados/meteorologia<br/>'
    ' URL base:   http://localhost:8765/<br/>'
    ' CORS:       habilitado para qualquer origem'
))
story.append(p('<b>4. Verifique no terminal (em outra aba) que está respondendo:</b>'))
story.append(code('curl -I http://localhost:8765/    # deve retornar 200 OK'))
story.append(p('<b>5. Deixe o terminal aberto.</b> Ao fechar, o servidor para. Para parar manualmente: <code>Ctrl+C</code>.'))

story.append(h2('macOS'))
story.append(p('Mesmo procedimento do Linux. Python 3 já vem instalado no macOS recente; se não tiver:'))
story.append(code('brew install python3'))

story.append(h2('Configurando o modelo para usar o servidor local'))
story.append(p('No template do modelo (Configurar > Editar), troque a base do servidor:'))
story.append(code(
    'Antes:  https://ftp1.cptec.inpe.br/modelos/tempo/Eta3km/{yyyy}/{mm}/{dd}/{hh}/fig/<br/>'
    'Depois: http://localhost:8765/Eta3km/{yyyy}/{mm}/{dd}{hh}/'
))
story.append(p(
    'O servidor vem com CORS aberto, MIME corretos (incluindo <code>image/tiff</code>) e protecao contra path-traversal. '
    'Compativel com qualquer browser, inclusive Safari.'
))

story.append(h2('Auto-start no boot — Linux (systemd user service)'))
story.append(p('Para o servidor subir automaticamente no login do usuario:'))
story.append(numbered([
    'Crie o arquivo <code>~/.config/systemd/user/gisele-server.service</code> com o conteudo abaixo (ajuste os caminhos).',
    'Recarregue o systemd: <code>systemctl --user daemon-reload</code>',
    'Habilite e inicie: <code>systemctl --user enable --now gisele-server</code>',
    'Verifique status: <code>systemctl --user status gisele-server</code>',
    'Para parar: <code>systemctl --user stop gisele-server</code>',
]))
story.append(p('<b>Conteudo do arquivo</b> <code>gisele-server.service</code>:'))
story.append(code(
    '[Unit]<br/>'
    'Description=GISELE local data server<br/>'
    'After=network.target<br/>'
    '<br/>'
    '[Service]<br/>'
    'Type=simple<br/>'
    'ExecStart=/caminho/tools/servir_dados/servir_dados.sh /caminho/dados<br/>'
    'Restart=on-failure<br/>'
    'RestartSec=5<br/>'
    '<br/>'
    '[Install]<br/>'
    'WantedBy=default.target'
))
story.append(tip(
    'Para o servico continuar rodando mesmo com usuario deslogado, ative <code>linger</code>: '
    '<code>sudo loginctl enable-linger $USER</code>.'
))

story.append(h2('Auto-start no boot — Windows'))
story.append(numbered([
    'Crie um atalho do <code>servir_dados.bat</code> com a pasta de dados como argumento.',
    'Pressione <code>Win+R</code> e digite <code>shell:startup</code> — a pasta Startup do usuario abre.',
    'Cole o atalho la. O servidor inicia automaticamente em todo login.',
]))
story.append(PageBreak())

# ===== 14. ATALHOS =====
story.append(h1('14. Atalhos de teclado'))
story.append(tbl([
    ['Atalho', 'Acao'],
    ['Espaco',                'Play/Pause da animacao no painel ativo.'],
    ['Direita / Esquerda',    'Proximo / passo anterior na animacao.'],
    ['Shift+seta',            'Pular 5 passos.'],
    ['Home / End',            'Primeiro / ultimo passo.'],
    ['Scroll do mouse',       'Zoom in/out centrado no cursor.'],
    ['Clique e arrastar',     'Pan do mapa.'],
    ['Esc',                   'Cancela a ferramenta ativa e volta para Pan. Tambem cancela dialogos.'],
    ['Enter',                 'Confirma dialogos de exportacao GeoJSON.'],
    ['Duplo-clique',          'Finaliza polilinha/poligono em desenho.'],
    ['Ctrl+F5',               'Recarrega o app forcando bypass de cache.'],
    ['F12',                   'Abre o DevTools (Electron) — util pra ver console e build marker.'],
], col_widths=[3.5*cm, 12.4*cm]))
story.append(PageBreak())

# ===== 15. SOLUCAO DE PROBLEMAS =====
story.append(h1('15. Solucao de problemas'))
story.append(h2('"Falha ao carregar camada: Failed to fetch"'))
story.append(p(
    'Ocorre quando o app tenta buscar um arquivo (GeoJSON da Miscelanea, GeoTIFF do modelo, etc.) e o '
    'protocolo <code>file://</code> bloqueia. Solucoes:'
))
story.append(bullets([
    'Use o GISELE empacotado (Electron) em vez de abrir o HTML direto — ele tem acesso ao disco.',
    'Suba o servidor HTTP local (secao 13) e ajuste a URL do modelo para <code>http://localhost:8765/...</code>.',
]))

story.append(h2('Erro: object is not iterable na exportacao'))
story.append(p(
    'Esse erro ocorria em versoes anteriores ao v2.6 — o engine de exportacao fazia destructuring de array '
    '(<code>const [...] = decoded.bbox</code>) sobre um objeto <code>{minX, minY, maxX, maxY}</code>. Corrigido '
    'na build <code>20260529-4700-bboxfix</code>. Se ainda aparece, force reload (Ctrl+F5).'
))

story.append(h2('Shape importado aparece com bolas grossas no contorno'))
story.append(p(
    'Em versoes <= 2.5 o renderer desenhava circulos de 3px em cada vertice. A partir do v2.6 '
    '(<code>style.noVertices=true</code>) shapes importados sao desenhados como linha fina pura. Se ainda '
    'aparecem bolinhas: force reload e cheque o build marker.'
))

story.append(h2('Cores estranhas / sem dados visiveis'))
story.append(bullets([
    'Verifique a paleta atual e min/max em Configuracao da Camada.',
    'Clique em <b>Auto min/max</b> para recalcular pelos percentis (5–95%).',
    'Adicione valores NoData explicitos em <b>UNDEF</b> se o modelo usa sentinels nao-padrao (ex: 1e20, -9999).',
]))

story.append(h2('GeoJSON exportado tem 500.000 features e foi cortado'))
story.append(p(
    'O exportador tem um cap de seguranca em 500.000 features para evitar arquivos gigantes em campos '
    'globais. Reduza o bbox via recorte (poligono/retangulo/camada vetorial), ou ajuste o cap editando '
    '<code>opts.maxFeatures</code> em <code>gtExportLayerToGeoJsonPointCloud</code>.'
))

story.append(h2('Calculadora Temporal: "tempo fora do horizonte"'))
story.append(p(
    'A expressao tem um <code>tN</code> alem do horizonte da variavel. Maximo permitido: '
    '<code>floor(horizonte / frequencia)</code>. Para verificar, abra Configurar > Editar e veja "Maximo de '
    'passos" do modelo + frequencia da variavel. Exemplo: BESM Global PREC freq=24h e horizonte=720h → '
    'maximo <code>t30</code>.'
))

story.append(h2('Build marker e diagnostico'))
story.append(p(
    'Em qualquer duvida sobre versao, abra o DevTools (F12 no Electron) e veja a primeira linha do console: '
    '<code>[GISELE] build = YYYYMMDD-NNNN-nome</code>. Reporte esse marker ao suporte para acelerar o diagnostico.'
))

story.append(h2('CORS e a flag --strict-cors'))
story.append(p(
    'O GISELE empacotado (Electron) roda com <code>webSecurity: false</code> por padrao para permitir vidеo MP4 '
    'sobre o FTP do CPTEC (que nao envia headers CORS). Para forcar isolamento estrito, passe a flag '
    '<code>--strict-cors</code> ao executavel. O log <code>%APPDATA%/GISELE/launch.log</code> mostra o modo ativo.'
))

# ===== Build do PDF =====
doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
print(f'PDF gerado: {OUT}')
