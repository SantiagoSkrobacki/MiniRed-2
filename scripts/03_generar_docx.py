# -*- coding: utf-8 -*-
"""
Markdown -> .docx nativo, sin dependencias externas.

Un .docx es un ZIP con XML (OOXML). Se genera a mano para no depender de
python-docx, que no se puede instalar en esta maquina (no hay pip).

Uso:  python md2docx.py entrada.md salida.docx
"""
import io, os, re, sys, zipfile
from xml.sax.saxutils import escape

SRC, OUT = sys.argv[1], sys.argv[2]
md = io.open(SRC, encoding="utf-8").read()

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

def esc(s):
    return escape(s).replace('"', "&quot;")

# ---------------------------------------------------------------- runs
def runs(texto, base=""):
    """Convierte **negrita**, *cursiva* y `codigo` en runs de Word."""
    partes = re.split(r"(\*\*[^*]+\*\*|(?<!\*)\*[^*\n]+\*(?!\*)|`[^`]+`)", texto)
    out = []
    for p in partes:
        if not p:
            continue
        props, txt = [base], p
        if p.startswith("**") and p.endswith("**") and len(p) > 4:
            props.append("<w:b/>"); txt = p[2:-2]
        elif p.startswith("`") and p.endswith("`") and len(p) > 2:
            props.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="17"/>'
                         '<w:shd w:val="clear" w:fill="F2F3F6"/>')
            txt = p[1:-1]
        elif p.startswith("*") and p.endswith("*") and len(p) > 2:
            props.append("<w:i/>"); txt = p[1:-1]
        # los links markdown quedan como texto plano
        txt = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", txt)
        rpr = "".join(props)
        out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>'
                   % (("<w:rPr>%s</w:rPr>" % rpr) if rpr else "", esc(txt)))
    return "".join(out)

def par(texto, estilo=None, extra="", base=""):
    ppr = ""
    if estilo or extra:
        ppr = "<w:pPr>%s%s</w:pPr>" % (('<w:pStyle w:val="%s"/>' % estilo) if estilo else "", extra)
    return "<w:p>%s%s</w:p>" % (ppr, runs(texto, base))

JUST = '<w:jc w:val="both"/>'

BORDES = ('<w:tblBorders>' + "".join(
    '<w:%s w:val="single" w:sz="4" w:space="0" w:color="B9BFCC"/>' % b
    for b in ("top", "left", "bottom", "right", "insideH", "insideV")) + '</w:tblBorders>')

def celda(txt, encabezado=False):
    sombra = '<w:shd w:val="clear" w:fill="E6EAF2"/>' if encabezado else ""
    base = "<w:b/>" if encabezado else ""
    return ('<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/>%s</w:tcPr>%s</w:tc>'
            % (sombra, par(txt, "TablaTexto", "", base)))

def tabla(enc, filas):
    x = ('<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/>%s'
         '<w:tblLayout w:type="autofit"/></w:tblPr>' % BORDES)
    x += ('<w:tr><w:trPr><w:tblHeader/></w:trPr>'
          + "".join(celda(c, True) for c in enc) + "</w:tr>")
    for f in filas:
        x += "<w:tr>" + "".join(celda(c) for c in f) + "</w:tr>"
    return x + "</w:tbl>" + par("", "Espaciador")

# ---------------------------------------------------------------- parser
cuerpo, i = [], 0
L = md.split("\n")
while i < len(L):
    l = L[i]

    if l.startswith("```"):
        i += 1; buf = []
        while i < len(L) and not L[i].startswith("```"):
            buf.append(L[i]); i += 1
        i += 1
        for b in buf:
            cuerpo.append(par(b.replace("*", ""), "Codigo"))
        cuerpo.append(par("", "Espaciador"))
        continue

    if re.match(r"^\|.*\|\s*$", l) and i + 1 < len(L) and re.match(r"^\|[\s:\-|]+\|\s*$", L[i+1]):
        enc = [c.strip() for c in l.strip().strip("|").split("|")]
        i += 2; filas = []
        while i < len(L) and re.match(r"^\|.*\|\s*$", L[i]):
            filas.append([c.strip() for c in L[i].strip().strip("|").split("|")]); i += 1
        cuerpo.append(tabla(enc, filas)); continue

    if l.startswith(">"):
        buf = []
        while i < len(L) and L[i].startswith(">"):
            buf.append(L[i].lstrip(">").strip()); i += 1
        cuerpo.append(par(" ".join(buf), "Destacado", JUST)); continue

    m = re.match(r"^(#{1,6})\s+(.*)$", l)
    if m:
        cuerpo.append(par(m.group(2), "Heading%d" % min(len(m.group(1)), 3))); i += 1; continue

    if re.match(r"^---+\s*$", l):
        cuerpo.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" '
                      'w:color="C8C8C8"/></w:pBdr></w:pPr></w:p>')
        i += 1; continue

    m = re.match(r"^\s*[-*]\s+(.*)$", l)
    if m:
        while i < len(L):
            m2 = re.match(r"^\s*[-*]\s+(.*)$", L[i])
            if not m2: break
            cuerpo.append(par(m2.group(1), "Vinieta")); i += 1
        continue

    m = re.match(r"^\s*\d+\.\s+(.*)$", l)
    if m:
        while i < len(L):
            m2 = re.match(r"^\s*\d+\.\s+(.*)$", L[i])
            if not m2: break
            cuerpo.append(par(m2.group(1), "Vinieta")); i += 1
        continue

    if not l.strip():
        i += 1; continue

    buf = []
    while i < len(L) and L[i].strip() and not re.match(
            r"^(#{1,6}\s|\||>|```|---+\s*$|\s*[-*]\s|\s*\d+\.\s)", L[i]):
        buf.append((L[i].strip(), L[i].endswith("  "))); i += 1
    if any(b for _, b in buf[:-1]):
        trozos = [runs(t) + ("<w:r><w:br/></w:r>" if b and k < len(buf) - 1 else "")
                  for k, (t, b) in enumerate(buf)]
        cuerpo.append("<w:p>%s</w:p>" % "".join(trozos))
    else:
        cuerpo.append(par(" ".join(t for t, _ in buf), None, JUST))

SECT = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1000" w:right="1000" w:bottom="1000" w:left="1000" '
        'w:header="510" w:footer="510" w:gutter="0"/></w:sectPr>')

DOC = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
       '<w:document %s><w:body>%s%s</w:body></w:document>' % (NS, "".join(cuerpo), SECT))

# ---------------------------------------------------------------- estilos
def estilo(sid, nombre, ppr, rpr, base=None):
    return ('<w:style w:type="paragraph" w:styleId="%s"><w:name w:val="%s"/>%s'
            '<w:pPr>%s</w:pPr><w:rPr>%s</w:rPr></w:style>'
            % (sid, nombre, ('<w:basedOn w:val="%s"/>' % base) if base else "", ppr, rpr))

SERIF = '<w:rFonts w:ascii="Georgia" w:hAnsi="Georgia"/>'
SANS = '<w:rFonts w:ascii="Segoe UI" w:hAnsi="Segoe UI"/>'

STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles %s>'
  '<w:docDefaults><w:rPrDefault><w:rPr>%s<w:sz w:val="20"/><w:szCs w:val="20"/>'
  '<w:lang w:val="es-AR"/></w:rPr></w:rPrDefault>'
  '<w:pPrDefault><w:pPr><w:spacing w:after="90" w:line="250" w:lineRule="auto"/>'
  '</w:pPr></w:pPrDefault></w:docDefaults>'
  + estilo("Normal", "Normal", "", SERIF + '<w:sz w:val="20"/>')
  + estilo("Heading1", "heading 1", '<w:spacing w:before="0" w:after="120"/><w:outlineLvl w:val="0"/>',
           SANS + '<w:b/><w:sz w:val="32"/><w:color w:val="12213F"/>')
  + estilo("Heading2", "heading 2",
           '<w:spacing w:before="220" w:after="100"/><w:outlineLvl w:val="1"/>'
           '<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="3" w:color="12213F"/></w:pBdr>',
           SANS + '<w:b/><w:sz w:val="24"/><w:color w:val="12213F"/>')
  + estilo("Heading3", "heading 3", '<w:spacing w:before="150" w:after="60"/><w:outlineLvl w:val="2"/>',
           SANS + '<w:b/><w:sz w:val="21"/><w:color w:val="2B3A67"/>')
  + estilo("Codigo", "Codigo", '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
           '<w:ind w:left="220"/><w:shd w:val="clear" w:fill="F5F6F8"/>'
           '<w:pBdr><w:left w:val="single" w:sz="18" w:space="6" w:color="2B3A67"/></w:pBdr>',
           '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="17"/>')
  + estilo("Destacado", "Destacado", '<w:spacing w:before="120" w:after="120"/>'
           '<w:ind w:left="220" w:right="160"/><w:shd w:val="clear" w:fill="EEF1F7"/>'
           '<w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="2B3A67"/></w:pBdr>',
           SERIF + '<w:sz w:val="20"/>')
  + estilo("TablaTexto", "TablaTexto", '<w:spacing w:before="20" w:after="20" w:line="230" w:lineRule="auto"/>',
           SANS + '<w:sz w:val="17"/>')
  + estilo("Vinieta", "Vinieta", '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
           '<w:spacing w:after="60"/><w:ind w:left="400" w:hanging="200"/>', SERIF + '<w:sz w:val="20"/>')
  + estilo("Espaciador", "Espaciador", '<w:spacing w:after="0" w:line="120" w:lineRule="exact"/>', '<w:sz w:val="4"/>')
  + '</w:styles>') % (NS, SERIF)

NUM = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering %s>'
  '<w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:start w:val="1"/>'
  '<w:numFmt w:val="bullet"/><w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/>'
  '<w:pPr><w:ind w:left="400" w:hanging="200"/></w:pPr>'
  '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/></w:rPr></w:lvl></w:abstractNum>'
  '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>') % NS

CT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
  '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
  '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
  '<Default Extension="xml" ContentType="application/xml"/>'
  '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
  '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
  '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
  '</Types>')

RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
  '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
  '</Relationships>')

DRELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
  '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
  '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
  '</Relationships>')

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", CT)
    z.writestr("_rels/.rels", RELS)
    z.writestr("word/_rels/document.xml.rels", DRELS)
    z.writestr("word/document.xml", DOC)
    z.writestr("word/styles.xml", STYLES)
    z.writestr("word/numbering.xml", NUM)

print("docx generado:", OUT)
print("  parrafos/tablas:", len(cuerpo))
print("  tamanio:", os.path.getsize(OUT), "bytes")
