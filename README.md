# Cazadores de Patrones en MiniRed

Reglas de asociación sobre `MiniRed_DW` con Apriori y FP-Growth.
Actividad práctica de la Clase 8 — Unidad 5, Base de Datos Aplicada.

**[▶ Ver el trabajo completo](https://SantiagoSkrobacki.github.io/MiniRed-2/)**

---

## El resultado en una línea

De 53 reglas que devolvió Apriori sobrevivieron 7 a la curaduría — y descubrimos que **las
reglas con explicación de negocio plausible son exactamente las que se mantienen estables
entre 2024 y 2025**.

| | |
|---|---|
| Transacciones analizadas | 67.521 |
| Ítems distintos | 30 |
| Reglas con soporte 0,05 | 8 |
| Reglas con soporte 0,01 | 53 |
| Reglas curadas finales | 7 |
| Lift más alto que sobrevivió | 14,26 |

## El recorte y su justificación

Se trabajó sobre `Fact_Ventas` con el catálogo completo (30 productos), las 7 sucursales y los
dos años disponibles (2024–2025). Se tomó una única decisión de recorte:

> **Se excluyeron los tickets de un solo producto: 152.944 de 220.465 (el 69 %).**
> Una transacción con un único ítem no puede generar ninguna regla de asociación, pero sí
> infla el denominador y hunde artificialmente todos los soportes. Quedaron 67.521
> transacciones útiles, con 2,34 productos por ticket en promedio.

## Dos diferencias entre el enunciado y la base

1. **El enunciado indica agrupar por `IdVenta`, "el ticket".** En `MiniRed_DW` el `IdVenta` es
   la PK de la *línea*; el ticket es `IdTicket`. Agrupando como dice el texto, cada canasta
   tendría un solo producto y Apriori no encontraría nada.
2. **El enunciado habla de 4.200 artículos en 14 sucursales.** La base instalada tiene 30 y 7.

## Cómo reproducirlo

Requiere SQL Server con `MiniRed_DW`, Python 3 y Weka 3.8.

```powershell
# 1. Exportar las canastas desde la base
powershell -ExecutionPolicy Bypass -File scripts\00_exportar_desde_sqlserver.ps1

# 2. Construir la matriz transaccional
python scripts\01_build_arff.py

# 3. Correr Apriori — las dos corridas del informe
java -cp weka.jar weka.associations.Apriori -t data\minired_canasta.arff -N 30  -C 0.5 -M 0.05 -D 0.05 -Z
java -cp weka.jar weka.associations.Apriori -t data\minired_canasta.arff -N 100 -C 0.5 -M 0.01 -D 0.01 -Z
```

`-Z` (*treatZeroAsMissing*) es obligatorio: sin él, Apriori genera reglas sobre la **ausencia**
de productos, que son ciertas y completamente inútiles.

El script SQL `sql/01_matriz_transaccional.sql` recalcula soporte, confianza y lift con las
fórmulas a mano, y es lo que se usó para verificar la salida de Weka de forma independiente.

## Estructura

```
├── index.html              La presentación completa (GitHub Pages)
├── sql/
│   └── 01_matriz_transaccional.sql    Consulta documentada + cálculo de métricas
├── scripts/
│   ├── 00_exportar_desde_sqlserver.ps1
│   └── 01_build_arff.py               Genera la matriz transaccional
├── data/
│   ├── minired_canasta.arff           67.521 transacciones × 30 ítems
│   ├── minired_canasta_2024.arff      Para validar en otro período
│   ├── minired_canasta_2025.arff
│   ├── catalogo_items.csv             Atributo de Weka → producto real
│   └── raw/                           Exports intermedios de sqlcmd
├── weka/                   Salidas crudas de las cinco corridas
└── informe/
    └── 04_reflexiones_individuales.md
```

## Verificación

Todos los valores se calcularon por **dos caminos independientes**: SQL contra `MiniRed_DW`
aplicando las fórmulas, y Weka sobre el `.arff`. Coinciden hasta el segundo decimal.

| Regla | Conf. SQL | Conf. Weka | Lift SQL | Lift Weka |
|---|---|---|---|---|
| Detergente → Palitos Helados | 0,7527 | 0,75 | 7,450 | 7,45 |
| Mermelada → Caramelos | 0,7360 | 0,74 | 8,443 | 8,44 |
| Gaseosa Lima-Limón → Cerveza Negra | 0,5268 | 0,53 | 14,262 | 14,26 |

Ningún valor de soporte, confianza o lift fue estimado.

## El descarte más valioso

`Palitos Helados → Detergente` tiene lift **7,45**, el cuarto más alto del dataset, y ninguna
explicación de negocio posible. Además cae 43 % entre 2024 y 2025. Si el criterio fuera
"ordenar por lift y quedarse con las de arriba", esta regla entraría a la presentación.

**Un número alto no es un hallazgo.**

## Integrantes

- *(completar)*
- *(completar)*
