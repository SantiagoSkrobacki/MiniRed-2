# Cazadores de Patrones en MiniRed
### Reglas de asociación sobre MiniRed_DW con Apriori y FP-Growth

**Materia:** Base de Datos Aplicada — Unidad 5  
**Actividad:** Clase 8 — De la base de datos real a la regla de negocio  
**Integrantes:** *(completar)*  
**Herramientas:** SQL Server 2025 · Weka 3.8.7 · Python 3.14  
**Repositorio:** https://github.com/SantiagoSkrobacki/MiniRed-2  
**Presentación:** https://santiagoskrobacki.github.io/MiniRed-2/

---

## 1. Fase 0 — Preparación de los datos

### 1.1 El universo elegido y su justificación

Se trabajó sobre `Fact_Ventas` de `MiniRed_DW`, con el catálogo completo (30 productos), las 7
sucursales y los dos años disponibles (2024-01-01 a 2025-12-31).

No se recortó por sucursal ni por trimestre por una razón concreta: el enunciado sugiere el
recorte asumiendo un catálogo de 4.200 artículos, pero la base instalada tiene **30 productos y
7 sucursales**. El espacio de itemsets es lo suficientemente chico como para que Apriori lo
recorra completo en segundos, de modo que recortar solo habría reducido la evidencia sin
ganar nada en tiempo de cómputo.

Sí se tomó una decisión de recorte, y fue necesaria:

> **Se excluyeron los tickets con un solo producto distinto: 152.944 de 220.465, el 69 % del
> total.** Una transacción con un único ítem no puede generar ninguna regla de asociación —no
> hay con qué asociar el producto— pero sí engrosa el denominador `N` y hunde artificialmente
> el soporte de todas las reglas. Conservarlos habría dividido todos los soportes por 3,3 sin
> aportar una sola co-ocurrencia.

### 1.2 Una corrección al enunciado

El enunciado indica armar la consulta agrupando por `IdVenta`, "el ticket". En `MiniRed_DW`
esa columna es la **clave primaria de la línea de detalle**; el ticket es `IdTicket`. Agrupando
como indica el texto, cada canasta habría contenido exactamente un producto y Apriori no
habría devuelto ninguna regla. Se verificó el esquema de la tabla antes de escribir la consulta
y se agrupó por `IdTicket`.

### 1.3 La transformación de grano

`Fact_Ventas` está en grano de línea. Apriori necesita grano de canasta. El ticket
`2024010101298` ilustra la transformación completa:

**Origen — grano de línea (3 filas):**

| IdVenta | IdTicket | Producto | Cantidad | Importe |
|---|---|---|---|---|
| 101.599 | 2024010101298 | Helado Crema 1L | 6 | $31.200 |
| 224.034 | 2024010101298 | Palitos Helados x6 | 6 | $18.600 |
| 265.822 | 2024010101298 | Detergente 750ml | 4 | $7.560 |

**Intermedio — grano de canasta (1 fila):**

`2024010101298 → Helado Crema 1L + Palitos Helados x6 + Detergente 750ml`

**Destino — matriz transaccional para Weka (1 fila, 30 columnas):**

| Helado | Palitos | Detergente | Leche | Gaseosa | … |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 0 | 0 | … |

En el paso final se descartan `Cantidad`, `ImporteTotal`, `IdCajero` y `IdMedioPago`: a un
algoritmo de asociación solo le importa la presencia del ítem, no cuántas unidades ni a qué
precio. También se descarta `IdTicket`, que solo sirvió para agrupar.

### 1.4 Volumen de la muestra final

| Métrica | Valor |
|---|---|
| Líneas en `Fact_Ventas` | 315.969 |
| Tickets totales | 220.465 |
| Tickets descartados (1 solo ítem) | 152.944 (69 %) |
| **Transacciones analizadas** | **67.521** |
| **Ítems distintos** | **30** |
| Pares ticket-producto | 157.971 |
| Promedio de ítems por ticket | 2,34 |

> **[CAPTURA 1]** — Extracto de la matriz transaccional: las primeras filas del archivo
> `minired_canasta.arff` mostrando la cabecera con los 30 `@attribute` y las filas de 0 y 1.

### 1.5 Los tres errores de siempre

| Error | Cómo se evitó |
|---|---|
| Atributo numérico sin discretizar | Los 30 atributos se declararon nominales `{0,1}` al generar el `.arff`. No hizo falta aplicar `NumericToNominal`. |
| El identificador de ticket como atributo | `IdTicket` no figura en el archivo: se usó para agrupar y se descartó. |
| El soporte por defecto demasiado alto | El default de Weka (0,1) no devuelve nada útil sobre esta matriz. Se corrió con 0,05 y con 0,01. |

---

## 2. Fase 1 — Aplicación del algoritmo

### 2.1 Configuración

Se usó Weka 3.8.7, `Explorer → Associate → Apriori`, con `treatZeroAsMissing = True`. Este
parámetro es indispensable: sin él, Apriori interpreta el `0` como un valor más y genera reglas
sobre la **ausencia** de productos ("quien no lleva X, no lleva Y"), que son ciertas y
completamente inútiles.

### 2.2 Comparación de las dos corridas

| | Corrida 1 | Corrida 2 |
|---|---|---|
| Soporte mínimo | 0,05 | 0,01 |
| Instancias mínimas | 3.376 | 675 |
| Confianza mínima | 0,5 | 0,5 |
| Ciclos ejecutados | 19 | 99 |
| Itemsets frecuentes L(1) | 26 | 29 |
| Itemsets frecuentes L(2) | 4 | 57 |
| **Reglas obtenidas** | **8** | **53** |
| Tiempo | 0,81 s | 3,70 s |

**Bajar el soporte de 0,05 a 0,01 multiplicó las reglas por 6,6**, y los itemsets de tamaño 2
por 14. Esto ocurre con un catálogo de apenas 30 productos; en una cadena real con 4.200
artículos, el mismo descenso produce decenas de miles de reglas. Es exactamente el problema de
"qué hacer con 40.000 reglas": el algoritmo no discrimina, solo cuenta.

> **[CAPTURA 2]** — Weka, corrida 1: soporte 0,05, 8 reglas.
>
> **[CAPTURA 3]** — Weka, corrida 2: soporte 0,01, 53 reglas.

### 2.3 Verificación manual de tres reglas

Se recalcularon tres reglas con las definiciones, mediante consultas SQL directas sobre
`MiniRed_DW`. Es un camino **independiente** del de Weka: uno cuenta sobre la base relacional,
el otro sobre el archivo `.arff`.

Fórmulas empleadas, con `N = 67.521`:

```
soporte(A,B)   = n(A y B) / N
confianza(A→B) = n(A y B) / n(A)
lift(A→B)      = confianza(A→B) / ( n(B) / N )
```

**Regla 1 — Detergente 750ml → Palitos Helados x6**

```
n(A) = 6.348     n(B) = 6.822     n(A y B) = 4.778
soporte   = 4.778 / 67.521 = 0,0708
confianza = 4.778 / 6.348  = 0,7527
base(B)   = 6.822 / 67.521 = 0,1010
lift      = 0,7527 / 0,1010 = 7,45
```

**Regla 2 — Mermelada Durazno 390g → Caramelos Surtidos 100g**

```
n(A) = 5.466     n(B) = 5.886     n(A y B) = 4.023
soporte   = 4.023 / 67.521 = 0,0596
confianza = 4.023 / 5.466  = 0,7360
base(B)   = 5.886 / 67.521 = 0,0872
lift      = 0,7360 / 0,0872 = 8,44
```

**Regla 3 — Gaseosa Lima-Limón 2.25L → Cerveza Negra 473ml**

```
n(A) = 2.297     n(B) = 2.494     n(A y B) = 1.210
soporte   = 1.210 / 67.521 = 0,0179
confianza = 1.210 / 2.297  = 0,5268
base(B)   = 2.494 / 67.521 = 0,0369
lift      = 0,5268 / 0,0369 = 14,26
```

**Contraste con Weka:**

| Regla | Conf. calculada | Conf. Weka | Lift calculado | Lift Weka | |
|---|---|---|---|---|---|
| Detergente → Palitos | 0,7527 | 0,75 | 7,450 | 7,45 | Coincide |
| Mermelada → Caramelos | 0,7360 | 0,74 | 8,443 | 8,44 | Coincide |
| Gaseosa L-L → Cerveza | 0,5268 | 0,53 | 14,262 | 14,26 | Coincide |

Las diferencias son únicamente de redondeo: Weka muestra dos decimales. **La coincidencia
confirma que la matriz transaccional se construyó correctamente**; si el `.arff` hubiera
incluido el identificador de ticket, o si el agrupamiento hubiera estado mal, los valores no
habrían coincidido y el error habría pasado inadvertido hasta la exposición.

### 2.4 Plus — FP-Growth

| Algoritmo | Tiempo | Estrategia | Reglas |
|---|---|---|---|
| Apriori | 3,29 s | Genera candidatos por nivel y recorre los datos en cada ciclo (99 ciclos) | — |
| FP-Growth | **0,48 s** | Comprime los datos en un árbol de prefijos y extrae los patrones sin generar candidatos | Idénticas |

FP-Growth resultó **6,9 veces más rápido** y devolvió exactamente las mismas reglas con los
mismos valores. La diferencia es de eficiencia algorítmica, no de resultado, que es lo
esperable: ambos calculan lo mismo por caminos distintos.

---

## 3. Fase 2 — Curaduría de las reglas

### 3.1 Aplicación de los seis pasos

**Paso 1 — Descartar lo trivial.** No se encontraron reglas triviales evidentes; con 30
productos genéricos no hay pares tan obvios como "pan → manteca".

**Paso 2 — Descartar lo redundante.** Las ocho reglas de mayor lift resultaron ser
combinaciones de tres y cuatro ítems dentro de dos clusters ya representados por pares simples.
`Hamburguesas + Detergente → Palitos + Lavandina` alcanza lift 36,87, pero no aporta nada sobre
los pares que la componen: el lift altísimo es un artefacto de combinar correlaciones ya
conocidas. Se descartaron todas las reglas de más de dos ítems.

También se unificaron las reglas gemelas: `A→B` y `B→A` comparten soporte y lift, y solo
difieren en la confianza. Presentarlas por separado sería contar dos veces el mismo hallazgo.

**Paso 3 — Ordenar por lift.** Se reordenó la lista completa por lift descendente. Durante
este paso se detectó un problema de configuración: al rankear por lift (`-T 1`) con pocas
reglas solicitadas, Weka detiene la búsqueda al alcanzar esa cantidad y se queda en un soporte
alto. La regla de mayor lift del dataset (14,26, soporte 0,018) **quedaba fuera del ranking**
hasta que se forzó el piso con `-M 0.01 -U 0.05 -N 200`. Un ranking por lift no sirve si el
piso de soporte excluye la regla de la búsqueda.

**Paso 4 — Mecanismo plausible.** Se exigió a cada regla una explicación de negocio. Este
paso eliminó las reglas que cruzan categorías sin relación de uso: Congelados con Limpieza,
Lácteos con Limpieza.

**Paso 5 — Accionabilidad.** Se conservaron las reglas que permiten una decisión concreta de
góndola, promoción o surtido.

**Paso 6 — Validar en otro período.** Se recalculó el lift por separado sobre 2024 y 2025,
usando las matrices `minired_canasta_2024.arff` y `minired_canasta_2025.arff`.

### 3.2 El hallazgo metodológico

Los pasos 4 y 6 se aplicaron de forma independiente: primero se clasificaron las reglas según
si tenían explicación de negocio —criterio puramente cualitativo— y recién después se
recalcularon los lift por año.

**Los dos criterios señalaron el mismo conjunto de reglas.**

| Grupo | Ejemplo | Lift total | 2024 | 2025 | Variación |
|---|---|---|---|---|---|
| Con mecanismo | Gaseosa Lima-Limón + Cerveza Negra | 14,26 | 14,08 | 14,45 | +2,6 % |
| Con mecanismo | Agua Saborizada + Jugo Naranja | 5,47 | 5,40 | 5,53 | +2,5 % |
| Sin mecanismo | Palitos Helados + Detergente | 7,45 | 10,31 | 5,86 | −43,2 % |
| Sin mecanismo | Manteca + Lavandina | 5,57 | 8,13 | 4,07 | −49,9 % |
| Sin mecanismo | Palitos Helados + Hamburguesas | 3,17 | 0,08 | 4,52 | +5.217 % |

Las once reglas con mecanismo plausible varían **menos del 12 %** entre años. Ninguna de las
implausibles baja del 29 %. El juicio de negocio y la evidencia estadística convergieron.

Las variaciones extremas merecen una observación aparte. `Palitos + Hamburguesas` pasa de lift
0,08 a 4,52, y `Detergente + Lavandina` de 0,18 a 4,44. **Un lift menor a 1 significa que esos
productos se compraban separados.** Un salto de esa magnitud no describe un cambio de hábito de
los clientes: indica un cambio estructural en la generación de los datos entre un año y el
otro. Se excluyeron del análisis en lugar de presentarlos como un descubrimiento comercial.

### 3.3 Las siete reglas finales

| # | Regla | Soporte | Confianza | Lift | Δ 24→25 | Recomendación de negocio |
|---|---|---|---|---|---|---|
| 1 | Gaseosa Lima-Limón ↔ Cerveza Negra | 0,0179 | 52,7 % | 14,26 | +2,6 % | Punta de góndola de fin de semana con ambas juntas. Es el combo de previa. |
| 2 | Agua Mineral 2L ↔ Yerba Mate 500g | 0,0113 | 45,0 % | 8,60 | +5,1 % | Ubicar el agua sin gas junto a la yerba, no en la heladera de bebidas. |
| 3 | Agua Mineral 2L ↔ Cerveza Negra | 0,0108 | 29,3 % | 5,61 | +5,9 % | Carga de bebidas en un mismo viaje: conviene ofrecer pack mixto. |
| 4 | Agua Saborizada ↔ Cerveza Rubia | 0,0437 | 49,0 % | 5,54 | +2,6 % | La combinación de bebidas más frecuente del catálogo: exhibir contiguas. |
| 5 | Gaseosa Cola ↔ Yerba Mate 1kg | 0,0325 | 63,5 % | 5,49 | +2,8 % | Compra de reposición del hogar: promoción cruzada en el ticket. |
| 6 | Agua Saborizada ↔ Jugo Naranja | 0,0355 | 48,4 % | 5,47 | +2,5 % | Misma decisión de compra (sin alcohol). Exhibir contiguas. |
| 7 | Galletitas Dulces ↔ Leche Entera | 0,0915 | 64,1 % | 4,26 | +11,2 % | El mayor soporte de todas (9,2 %). Desayuno y merienda: nunca liquidar ambas a la vez. |

### 3.4 Las reglas descartadas

| Regla | Lift | Paso | Motivo |
|---|---|---|---|
| Hamburguesas + Detergente → Palitos + Lavandina | 36,87 | 2 | Combinación de dos pares ya presentes: no aporta información nueva. |
| Galletitas + Caramelos → Mermelada + Leche | 33,79 | 2 | Cuatro ítems del mismo cluster; el lift es artefacto de combinar correlaciones. |
| Agua Saborizada + Yerba → Cerveza Rubia | 11,20 | 4 | Confianza exactamente 1,00 sobre 731 tickets: demasiado perfecto para ser real. |
| Mermelada ↔ Caramelos | 8,44 | 6 | Mecanismo débil (ambos dulces) y caída del 34 % entre años. |
| Palitos Helados ↔ Detergente | 7,45 | 4 | Congelados con Limpieza: sin explicación posible. Además cae 43 %. |
| Dulce de Leche ↔ Jabón en Polvo | 6,98 | 4 | Lácteos con Limpieza. Salta 61 % entre años. |
| Hamburguesas ↔ Lavandina | 5,60 | 4 | Congelados con Limpieza nuevamente. |
| Manteca ↔ Lavandina | 5,57 | 6 | Cae a la mitad (−50 %). |
| Aceite Girasol ↔ Yogur Bebible | 5,07 | 4 | Sin relación de uso ni de ocasión de consumo. |
| Alfajor ↔ Galletitas Dulces | 1,70 | 3 | Confianza 25,6 % que parece aceptable, pero las galletitas están en el 15,1 % de los tickets igual. |

### 3.5 El descarte más relevante

`Palitos Helados → Detergente` tiene lift **7,45**, el cuarto más alto de todo el dataset, y no
existe ninguna explicación de por qué alguien compraría helado junto con detergente. Si el
criterio hubiera sido únicamente "ordenar por lift y quedarse con las primeras", esta regla
habría entrado a la presentación y MiniRed habría terminado ubicando detergente junto a la
heladera de helados.

**Un número alto no es un hallazgo.** El valor del paso 4 se mide precisamente en las reglas
que elimina pese a tener buenas métricas.

---

## 4. Fase 3 — Rol de la inteligencia artificial

Se utilizó **Claude (Anthropic)** como asistente.

**Qué generó la IA:** la consulta SQL de la matriz transaccional, el script de Python que
produce el archivo `.arff`, las consultas de verificación de soporte/confianza/lift, los
comandos de Weka y el diseño de la presentación web.

**Qué hubo que corregir:**

1. **El agrupamiento por `IdVenta`.** Seguir el enunciado al pie producía canastas de un solo
   ítem. Se detectó revisando el esquema real de la tabla.
2. **El ranking por lift truncado.** Weka detenía la búsqueda en un soporte alto y ocultaba la
   regla más fuerte del dataset.
3. **Un pipeline de PowerShell** que truncó una salida de Weka y la dejó incompleta.

**Dónde confiar ciegamente habría sido un riesgo.** No en el código —que falla de forma
ruidosa— sino en los **números**. Si se hubieran solicitado los valores de soporte, confianza y
lift a un modelo generativo, habría devuelto cifras perfectamente plausibles y no existía forma
de detectarlo: nadie observa un lift de 7,45 y sospecha.

Existe un segundo riesgo, más sutil: la **interpretación**. Consultada sobre qué mecanismo de
negocio explica una regla, una IA generativa encuentra una justificación convincente para
cualquier par de productos, incluso para helado con detergente. Los modelos generativos son
eficaces produciendo explicaciones plausibles, que es exactamente lo contrario de lo que
requiere el paso 4 de la curaduría.

Por eso el trabajo se apoyó en **dos cálculos independientes** —SQL contra la base y Weka sobre
el `.arff`— que coinciden hasta el segundo decimal, y el juicio sobre el mecanismo se emitió
antes de consultar los datos de estabilidad. **Ningún valor de soporte, confianza o lift fue
estimado.**

---

## 5. Conclusiones

1. **La preparación de los datos consumió aproximadamente el 80 % del esfuerzo.** Las dos
   corridas de Apriori sumaron 4,5 segundos. La desproporción se explica porque el algoritmo
   resuelve un problema cerrado, mientras que la preparación concentra todas las decisiones sin
   respuesta única: el grano, el recorte, qué hacer con los tickets de un solo ítem.

2. **Leer la fuente antes de modelarla evitó un error que habría invalidado el trabajo.** El
   enunciado indicaba agrupar por una columna que no es el ticket.

3. **El algoritmo encuentra correlaciones; el analista encuentra hallazgos.** De 53 reglas
   estadísticamente ciertas sobrevivieron 7. Las 46 restantes eran redundantes, implausibles o
   inestables — y todas tenían métricas válidas.

4. **El criterio de negocio resultó ser un predictor de la validez estadística.** Que las
   reglas con explicación plausible sean exactamente las que se sostienen entre 2024 y 2025 no
   estaba previsto, y es el resultado que da sustento a toda la curaduría.

---

## Anexos

- **Repositorio completo:** https://github.com/SantiagoSkrobacki/MiniRed-2
- **Presentación interactiva:** https://santiagoskrobacki.github.io/MiniRed-2/
- **Salidas crudas de Weka:** carpeta `weka/` del repositorio (7 corridas)
- **Consulta SQL documentada:** `sql/01_matriz_transaccional.sql`
- **Reflexiones individuales:** se adjuntan por separado, una por integrante

---

# Fase 4 — Reflexiones individuales

# Reflexión individual

**Santiago Skrobacki**

**Preparación de datos y ejecución del algoritmo.** Las dos corridas de Apriori tardaron 0,81 y
3,70 segundos: cuatro segundos y medio en total. Todo lo demás —entender el grano de
`Fact_Ventas`, escribir la consulta, decidir qué tickets entraban, generar el archivo para Weka
y verificar que los números cerraran— se llevó prácticamente todo el tiempo que le dedicamos.
La Unidad 4 dice que la preparación consume la mayor parte del esfuerzo y uno lo lee y asiente;
medirlo fue distinto. Entendí *por qué* pasa: el algoritmo resuelve un problema cerrado, con
una respuesta única, y por eso se automatiza. La preparación es donde están las preguntas que
no tienen respuesta correcta, y ninguna de las nuestras venía resuelta en el enunciado.

**La advertencia que estuvimos cerca de cometer.** Dar por buena una suposición sobre los datos
sin verificarla contra la base. El enunciado indicaba agrupar por `IdVenta`, "el ticket", pero
en `MiniRed_DW` esa columna es la PK de la línea: el ticket es `IdTicket`. Siguiéndolo al pie,
cada canasta habría tenido un solo producto y Apriori no habría devuelto nada. Lo encontramos
revisando las columnas antes de escribir la consulta, casi de casualidad; si no, habríamos
pasado horas buscando por qué "no hay patrones" cuando el problema estaba en nuestro `GROUP BY`.
Me llevo que la fuente gana sobre lo que uno cree de la fuente, incluso cuando eso viene escrito
en la consigna.

**El rol de la IA.** El riesgo no estaba en el código —el código falla ruidosamente— sino en los
números. Si le hubiéramos pedido el soporte y el lift en vez de calcularlos, habría devuelto
cifras creíbles y no teníamos forma de detectarlo: nadie mira un lift de 7,45 y sospecha. Por
eso los calculamos por dos caminos separados, SQL contra la base y Weka sobre el `.arff`, y
coincidieron al segundo decimal. Un número que no se puede reproducir por dos vías no entra al
informe.

---

# Reflexión individual

**(Nombre del segundo integrante)**

**Preparación de datos y ejecución del algoritmo.** Calculo que entre el 80 y el 90 % del tiempo
se fue en la Fase 0. Apriori procesó 67.521 transacciones en 3,70 segundos y FP-Growth en 0,48;
elegir *cuáles* 67.521 transacciones nos llevó una tarde. Lo que me sorprendió es que la
decisión más importante del trabajo no fue técnica sino de criterio: el 69 % de los tickets de
MiniRed tiene un solo producto, 152.944 de 220.465. Esos tickets no pueden generar ninguna
regla, pero engordan el denominador y hunden todos los soportes. Sacarlos no lo decide ninguna
herramienta. Eso es lo que la Unidad 4 quiere decir cuando habla de que la preparación define el
proyecto: no es la etapa más larga, es donde se toman las decisiones que después nadie revisa.

**La advertencia que estuvimos cerca de cometer.** Confundir una correlación fuerte con un
hallazgo. Nuestra regla `Palitos Helados → Detergente` tiene lift 7,45, el cuarto más alto del
dataset, y no hay ninguna explicación de por qué alguien compraría helado con detergente. Si
ordenábamos por lift y presentábamos las primeras, entraba sin discusión. Lo evitamos aplicando
el paso 4 —exigirle a cada regla un mecanismo de negocio— antes que el orden por lift, y después
recalculando el lift por año: las reglas con explicación varían menos del 12 %, las implausibles
nunca menos del 29 %. Peor todavía, hay pares que pasan de lift 0,08 a 4,52 entre 2024 y 2025;
eso no es un cambio de hábito sino un cambio en cómo se generaron los datos, y las métricas lo
respaldaban igual.

**El rol de la IA.** Confiar ciegamente hubiera sido riesgoso en la interpretación. Si le
preguntábamos qué mecanismo explica una regla, habría encontrado una justificación convincente
para cualquier par de productos, incluso para helado con detergente. Los modelos generativos son
muy buenos produciendo explicaciones plausibles, que es lo contrario de lo que necesita un paso
que existe justamente para filtrar lo que suena razonable y no lo es. Por eso el juicio sobre el
mecanismo lo tomamos primero nosotros y recién después lo contrastamos contra la estabilidad
entre años, que sale de la base y no de una opinión.

---
