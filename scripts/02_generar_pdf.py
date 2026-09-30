# -*- coding: utf-8 -*-
"""Markdown -> HTML con estilos de impresion (A4). Despues Chrome lo pasa a PDF."""
import io, os, re, sys, html

SRC = sys.argv[1]
OUT = sys.argv[2]

txt = io.open(SRC, encoding="utf-8").read()

CSS = """
@page { size: A4; margin: 14mm 15mm 14mm 15mm; }
* { box-sizing: border-box; }
body{ margin:0; font:9.5pt/1.28 Georgia,Cambria,"Times New Roman",serif; color:#1a1a1a; }
h1,h2,h3{ font-family:"Segoe UI",Calibri,Arial,sans-serif; color:#12213f; margin:0; line-height:1.2; }
h1{ font-size:17pt; font-weight:700; margin:0 0 3pt; letter-spacing:-.3pt; }
h2{ font-size:12.5pt; font-weight:700; margin:10pt 0 4pt; padding-bottom:2pt;
    border-bottom:1.2pt solid #12213f; page-break-after:avoid; }
h3{ font-size:10.5pt; font-weight:600; margin:9pt 0 3pt; color:#2b3a67; page-break-after:avoid; }
p{ margin:0 0 4.5pt; text-align:justify; }
hr{ border:0; border-top:.6pt solid #c8c8c8; margin:7pt 0; }
strong{ font-weight:700; color:#101010; }
em{ font-style:italic; }
code{ font-family:Consolas,"Courier New",monospace; font-size:9pt; background:#f2f3f6;
      padding:.5pt 3pt; border-radius:2pt; }
pre{ font-family:Consolas,"Courier New",monospace; font-size:8.3pt; background:#f5f6f8;
     border-left:2.5pt solid #2b3a67; padding:5pt 8pt; margin:6pt 0; line-height:1.35;
     white-space:pre-wrap; page-break-inside:avoid; }
pre code{ background:none; padding:0; }
blockquote{ margin:6pt 0; padding:5pt 10pt; background:#eef1f7; border-left:2.5pt solid #2b3a67;
            page-break-inside:avoid; }
blockquote p{ margin:0; }
table{ border-collapse:collapse; width:100%; margin:5pt 0 7pt; font-size:8pt;
       font-family:"Segoe UI",Calibri,Arial,sans-serif; }
th,td{ border:.5pt solid #b9bfcc; padding:2.5pt 4pt; text-align:left; vertical-align:top; }
th{ background:#e6eaf2; font-weight:600; color:#12213f; }
tr:nth-child(even) td{ background:#fafbfc; }
tr{ page-break-inside:avoid; }
ul,ol{ margin:0 0 7pt; padding-left:17pt; }
li{ margin-bottom:2.5pt; }
.meta{ font-family:"Segoe UI",Calibri,Arial,sans-serif; font-size:9.5pt; color:#3d4759;
       margin-bottom:12pt; }
.meta p{ margin:1pt 0; text-align:left; }
h1 + p em, .sub{ color:#3d4759; }
"""

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", s)
    s = re.sub(r"(?<!\w)(https?://[^\s<]+)", r"\1", s)
    return s

def fila(l):
    celdas = [c.strip() for c in l.strip().strip("|").split("|")]
    return celdas

out, i = [], 0
lineas = txt.split("\n")
while i < len(lineas):
    l = lineas[i]

    if l.startswith("```"):
        buf = []
        i += 1
        while i < len(lineas) and not lineas[i].startswith("```"):
            buf.append(html.escape(lineas[i], quote=False)); i += 1
        i += 1
        out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
        continue

    if re.match(r"^\|.*\|\s*$", l) and i + 1 < len(lineas) and re.match(r"^\|[\s:\-|]+\|\s*$", lineas[i+1]):
        enc = fila(l); i += 2
        cuerpo = []
        while i < len(lineas) and re.match(r"^\|.*\|\s*$", lineas[i]):
            cuerpo.append(fila(lineas[i])); i += 1
        t = "<table><thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in enc) + "</tr></thead><tbody>"
        for r in cuerpo:
            t += "<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>"
        out.append(t + "</tbody></table>")
        continue

    if l.startswith(">"):
        buf = []
        while i < len(lineas) and lineas[i].startswith(">"):
            buf.append(lineas[i].lstrip(">").strip()); i += 1
        out.append("<blockquote><p>" + inline(" ".join(buf)) + "</p></blockquote>")
        continue

    m = re.match(r"^(#{1,6})\s+(.*)$", l)
    if m:
        n = len(m.group(1))
        out.append("<h%d>%s</h%d>" % (min(n,3), inline(m.group(2)), min(n,3)))
        i += 1; continue

    if re.match(r"^---+\s*$", l):
        out.append("<hr>"); i += 1; continue

    if re.match(r"^\s*[-*]\s+", l):
        buf = []
        while i < len(lineas) and re.match(r"^\s*[-*]\s+", lineas[i]):
            buf.append("<li>%s</li>" % inline(re.sub(r"^\s*[-*]\s+", "", lineas[i]))); i += 1
        out.append("<ul>" + "".join(buf) + "</ul>"); continue

    if re.match(r"^\s*\d+\.\s+", l):
        buf = []
        while i < len(lineas) and re.match(r"^\s*\d+\.\s+", lineas[i]):
            buf.append("<li>%s</li>" % inline(re.sub(r"^\s*\d+\.\s+", "", lineas[i]))); i += 1
        out.append("<ol>" + "".join(buf) + "</ol>"); continue

    if l.strip() == "":
        i += 1; continue

    buf = []
    while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#{1,6}\s|\||>|```|---+\s*$|\s*[-*]\s|\s*\d+\.\s)", lineas[i]):
        buf.append(lineas[i].rstrip() + ("<<BR>>" if lineas[i].endswith("  ") else "")); i += 1
    par = " ".join(x.strip() for x in buf)
    out.append("<p>" + inline(par).replace("&lt;&lt;BR&gt;&gt;", "<br>").replace("<<BR>>", "<br>") + "</p>")

cuerpo = "\n".join(out)
doc = ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
       '<title>Cazadores de Patrones en MiniRed</title>'
       '<style>' + CSS + '</style></head><body>' + cuerpo + '</body></html>')
io.open(OUT, "w", encoding="utf-8", newline="\n").write(doc)
print("HTML generado:", OUT, "(%d elementos)" % len(out))
