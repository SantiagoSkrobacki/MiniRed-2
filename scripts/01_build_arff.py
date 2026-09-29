# -*- coding: utf-8 -*-
"""
Paso 2 de 3 - Construye la matriz transaccional (.arff) para Weka.

Uso (parado en la raiz del repo):
    python scripts/01_build_arff.py

Entrada : data/raw/productos.txt y data/raw/canasta.txt (los genera 00_exportar...)
Salida  : data/minired_canasta.arff        (todas las transacciones)
          data/minired_canasta_2024.arff   (para validar en otro periodo)
          data/minired_canasta_2025.arff
          data/catalogo_items.csv          (atributo Weka -> producto real)

Decisiones de modelado, explicadas en el README:
  - El grano de salida es el TICKET, no la linea. En MiniRed_DW el ticket es
    IdTicket; IdVenta es la PK de la linea.
  - IdTicket NO se incluye como atributo: es un identificador unico y su
    presencia impide que Apriori encuentre nada.
  - Los atributos se declaran nominales {0,1} para no necesitar discretizacion.
    Al correr Apriori hay que usar -Z (treatZeroAsMissing) para que el 0 no
    genere reglas sobre la ausencia de productos.
"""
import io
import os
import re
import sys
import unicodedata
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRUDO = os.path.join(RAIZ, "data", "raw")
DESTINO = os.path.join(RAIZ, "data")


def leer(nombre):
    """Lee un export de sqlcmd, salteando los avisos del servidor."""
    ruta = os.path.join(CRUDO, nombre)
    if not os.path.exists(ruta):
        sys.exit("Falta %s. Corre primero scripts/00_exportar_desde_sqlserver.ps1" % ruta)
    with io.open(ruta, encoding="utf-8", errors="replace") as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea or linea.startswith("Changed database context"):
                continue
            yield linea


def slug(texto):
    """Nombre de atributo valido para ARFF: sin acentos ni espacios."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")


# --- catalogo ---------------------------------------------------------------
atributo, meta = {}, {}
for linea in leer("productos.txt"):
    campos = [c.strip() for c in linea.split("|")]
    if len(campos) < 4 or not campos[0].isdigit():
        continue
    pid = int(campos[0])
    atributo[pid] = slug(campos[1])
    meta[pid] = {"nombre": campos[1], "categoria": campos[2], "rubro": campos[3]}

orden = sorted(atributo)
nombres = [atributo[p] for p in orden]
if len(set(nombres)) != len(nombres):
    sys.exit("Hay nombres de atributo duplicados tras normalizar.")

# --- canastas ---------------------------------------------------------------
tickets, anio_de = defaultdict(set), {}
for linea in leer("canasta.txt"):
    campos = [c.strip() for c in linea.split("|")]
    if len(campos) < 3 or not campos[1].isdigit():
        continue
    tickets[campos[0]].add(int(campos[1]))
    anio_de[campos[0]] = campos[2]

if not tickets:
    sys.exit("No se leyo ninguna canasta. Revisa data/raw/canasta.txt")


def escribir_arff(ruta, claves, relacion):
    with io.open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%% Matriz transaccional MiniRed_DW - %s\n" % relacion)
        fh.write("% Grano: una fila por ticket. IdTicket NO figura como atributo.\n")
        fh.write("% Filtro: solo tickets con 2 o mas productos distintos.\n")
        fh.write("%% Transacciones: %d | Items: %d\n\n" % (len(claves), len(orden)))
        fh.write("@relation %s\n\n" % relacion)
        for n in nombres:
            fh.write("@attribute %s {0,1}\n" % n)
        fh.write("\n@data\n")
        for clave in claves:
            presentes = tickets[clave]
            fh.write(",".join("1" if pid in presentes else "0" for pid in orden) + "\n")


todas = sorted(tickets)
por_anio = defaultdict(list)
for clave in todas:
    por_anio[anio_de[clave]].append(clave)

escribir_arff(os.path.join(DESTINO, "minired_canasta.arff"), todas, "MiniRed_Canasta")
for anio, claves in sorted(por_anio.items()):
    escribir_arff(
        os.path.join(DESTINO, "minired_canasta_%s.arff" % anio),
        claves,
        "MiniRed_Canasta_%s" % anio,
    )

# --- catalogo de referencia -------------------------------------------------
with io.open(os.path.join(DESTINO, "catalogo_items.csv"), "w",
             encoding="utf-8-sig", newline="\n") as fh:
    fh.write("AtributoEnWeka,NombreProducto,Categoria,Rubro\n")
    for pid in orden:
        m = meta[pid]
        fh.write('%s,"%s","%s","%s"\n' % (atributo[pid], m["nombre"], m["categoria"], m["rubro"]))

lineas = sum(len(v) for v in tickets.values())
print("transacciones : %d" % len(todas))
for anio, claves in sorted(por_anio.items()):
    print("  %s        : %d" % (anio, len(claves)))
print("items         : %d" % len(orden))
print("items/ticket  : %.2f" % (lineas / float(len(todas))))
print("destino       : %s" % DESTINO)
