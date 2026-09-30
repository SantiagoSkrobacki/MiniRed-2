# Fase 4 — Conexión con RA4
## Reflexiones individuales

---

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

## Datos de respaldo

| Dato | Valor |
|---|---|
| Transacciones analizadas | 67.521 |
| Tickets descartados (1 solo ítem) | 152.944 de 220.465 (69 %) |
| Ítems distintos | 30 |
| Promedio de ítems por ticket | 2,34 |
| Apriori, soporte 0,05 | 8 reglas · 0,81 s |
| Apriori, soporte 0,01 | 53 reglas · 3,70 s |
| FP-Growth, soporte 0,01 | mismas reglas · 0,48 s |
| Variación de lift, reglas con mecanismo | menos del 12 % |
| Variación de lift, reglas sin mecanismo | entre −50 % y +5.217 % |
