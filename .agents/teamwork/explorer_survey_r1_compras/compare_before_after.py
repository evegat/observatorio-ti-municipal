import duckdb
import sys
sys.stdout.reconfigure(encoding='utf-8')

con = duckdb.connect()
from simulate_sanitized_basket import sanitization_sql

print("=================================================================")
print("COMPARATIVA DE INTEGRIDAD: ANTES VS DESPUÉS DEL SANEAMIENTO")
print("=================================================================")

con.execute(f"CREATE TEMP TABLE base_eval AS {sanitization_sql}")

# 1. Top 10 Proveedores Nacionales Antes
print("\n--- TOP 10 PROVEEDORES NACIONALES (ANTES DEL SANEAMIENTO) ---")
p_before = con.execute("""
    SELECT nombre_proveedor, count(distinct codigo_orden) as ocs, round(sum(monto_linea)/1e9, 2) as mm_clp
    FROM base_eval
    GROUP BY nombre_proveedor
    ORDER BY sum(monto_linea) DESC
    LIMIT 10
""").df()
print(p_before.to_string())

# 2. Top 10 Proveedores Nacionales Después
print("\n--- TOP 10 PROVEEDORES NACIONALES (DESPUÉS DEL SANEAMIENTO) ---")
p_after = con.execute("""
    SELECT nombre_proveedor, count(distinct codigo_orden) as ocs, round(sum(monto_linea)/1e9, 2) as mm_clp
    FROM base_eval
    WHERE es_tecnologico_valido AND NOT es_espurio_obvio
    GROUP BY nombre_proveedor
    ORDER BY sum(monto_linea) DESC
    LIMIT 10
""").df()
print(p_after.to_string())

# 3. Top 10 Contratos Nacionales Antes
print("\n--- TOP 10 CONTRATOS HISTÓRICOS NACIONALES (ANTES DEL SANEAMIENTO) ---")
c_before = con.execute("""
    SELECT codigo_orden, anio, comuna_comprador, nombre_proveedor, round(monto_linea/1e6, 1) as millones_clp, texto_descriptivo
    FROM base_eval
    ORDER BY monto_linea DESC
    LIMIT 10
""").df()
for idx, r in c_before.iterrows():
    print(f"[{idx+1}] {r['codigo_orden']} ({r['anio']}) - {r['comuna_comprador']} | {r['nombre_proveedor']} | ${r['millones_clp']:,.1f} M CLP")
    print(f"    {r['texto_descriptivo'][:100]}...")

# 4. Top 10 Contratos Nacionales Después
print("\n--- TOP 10 CONTRATOS HISTÓRICOS NACIONALES (DESPUÉS DEL SANEAMIENTO) ---")
c_after = con.execute("""
    SELECT codigo_orden, anio, comuna_comprador, nombre_proveedor, round(monto_linea/1e6, 1) as millones_clp, texto_descriptivo
    FROM base_eval
    WHERE es_tecnologico_valido AND NOT es_espurio_obvio
    ORDER BY monto_linea DESC
    LIMIT 10
""").df()
for idx, r in c_after.iterrows():
    print(f"[{idx+1}] {r['codigo_orden']} ({r['anio']}) - {r['comuna_comprador']} | {r['nombre_proveedor']} | ${r['millones_clp']:,.1f} M CLP")
    print(f"    {r['texto_descriptivo'][:100]}...")
