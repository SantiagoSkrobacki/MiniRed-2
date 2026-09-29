<#
    Paso 1 de 3 — Exporta las canastas desde MiniRed_DW a data/raw/

    Uso (parado en la raiz del repo):
        powershell -ExecutionPolicy Bypass -File scripts\00_exportar_desde_sqlserver.ps1

    Requiere sqlcmd y una instancia de SQL Server con MiniRed_DW.
    Salida: data/raw/productos.txt y data/raw/canasta.txt (separados por |)
#>
param(
    [string]$Servidor = "localhost",
    [string]$BaseDatos = "MiniRed_DW"
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$salida = Join-Path $raiz "data\raw"
New-Item -ItemType Directory -Force -Path $salida | Out-Null

Write-Host "Exportando desde $Servidor/$BaseDatos ..."

# --- catalogo de productos -------------------------------------------------
$qProductos = @"
SET NOCOUNT ON;
USE $BaseDatos;
SELECT IdProducto, NombreProducto, Categoria, Rubro
FROM dbo.Dim_Producto
ORDER BY IdProducto;
"@
sqlcmd -S $Servidor -E -W -h -1 -s"|" -Q $qProductos -o "$salida\productos.txt"

# --- canastas: solo tickets con 2 o mas productos distintos ----------------
$qCanasta = @"
SET NOCOUNT ON;
USE $BaseDatos;
WITH LineasUnicas AS (
    SELECT DISTINCT f.IdTicket, f.IdProducto, t.Anio
    FROM dbo.Fact_Ventas f
    JOIN dbo.Dim_Tiempo  t ON t.IdTiempo = f.IdTiempo
),
TicketsUtiles AS (
    SELECT IdTicket FROM LineasUnicas
    GROUP BY IdTicket HAVING COUNT(*) >= 2
)
SELECT l.IdTicket, l.IdProducto, l.Anio
FROM LineasUnicas l
JOIN TicketsUtiles u ON u.IdTicket = l.IdTicket
ORDER BY l.IdTicket;
"@
sqlcmd -S $Servidor -E -W -h -1 -s"|" -Q $qCanasta -o "$salida\canasta.txt"

foreach ($f in @("productos.txt","canasta.txt")) {
    $ruta = Join-Path $salida $f
    $n = (Get-Content $ruta | Measure-Object -Line).Lines
    Write-Host ("  {0,-16} {1,8} lineas" -f $f, $n)
}
Write-Host "Listo. Siguiente paso: python scripts\01_build_arff.py"
