# Fase 4 — Conexión con RA4
## Reflexiones individuales

> **Cómo usar este archivo.** Son dos borradores, uno por integrante, escritos sobre hechos
> reales de este trabajo. Están pensados como punto de partida, no como entrega final.
> Cada uno debería reemplazar los tramos marcados con `[...]` por su propia experiencia y
> ajustar el tono. Donde dice `[NOMBRE DE LA ADVERTENCIA]` va el nombre exacto que usó el
> profesor en la Clase 8 — no lo tenemos en el PDF de la Unidad 5 y no conviene inventarlo.

---

# Reflexión individual — Integrante 1

**[Nombre y apellido]**

### Preparación de datos contra ejecución del algoritmo

La desproporción fue tan grande que da un poco de vergüenza escribirla. Las dos corridas de
Apriori tardaron **0,81 y 3,70 segundos**: cuatro segundos y medio sumados. Todo lo demás
—entender el grano de `Fact_Ventas`, escribir la consulta que arma las canastas, decidir qué
tickets entraban, generar el `.arff` y verificar que los números cerraran— se llevó
prácticamente la totalidad del tiempo que le dedicamos.

Esto es exactamente lo que plantea la Unidad 4 cuando dice que la preparación consume la mayor
parte del esfuerzo de un proyecto de minería, pero leerlo en un apunte y medirlo con reloj son
dos cosas distintas. Lo que entendí es *por qué* pasa: el algoritmo resuelve un problema
cerrado y bien definido, mientras que la preparación es donde están todas las decisiones que
no tienen una respuesta única. Ninguna de las nuestras —el recorte, el grano, qué hacer con
los tickets de un solo ítem— venía dada por el enunciado.

### La advertencia que estuvimos por cometer

`[NOMBRE DE LA ADVERTENCIA — la de confundir el dato con lo que uno supone del dato]`

El enunciado indicaba agrupar por `IdVenta`, "el ticket". En `MiniRed_DW` el `IdVenta` es la
clave primaria de la **línea**; el ticket es `IdTicket`. Si lo hubiéramos seguido al pie, cada
canasta habría tenido un solo producto y Apriori no habría devuelto absolutamente nada.

Lo que más me quedó no es el error en sí, sino que lo encontramos por casualidad, mirando las
columnas de la tabla antes de escribir la consulta. Si en vez de eso hubiéramos confiado en la
consigna, habríamos pasado horas buscando por qué "no hay patrones en los datos" cuando el
problema era nuestro. Lo evitamos consultando el esquema real en lugar de asumir que el
enunciado describía la base que teníamos instalada — y de paso descubrimos que tampoco
coincidía en la escala: habla de 4.200 artículos y 14 sucursales, y nuestra base tiene 30 y 7.

### El rol de la IA

Usamos la IA para escribir la consulta SQL, generar el archivo `.arff` y redactar buena parte
de la documentación. El riesgo no estaba en el código —ese falla ruidosamente o no falla— sino
en los **números**. Si le hubiéramos pedido los valores de soporte, confianza y lift, nos
habría dado cifras perfectamente plausibles y no teníamos forma de darnos cuenta: nadie mira
un lift de 7,45 y sospecha.

Por eso los calculamos por **dos caminos independientes**: una consulta SQL contra
`MiniRed_DW` aplicando las fórmulas a mano, y Weka sobre el `.arff`. Los dos coincidieron
hasta el segundo decimal. La regla que adoptamos fue simple: un número que no se puede
reproducir por dos vías no entra al informe.

`[Agregar acá algo propio: qué parte te costó más, o algo que hubieras hecho distinto.]`

---

# Reflexión individual — Integrante 2

**[Nombre y apellido]**

### Preparación de datos contra ejecución del algoritmo

Si tuviera que poner un número, diría que entre el 80 y el 90 % del tiempo se fue en la Fase 0.
El dato que mejor lo ilustra: Apriori corrió en **3,70 segundos** sobre 67.521 transacciones,
y FP-Growth en **0,48**. Elegir *qué* 67.521 transacciones, en cambio, fue una discusión larga.

Lo que me llamó la atención es que la decisión más importante de todo el trabajo no fue técnica
sino de criterio: el **69 % de los tickets de MiniRed tiene un solo producto**. Son 152.944 de
220.465. Esos tickets no pueden generar ninguna regla —no hay con qué asociar el único ítem—
pero sí engordan el denominador y hunden todos los soportes. Decidir excluirlos no lo hace
ningún algoritmo; lo tuvimos que razonar nosotros, y de eso dependía que el resto del análisis
tuviera sentido o no. Eso es, creo, lo que la Unidad 4 quiere decir con que la preparación es
donde se define el proyecto.

### La advertencia que estuvimos por cometer

`[NOMBRE DE LA ADVERTENCIA — la de tomar una correlación fuerte como si fuera un hallazgo]`

Nuestra regla `Palitos Helados → Detergente` tiene un lift de **7,45**, el cuarto más alto de
todo el dataset. Si hubiéramos ordenado por lift y presentado las primeras, entraba sin
discusión. Y no existe ninguna explicación de por qué alguien compraría helado junto con
detergente.

Lo que hicimos para no caer fue aplicar el paso 4 de la curaduría antes que el orden por lift:
exigirle a cada regla una explicación de negocio. Después, para confirmarlo, recalculamos el
lift por separado en 2024 y 2025. El resultado fue el que más me sorprendió del trabajo: las
reglas con explicación plausible varían **menos del 12 %** entre años, y ninguna de las
implausibles baja del 29 %. Dos criterios independientes, uno cualitativo y otro estadístico,
señalaron el mismo grupo.

Hubo un caso todavía peor: hay pares que pasan de lift **0,08 a 4,52** entre un año y otro. Un
lift menor a 1 significa que esos productos se compraban *separados*. Un salto así no es un
cambio de hábito de los clientes; es un cambio estructural en cómo se generaron los datos.
Presentarlo como descubrimiento comercial habría sido el error más grave que podíamos cometer.

### El rol de la IA

La IA nos generó el código y la redacción, y eso funcionó bien. Donde confiar ciegamente
hubiera sido un riesgo real es en la **interpretación**: si le hubiéramos preguntado "¿qué
mecanismo de negocio explica esta regla?", habría encontrado una justificación convincente
para cualquier par de productos, incluso para helado con detergente. Los modelos generativos
son buenos inventando explicaciones plausibles, y eso es justo lo contrario de lo que necesita
el paso 4.

Por eso el juicio sobre el mecanismo lo tomamos nosotros primero, y recién después lo
contrastamos contra la estabilidad entre años, que es un dato duro que sale de la base y no
de una opinión.

`[Agregar acá algo propio: qué parte te costó más, o algo que hubieras hecho distinto.]`

---

## Datos de respaldo (por si hace falta citarlos)

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
