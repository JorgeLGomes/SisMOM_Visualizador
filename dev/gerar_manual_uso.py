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
    '6. Painel direito — controles do painel ativo',
    '7. Configurando modelos e variáveis',
    '8. Templates de URL e placeholders',
    '9. Camadas extras e calculadora',
    '10. Servidor HTTP local de dados',
    '11. Atalhos de teclado',
    '12. Solução de problemas',
    '13. Apêndice — referência de placeholders',
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
story.append(h1('6. Painel direito — controles do painel ativo'))
story.append(p('O painel direito está dividido em seções colapsáveis. Tudo o que você ajusta afeta APENAS o painel Mi ativo.'))
story.append(h2('Arquivo / Visual'))
story.append(bullets([
    '<b>Paleta:</b> 15 paletas disponíveis, agrupadas em Sequenciais (Viridis, Plasma, Inferno, Magma, Cividis, Jet, Turbo, Cinza), Divergentes (RdBu, RdYlBu, Spectral, BrBG, Seismic, Coolwarm) e Topográficas (Terrain, Ocean).',
    '<b>Min / Max:</b> faixa de valores mapeada na paleta. Em modo "Auto" usa o min/max do dado; clique em <b>Editar escala</b> para fixar manualmente.',
    '<b>Editar / Auto:</b> alterna entre escala manual e automática.',
]))
story.append(h2('NoData / Clip'))
story.append(bullets([
    '<b>UNDEF:</b> lista de valores sentinela tratados como "sem dado" (ex: <code>-999, -9999</code>). Esses pixels ficam transparentes.',
    '<b>Clip ≥:</b> valores menores que esse limite são mascarados.',
    '<b>Clip ≤:</b> valores maiores que esse limite são mascarados.',
    '<b>Limpar:</b> remove todos os filtros.',
]))
story.append(tip(
    'O decoder já detecta automaticamente sentinelas grandes (ex: <code>-3.4e+38</code> do GrADS) e o NoData declarado no header do TIF. '
    'Use UNDEF/Clip para casos onde a detecção automática não pega.'
))
story.append(h2('Camadas'))
story.append(p(
    'A camada base é o GeoTIFF do painel ativo. Você pode adicionar camadas extras (outros TIFs ou GeoJSONs) que ficam sobrepostas. '
    'Cada camada extra tem botões de subir/descer ordem, mostrar/ocultar (👁) e remover. Configurar uma camada como ativa permite editar suas propriedades pelo painel.'
))
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
]))
story.append(h2('Tabela de variáveis'))
story.append(p(
    'Cada linha é uma variável. Colunas: ID, Nome longo, Unidade, Frequência em horas, Horizonte máximo, Prefixo de arquivo, '
    'e checkboxes <b>PNG</b> e <b>TIF</b> indicando em quais formatos a variável está disponível. '
    'Variáveis sem TIF não aparecem no seletor da aba GeoTIFF.'
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
story.append(h1('9. Camadas extras e calculadora'))
story.append(h2('Adicionando camadas'))
story.append(p(
    'Na seção <b>Camadas</b> do painel direito, clique em <b>+ Adicionar GeoTIFF/GeoJSON...</b> e escolha um arquivo do disco. '
    'A camada aparece na lista, sobreposta à camada base.'
))
story.append(bullets([
    '<b>↑ ↓</b> reorganiza a ordem (camadas no topo aparecem na frente).',
    '<b>👁</b> oculta/mostra a camada.',
    '<b>🗑</b> remove.',
    'Clique no chip da camada para torná-la a camada <b>ativa</b> — os controles do painel direito (paleta, min/max) passam a operar sobre ela.',
]))
story.append(h2('Calculadora de raster'))
story.append(p(
    'Permite operações entre camadas (ou entre camada e escalar). Resultado vira uma nova camada.'
))
story.append(numbered([
    'Em <b>Calc</b>, escolha a <b>camada A</b>.',
    'Escolha o <b>operador</b>: + (soma), − (diferença), × (produto), ÷ (razão).',
    'Escolha a <b>camada B</b> (outro raster) <i>ou</i> "(valor escalar)" e digite um número.',
    'Clique em <b>Calcular</b>. Uma nova camada aparece na lista.',
]))
story.append(tip(
    'Os pixels mascarados (NoData) em qualquer dos operandos resultam em pixel mascarado no resultado. '
    'Útil para diferença entre rodadas, razões, ou conversões de unidade.'
))
story.append(PageBreak())

# ===== 10. SERVIDOR LOCAL =====
story.append(h1('10. Servidor HTTP local de dados'))
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
    'O servidor vem com CORS aberto, MIME corretos (incluindo <code>image/tiff</code>) e proteção contra path-traversal. '
    'Compatível com qualquer browser, inclusive Safari.'
))

story.append(h2('Auto-start no boot — Linux (systemd user service)'))
story.append(p('Para o servidor subir automaticamente no login do usuário:'))
story.append(numbered([
    'Crie o arquivo <code>~/.config/systemd/user/gisele-server.service</code> com o conteúdo abaixo (ajuste os caminhos).',
    'Recarregue o systemd: <code>systemctl --user daemon-reload</code>',
    'Habilite e inicie: <code>systemctl --user enable --now gisele-server</code>',
    'Verifique status: <code>systemctl --user status gisele-server</code>',
    'Para parar: <code>systemctl --user stop gisele-server</code>',
]))
story.append(p('<b>Conteúdo do arquivo</b> <code>gisele-server.service</code>:'))
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
    'Para o serviço continuar rodando mesmo com usuário deslogado, ative <code>linger</code>: '
    '<code>sudo loginctl enable-linger $USER</code>.'
))

story.append(h2('Auto-start no boot — Linux (cron alternativo)'))
story.append(p('Mais simples mas sem reinício automático em caso de falha:'))
story.append(code(
    'crontab -e<br/>'
    '# adicione a linha:<br/>'
    '@reboot /caminho/tools/servir_dados/servir_dados.sh /caminho/dados &gt; /tmp/gisele-server.log 2&gt;&amp;1 &amp;'
))

story.append(h2('Auto-start no boot — Windows'))
story.append(numbered([
    'Crie atalho do <code>servir_dados.bat</code> com a pasta como argumento.',
    'Aperte <code>Win+R</code>, digite <code>shell:startup</code>, Enter.',
    'Cole o atalho nessa pasta.',
    'Pronto — no próximo login o servidor sobe sozinho.',
]))

story.append(h2('Auto-start no boot — macOS (launchd)'))
story.append(p('Crie um plist em <code>~/Library/LaunchAgents/br.inpe.gisele.server.plist</code> e carregue com:'))
story.append(code(
    'launchctl load ~/Library/LaunchAgents/br.inpe.gisele.server.plist<br/>'
    'launchctl start br.inpe.gisele.server'
))
story.append(p('Detalhes do plist em <code>tools/servir_dados/README.md</code>.'))

story.append(h2('Diagnóstico'))
story.append(bullets([
    '<b>Servidor está rodando?</b> Abra <code>http://localhost:8765/</code> no browser. Deve mostrar listing da pasta.',
    '<b>Porta ocupada?</b> Linux: <code>lsof -i :8765</code> mostra quem está usando. Windows: <code>netstat -ano | findstr 8765</code>. Use outra porta: <code>--port 9000</code>.',
    '<b>App não acha o arquivo?</b> Navegue no browser até a URL exata para confirmar caminho e nome. Ajuste os placeholders no template.',
    '<b>Logs no terminal:</b> cada requisição é registrada com IP, método, caminho e status (200/404).',
]))
story.append(PageBreak())

# ===== 11. ATALHOS =====
story.append(h1('11. Atalhos de teclado'))
story.append(tbl([
    ['Tecla', 'Ação'],
    ['← →', 'Recuar/avançar um passo de tempo (snap para a frequência da variável).'],
    ['Espaço', 'Animar / pausar.'],
    ['Esc', 'Fechar modal de configuração.'],
    ['Ctrl + Scroll', 'Zoom no painel sob o cursor.'],
    ['Arrasto com botão direito', 'Pan no painel.'],
    ['Duplo-clique', 'Reset de zoom no painel.'],
], col_widths=[5*cm, 11*cm]))
story.append(h2('Atalhos exclusivos do modo GeoTIFF'))
story.append(tbl([
    ['Ação', 'Como acionar'],
    ['Selecionar painel ativo', 'Clique no botão "Painel M_n_" no canto do mapa.'],
    ['Mostrar/ocultar mapa-base', 'Checkbox "Mostrar mapa" no painel direito.'],
    ['Recentrar mapa no raster', 'Botão ⟲ na barra inferior do painel.'],
    ['Editar escala manual', 'Botão "Editar escala" → digite Min/Max → Enter.'],
], col_widths=[6*cm, 10*cm]))
story.append(PageBreak())

# ===== 12. TROUBLESHOOTING =====
story.append(h1('12. Solução de problemas'))
story.append(h3('Imagem não carrega ("Imagem não disponível no servidor")'))
story.append(bullets([
    'Verifique conexão com o FTP do CPTEC (<code>https://ftp1.cptec.inpe.br</code>).',
    'Verifique se a rodada existe para a data escolhida. Algumas rodadas só rodam em horários específicos (00Z, 12Z).',
    'Confirme o template do modelo: clique direito → Inspecionar → Network para ver a URL gerada e o status HTTP.',
]))
story.append(h3('GeoTIFF mostra "Failed to fetch" ou erro CORS'))
story.append(bullets([
    '<b>No app Electron:</b> webSecurity está desabilitado por padrão; não deveria ter CORS. Verifique se o FTP responde (rede, firewall).',
    '<b>No navegador via file://:</b> CORS bloqueia. Use o app Electron, OU rode o servidor HTTP local (seção 10) e use <code>http://localhost:8765/...</code>.',
]))
story.append(h3('Animação fica congelada / não avança'))
story.append(bullets([
    'A primeira passagem em modelos pesados (Eta) pode levar alguns segundos por passo. Espere completar uma volta — a segunda fica instantânea.',
    'No console (F12), procure por erros de fetch ou decode.',
]))
story.append(h3('App não abre / SmartScreen bloqueia'))
story.append(bullets([
    'No Windows, o SmartScreen pode bloquear executáveis não assinados. Clique em <b>Mais informações &rarr; Executar mesmo assim</b>.',
    'No macOS, o Gatekeeper pode bloquear apps não notarizados. Clique direito no .app &rarr; <b>Abrir</b> &rarr; confirme. Ou em Preferências &rarr; Segurança &rarr; "Abrir mesmo assim".',
    'Verifique antivírus: alguns sinalizam Electron como suspeito (falso-positivo). Adicione exceção para a pasta de instalação.',
]))
story.append(h3('Configuração foi perdida'))
story.append(bullets([
    'A config fica em <code>localStorage</code> do navegador/Electron. Limpar cache do navegador apaga.',
    '<b>Sempre exporte</b> sua configuração para .json (botão <b>Exportar</b> no modal de configuração) — facilita backup e migração entre máquinas.',
]))
story.append(h3('Saber a versão exata do app'))
story.append(p(
    'Abra o DevTools (F12) e procure no console pelo log <code>[GISELE] build = YYYYMMDD-HHMM-tag</code>. '
    'Esse marcador identifica a versão carregada e ajuda no suporte.'
))
story.append(PageBreak())

# ===== 13. APÊNDICE =====
story.append(h1('13. Apêndice — referência de placeholders'))
story.append(p('Lista completa para uso em templates de URL e nome de arquivo.'))
story.append(tbl([
    ['Placeholder', 'Onde se aplica', 'Significado'],
    ['{yyyy}',         'endereço (rodada) / nome (validade)', 'Ano 4 dígitos'],
    ['{mm}',           'idem',                                'Mês 2 dígitos'],
    ['{dd}',           'idem',                                'Dia 2 dígitos'],
    ['{hh}',           'idem',                                'Hora UTC 2 dígitos'],
    ['{yyyymmddhh}',   'idem',                                'Concatenação completa'],
    ['{yyyymmdd}',     'idem',                                'Sem hora'],
    ['{yyyymm}',       'idem',                                'Ano+mês'],
    ['{data}',         'qualquer',                            'String de data como digitada (8 ou 10 dígitos)'],
    ['{escopo1}',      'qualquer',                            'Escopo 1 do modelo ou variável (override por variável)'],
    ['{escopo2}',      'qualquer',                            'Escopo 2 do modelo ou variável'],
    ['{prefixo}',      'nome',                                'Prefixo de arquivo (da variável)'],
    ['{ext}',          'nome',                                'Extensão (.png, .gif, .tif...)'],
    ['{N} ou {N%n}',   'nome',                                'Índice da figura na sequência, padded a n dígitos'],
    ['{F} ou {F%n}',   'nome',                                'Horas de previsão = índice × freq'],
    ['{fct} ou {f%n}', 'nome',                                'Idem F, prefixado com "f"'],
    ['{passo}',        'nome (legacy)',                       'Equivalente a {F}'],
    ['{passo4}',       'nome (legacy)',                       'Equivalente a {N%4}'],
], col_widths=[3.8*cm, 4.5*cm, 7.5*cm]))
story.append(h2('Notas'))
story.append(bullets([
    'O modificador <code>%n</code> faz padding com zeros à esquerda. <code>{F%3}</code> = 024 (não 24).',
    'No CAMINHO (endereço), os placeholders de data sempre referem à <b>rodada</b>. No NOME do arquivo, referem à <b>validade</b> (rodada + F horas).',
    'Para análise/observação (Freq=0), não há previsão; N=0 e F=0; a validade coincide com a rodada.',
]))
story.append(Spacer(1, 1*cm))
story.append(hr())
story.append(p('GISELE — Gestão Integrada de Soluções Estratégicas e Inteligência © CPTEC/INPE — Versão 2.0.0', 'FooterStyle'))
story.append(p(f'Manual de Uso gerado automaticamente em {date.today().strftime("%d/%m/%Y")}', 'FooterStyle'))

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(GRAY_M)
    canvas.setFont('Helvetica', 8.5)
    canvas.drawCentredString(A4[0] / 2, 1*cm, f'— {doc.page} —')
    canvas.drawString(2*cm, 1*cm, 'GISELE · Manual de Uso')
    canvas.drawRightString(A4[0] - 2*cm, 1*cm, 'v2.0.0')
    canvas.restoreState()

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=1.8*cm, bottomMargin=1.8*cm,
    title='GISELE — Manual de Uso',
    author='CPTEC / INPE',
    subject='Manual de Uso',
)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f'OK: {OUT}  ({OUT.stat().st_size} bytes)')
