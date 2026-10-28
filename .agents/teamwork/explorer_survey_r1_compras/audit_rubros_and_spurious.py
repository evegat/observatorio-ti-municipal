import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
parquet_path = "D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet"

print("=================================================================")
print("ANÁLISIS EXHAUSTIVO DE RUBROS Y CÓDIGOS ONU EN CATASTRO MUNICIPAL")
print("=================================================================")

# 1. Total por Rubro Nivel 1
rubros_all = con.execute(f"""
    SELECT 
        coalesce(rubro_nivel1, 'SIN_RUBRO') as rubro,
        count(*) as total_items,
        count(distinct codigo_orden) as total_ocs,
        round(sum(monto_linea) / 1e9, 3) as monto_mm_clp,
        round(sum(monto_linea) * 100.0 / sum(sum(monto_linea)) over(), 2) as pct_monto
    FROM read_parquet('{parquet_path}')
    GROUP BY coalesce(rubro_nivel1, 'SIN_RUBRO')
    ORDER BY monto_mm_clp DESC
""").df()

print("\n--- TODOS LOS RUBROS NIVEL 1 ORDENADOS POR MONTO (MM CLP = Miles de millones) ---")
print(rubros_all.to_string())

# 2. Rubros no-tecnológicos evidentes
spurious_rubros = [
    'Artículos para estructuras, obras y construcciones',
    'Servicios de Viajes, alimentación, alojamiento y entretenimiento',
    'Servicios de construcción y mantenimiento',
    'Artículos para plantas y animales',
    'Ropa, maletas y productos de aseo personal',
    'Muebles y mobiliario',
    'Equipamiento y suministros médicos',
    'Herramientas y maquinaria en general',
    'Instrumentos musicales, juegos, juguetes, artesanías y materiales educativos',
    'Productos de papel',
    'Muebles, accesorios, electrodomésticos y productos electrónicos',
    'Medicamentos y productos farmacéuticos',
    'Equipos, suministros y accesorios deportivos y recreativos',
    'Artículos de fabricación y producción',
    'Vehículos y equipamiento en general'
]

print("\n--- CÓDIGOS ONU DE MAYOR CUANTÍA DENTRO DE RUBROS SOSPECHOSOS ---")
onu_susp = con.execute(f"""
    SELECT 
        codigo_producto_onu,
        nombre_producto_generico,
        rubro_nivel1,
        count(distinct codigo_orden) as ocs,
        round(sum(monto_linea) / 1e9, 3) as monto_mm_clp
    FROM read_parquet('{parquet_path}')
    WHERE rubro_nivel1 IN ({', '.join(f"'{r}'" for r in spurious_rubros)})
    GROUP BY codigo_producto_onu, nombre_producto_generico, rubro_nivel1
    HAVING sum(monto_linea) > 500000000
    ORDER BY sum(monto_linea) DESC
""").df()
print(onu_susp.to_string())
