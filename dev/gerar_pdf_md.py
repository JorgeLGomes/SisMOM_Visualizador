#!/usr/bin/env python3
"""
Converte arquivos Markdown para PDF usando reportlab.
Uso: python gerar_pdf_md.py src.md dst.pdf [src2.md dst2.pdf ...]
"""
import sys, re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, Preformatted
)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

NAVY   = colors.HexColor('#0b1e3a')
CYAN   = colors.HexColor('#0a6e8a')
GRAY_D = colors.HexColor('#384858')
GRAY_M = colors.HexColor('#6a7c8e')
GRAY_L = colors.HexColor('#e6ecf2')
GRAY_B = colors.HexColor('#f6f9fc')

styles = getSampleStyleSheet()
def _S(name, **kw):
    styles.add(ParagraphStyle(name=name, **kw))

_S('MD_H1', parent=styles['Heading1'], fontSize=17, leading=21, textColor=NAVY,   spaceBefore=16, spaceAfter=8)
_S('MD_H2', parent=styles['Heading2'], fontSize=13, leading=17, textColor=CYAN,   spaceBefore=12, spaceAfter=5)
_S('MD_H3', parent=styles['Heading3'], fontSize=11, leading=15, textColor=GRAY_D, spaceBefore=9,  spaceAfter=4)
_S('MD_H4', parent=styles['Heading3'], fontSize=10.5,leading=14,textColor=GRAY_D, spaceBefore=7,  spaceAfter=3)
_S('MD_Body', parent=styles['BodyText'], fontSize=10, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=6)
_S('MD_BQ',   parent=styles['BodyText'], fontSize=9.5,leading=13, leftIndent=12, rightIndent=8,
   spaceAfter=6, textColor=GRAY_D, backColor=GRAY_B, borderPadding=5, borderColor=CYAN)
_S('MD_Li',   parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=2)
_S('MD_Code', parent=styles['Code'],     fontSize=8.5,leading=12, fontName='Courier',
   textColor=NAVY, leftIndent=8, spaceAfter=6, backColor=GRAY_B, borderPadding=4)
_S('MD_Footer', parent=styles['Normal'], fontSize=8, textColor=GRAY_M, alignment=TA_CENTER)


# Substituição de emoji por markup colorido compatível com reportlab
EMOJI_MAP = [
    ('✅', '<font color="#1a8b5e"><b> OK </b></font>'),       # ✅
    ('🟡', '<font color="#a05500"><b>PARC</b></font>'),    # 🟡
    ('❌', '<font color="#c0392b"><b> -- </b></font>'),        # ❌
    ('✔', '<font color="#1a8b5e"><b>✔</b></font>'),      # ✔
    ('⚠', '<font color="#a05500">[!]</font>'),                 # ⚠
    ('📦', '[PKG]'), ('🗺', '[MAP]'),
    ('📌', '[PIN]'), ('⚙', '[CFG]'),
    ('🧮', '[NUM]'), ('🔧', '[TOOL]'),
    ('📡', '[ANT]'), ('🗄', '[DB]'),
]

def _esc(t):
    return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def _emoji(txt):
    """Substitui emoji por markup colorido antes de escapar."""
    for em, rep in EMOJI_MAP:
        txt = txt.replace(em, rep)
    # Remove emoji restantes (substitui por vazio para não quebrar o parser)
    txt = re.sub(r'[\U00010000-\U0010ffff]', '', txt)
    return txt

def _inline(txt):
    """Código primeiro (salvo), emoji (salvo), escape, negrito/itálico, restaura."""
    # 1) Salva spans de código antes de qualquer transformação
    code_ph = {}
    def _save_code(m):
        k = '\x00C%d\x00' % len(code_ph)
        code_ph[k] = '<font face="Courier" fontSize="8.5">%s</font>' % _esc(m.group(1))
        return k
    txt = re.sub(r'`(.+?)`', _save_code, txt)

    # 2) Salva substituições de emoji (markup HTML pronto, não deve ser escapado)
    emoji_ph = {}
    def _save_emoji(text):
        for em, rep in EMOJI_MAP:
            while em in text:
                k = '\x00E%d\x00' % len(emoji_ph)
                emoji_ph[k] = rep
                text = text.replace(em, k, 1)
        # Remove emoji Unicode restantes (plano suplementar)
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        return text
    txt = _save_emoji(txt)

    # 3) Escapa o restante (texto literal, sem código nem emoji)
    txt = _esc(txt)

    # 4) Negrito e itálico
    txt = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', txt)
    txt = re.sub(r'\*([^*]+?)\*',  r'<i>\1</i>', txt)

    # 5) Links → texto simples
    txt = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', txt)

    # 6) Restaura placeholders (em ordem: código e emoji, já são HTML válido)
    for k, v in code_ph.items():
        txt = txt.replace(_esc(k), v)
    for k, v in emoji_ph.items():
        txt = txt.replace(_esc(k), v)
    return txt

def _para(txt, style='MD_Body'):
    return Paragraph(_inline(txt), styles[style])

def _hr():
    return HRFlowable(width='100%', thickness=0.5, color=GRAY_L, spaceBefore=4, spaceAfter=6)

def _tbl(rows):
    if not rows:
        return Spacer(1, 2)
    col_n = max(len(r) for r in rows)
    W = A4[0] - 4.4 * cm
    col_w = [W / col_n] * col_n
    tdata = []
    for ri, row in enumerate(rows):
        row = list(row) + [''] * (col_n - len(row))
        cells = [Paragraph(_inline(c), styles['MD_Body']) for c in row]
        tdata.append(cells)
    t = Table(tdata, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME',      (0,0),(-1,-1),'Helvetica'),
        ('FONTSIZE',      (0,0),(-1,-1),9),
        ('VALIGN',        (0,0),(-1,-1),'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1),4),
        ('BOTTOMPADDING', (0,0),(-1,-1),4),
        ('LEFTPADDING',   (0,0),(-1,-1),5),
        ('RIGHTPADDING',  (0,0),(-1,-1),5),
        ('GRID',          (0,0),(-1,-1),0.3,GRAY_L),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,GRAY_B]),
        ('BACKGROUND',    (0,0),(-1,0),NAVY),
        ('TEXTCOLOR',     (0,0),(-1,0),colors.white),
        ('FONTNAME',      (0,0),(-1,0),'Helvetica-Bold'),
    ]))
    return t

def parse_md(text):
    lines = text.splitlines()
    story = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # Fenced code block
        if line.strip().startswith('```'):
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1
            story.append(Preformatted(_esc('\n'.join(code_lines)), styles['MD_Code']))
            continue

        # Headings
        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            lvl = len(m.group(1))
            st = {1:'MD_H1',2:'MD_H2',3:'MD_H3',4:'MD_H4'}.get(lvl,'MD_H3')
            story.append(_para(m.group(2).strip(), st))
            i += 1
            continue

        # HR
        if re.match(r'^[-*_]{3,}$', line.strip()):
            story.append(_hr())
            i += 1
            continue

        # Table
        if '|' in line and re.match(r'\s*\|', line):
            table_lines = []
            while i < n and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            rows = []
            for tl in table_lines:
                if re.match(r'^\s*\|?\s*[-:]+\s*\|', tl):
                    continue
                cols = [c.strip() for c in tl.strip().strip('|').split('|')]
                rows.append(cols)
            if rows:
                story.append(_tbl(rows))
            continue

        # Blockquote
        if line.startswith('>'):
            bq = []
            while i < n and lines[i].startswith('>'):
                bq.append(lines[i].lstrip('>').strip())
                i += 1
            story.append(_para(' '.join(bq), 'MD_BQ'))
            continue

        # Unordered list
        if re.match(r'^\s*[-*+]\s+', line):
            while i < n and re.match(r'^\s*[-*+]\s+', lines[i]):
                m2 = re.match(r'^\s*[-*+]\s+(.*)', lines[i])
                txt = m2.group(1) if m2 else lines[i]
                story.append(Paragraph('• ' + _inline(txt), styles['MD_Li']))
                i += 1
            story.append(Spacer(1, 4))
            continue

        # Ordered list
        if re.match(r'^\d+\.\s+', line):
            num = 1
            while i < n and re.match(r'^\d+\.\s+', lines[i]):
                m2 = re.match(r'^\d+\.\s+(.*)', lines[i])
                txt = m2.group(1) if m2 else lines[i]
                story.append(Paragraph('%d. %s' % (num, _inline(txt)), styles['MD_Li']))
                num += 1
                i += 1
            story.append(Spacer(1, 4))
            continue

        # Blank line
        if not line.strip():
            story.append(Spacer(1, 5))
            i += 1
            continue

        # Paragraph
        para_lines = []
        while i < n and lines[i].strip() and not re.match(
                r'^#{1,4}\s|^```|^\s*[-*+]\s|\d+\.\s|^\s*\||^\s*>|^[-*_]{3,}$', lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            story.append(_para(' '.join(para_lines)))

    return story


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GRAY_M)
    canvas.drawCentredString(A4[0]/2, 1.2*cm, '%s  |  pagina %d' % (doc.title, doc.page))
    canvas.restoreState()


def convert(src, dst):
    text = Path(src).read_text(encoding='utf-8')
    story = parse_md(text)
    doc = SimpleDocTemplate(
        str(dst),
        pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2*cm,    bottomMargin=2*cm,
        title=Path(src).stem,
        author='CPTEC/INPE',
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print('  OK: %s' % dst)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2 != 0:
        print('Uso: python gerar_pdf_md.py src.md dst.pdf [...]')
        sys.exit(1)
    for src, dst in zip(args[0::2], args[1::2]):
        convert(src, dst)
