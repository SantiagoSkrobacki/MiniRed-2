/* ============================================================================
   MiniRed_DW - Fase 0: de la tabla de hechos a la matriz transaccional
   Actividad Clase 8 - Cazadores de Patrones
   ----------------------------------------------------------------------------
   RECORTE ELEGIDO Y SU JUSTIFICACION
   ----------------------------------------------------------------------------
   1) Se trabaja con el catalogo completo (30 productos) y las 7 sucursales,
      sobre los dos anios disponibles (2024-2025). El enunciado sugiere recortar
      porque asume 4.200 articulos; la base instalada tiene 30, de modo que el
      espacio de itemsets es chico y Apriori corre sin problemas de volumen.

   2) Se excluyen los tickets con UN SOLO producto distinto. Son 152.944 de
      220.465 (69%). Una transaccion de un solo item no puede generar ninguna
      regla de asociacion, pero si infla el denominador y hunde artificialmente
      todos los soportes. Quedan 67.521 transacciones utiles.

   3) Para el paso 6 de la curaduria (validar en otro periodo) se generan ademas
      dos matrices separadas, 2024 y 2025, con el mismo criterio.
   ----------------------------------------------------------------------------
   OJO: el enunciado dice "agrupar por IdVenta (el ticket)". En MiniRed_DW
   IdVenta es la PK de la LINEA; el ticket es IdTicket. Agrupar por IdVenta
   daria una canasta de un item por fila y Apriori no encontraria nada.
   ============================================================================ */

USE MiniRed_DW;
GO

/* ---------------------------------------------------------------------------
   PASO 1 - Tickets con su lista de productos (grano: ticket x producto)
   DISTINCT porque un mismo producto puede aparecer en dos lineas del ticket.
   --------------------------------------------------------------------------- */
IF OBJECT_ID('tempdb..#Canasta') IS NOT NULL DROP TABLE #Canasta;

WITH LineasUnicas AS (
    SELECT DISTINCT
           f.IdTicket,
           f.IdProducto,
           t.Anio
    FROM dbo.Fact_Ventas   f
    JOIN dbo.Dim_Tiempo    t ON t.IdTiempo = f.IdTiempo
),
TicketsUtiles AS (
    SELECT IdTicket
    FROM LineasUnicas
    GROUP BY IdTicket
    HAVING COUNT(*) >= 2          -- descarta los tickets de un solo item
)
SELECT l.IdTicket, l.IdProducto, l.Anio
INTO   #Canasta
FROM   LineasUnicas l
JOIN   TicketsUtiles u ON u.IdTicket = l.IdTicket;

/* ---------------------------------------------------------------------------
   PASO 2 - Volumen de la muestra (va en el informe)
   --------------------------------------------------------------------------- */
SELECT transacciones     = COUNT(DISTINCT IdTicket),
       items_distintos   = COUNT(DISTINCT IdProducto),
       lineas            = COUNT(*),
       items_por_ticket  = CAST(COUNT(*) * 1.0 / COUNT(DISTINCT IdTicket) AS decimal(5,2))
FROM #Canasta;

/* ---------------------------------------------------------------------------
   PASO 3 - Vista legible de la canasta (una fila por ticket)
   Sirve para la captura del informe: "asi quedo la matriz".
   --------------------------------------------------------------------------- */
SELECT TOP 20
       c.IdTicket,
       productos = STRING_AGG(p.NombreProducto, ' + ') WITHIN GROUP (ORDER BY p.NombreProducto)
FROM #Canasta c
JOIN dbo.Dim_Producto p ON p.IdProducto = c.IdProducto
GROUP BY c.IdTicket
ORDER BY c.IdTicket;

/* ---------------------------------------------------------------------------
   PASO 4 - VERIFICACION MANUAL (Fase 1)
   Soporte, confianza y lift de todos los pares, calculados con la definicion.
   Estos son los numeros contra los que hay que comparar la salida de Weka.

       soporte(A,B)   = n(A y B) / N
       confianza(A>B) = n(A y B) / n(A)
       lift(A>B)      = confianza(A>B) / ( n(B) / N )
   --------------------------------------------------------------------------- */
WITH N AS (
    SELECT n = CAST(COUNT(DISTINCT IdTicket) AS float) FROM #Canasta
),
Frecuencia AS (
    SELECT IdProducto, c = CAST(COUNT(*) AS float)
    FROM #Canasta GROUP BY IdProducto
),
Pares AS (
    SELECT a.IdProducto AS A, b.IdProducto AS B, ab = CAST(COUNT(*) AS float)
    FROM #Canasta a
    JOIN #Canasta b ON b.IdTicket = a.IdTicket
                   AND b.IdProducto <> a.IdProducto
    GROUP BY a.IdProducto, b.IdProducto
)
SELECT  antecedente = pa.NombreProducto,
        consecuente = pb.NombreProducto,
        n_A   = CAST(fa.c AS int),
        n_B   = CAST(fb.c AS int),
        n_AB  = CAST(pr.ab AS int),
        N     = CAST(N.n  AS int),
        soporte   = CAST(pr.ab / N.n        AS decimal(6,4)),
        confianza = CAST(pr.ab / fa.c       AS decimal(6,4)),
        lift      = CAST((pr.ab / fa.c) / (fb.c / N.n) AS decimal(8,3))
FROM Pares pr
CROSS JOIN N
JOIN Frecuencia fa ON fa.IdProducto = pr.A
JOIN Frecuencia fb ON fb.IdProducto = pr.B
JOIN dbo.Dim_Producto pa ON pa.IdProducto = pr.A
JOIN dbo.Dim_Producto pb ON pb.IdProducto = pr.B
WHERE pr.ab >= 100
ORDER BY lift DESC;

/* ---------------------------------------------------------------------------
   PASO 5 - Mismo calculo partido por anio (paso 6 de la curaduria:
   "validar la regla en otro periodo"). Una regla real se sostiene en ambos.
   --------------------------------------------------------------------------- */
WITH N AS (
    SELECT Anio, n = CAST(COUNT(DISTINCT IdTicket) AS float)
    FROM #Canasta GROUP BY Anio
),
Frecuencia AS (
    SELECT Anio, IdProducto, c = CAST(COUNT(*) AS float)
    FROM #Canasta GROUP BY Anio, IdProducto
),
Pares AS (
    SELECT a.Anio, a.IdProducto AS A, b.IdProducto AS B, ab = CAST(COUNT(*) AS float)
    FROM #Canasta a
    JOIN #Canasta b ON b.IdTicket = a.IdTicket
                   AND b.IdProducto <> a.IdProducto
    GROUP BY a.Anio, a.IdProducto, b.IdProducto
)
SELECT  anio        = pr.Anio,
        antecedente = pa.NombreProducto,
        consecuente = pb.NombreProducto,
        soporte   = CAST(pr.ab / N.n  AS decimal(6,4)),
        confianza = CAST(pr.ab / fa.c AS decimal(6,4)),
        lift      = CAST((pr.ab / fa.c) / (fb.c / N.n) AS decimal(8,3))
FROM Pares pr
JOIN N          ON N.Anio  = pr.Anio
JOIN Frecuencia fa ON fa.Anio = pr.Anio AND fa.IdProducto = pr.A
JOIN Frecuencia fb ON fb.Anio = pr.Anio AND fb.IdProducto = pr.B
JOIN dbo.Dim_Producto pa ON pa.IdProducto = pr.A
JOIN dbo.Dim_Producto pb ON pb.IdProducto = pr.B
WHERE pr.ab >= 50
ORDER BY antecedente, consecuente, anio;
