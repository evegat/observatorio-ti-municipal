import duckdb

con = duckdb.connect()

p_raw = r"D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet"
p_san = r"D:\Proyectos\observatorio-ti-municipal\data\catastro_ti_saneado.parquet"

print("--- BUSCANDO CAPACITACIONES EN TECNOLOGÍA EN DATASET BASE ---")
q_cap = f"""
    SELECT 
        anio,
        codigo_orden,
        nombre_comprador,
        comuna_comprador,
        nombre_proveedor,
        nombre_producto_generico,
        texto_descriptivo,
        monto_linea
    FROM '{p_raw}'
    WHERE (
        texto_descriptivo ILIKE '%capacita%tecnol%' OR
        texto_descriptivo ILIKE '%capacita%comput%' OR
        texto_descriptivo ILIKE '%capacita%informat%' OR
        texto_descriptivo ILIKE '%capacita%software%' OR
        texto_descriptivo ILIKE '%capacita%ciberseguridad%' OR
        texto_descriptivo ILIKE '%capacita%excel%' OR
        texto_descriptivo ILIKE '%capacita%ofimat%' OR
        texto_descriptivo ILIKE '%alfabetiza%digital%' OR
        texto_descriptivo ILIKE '%curso%comput%' OR
        texto_descriptivo ILIKE '%curso%excel%' OR
        texto_descriptivo ILIKE '%curso%ciberseguridad%' OR
        texto_descriptivo ILIKE '%capacita%erp%' OR
        texto_descriptivo ILIKE '%capacita%sistema%' OR
        nombre_producto_generico ILIKE '%capacita%tecnol%' OR
        nombre_producto_generico ILIKE '%capacita%comput%' OR
        nombre_producto_generico ILIKE '%capacitaci%ti%'
    )
"""
df_cap = con.execute(q_cap).df()
print(f"Total registros de capacitación tecnológica encontrados: {len(df_cap)}")
print(f"Total OCs únicas: {df_cap['codigo_orden'].nunique()}")
print(f"Total comunas con capacitaciones TI: {df_cap['comuna_comprador'].nunique()}")
print(f"Monto total en capacitaciones TI: ${df_cap['monto_linea'].sum():,.0f} CLP")

print("\nMuestra de compras de capacitación TI:")
for _, r in df_cap.head(10).iterrows():
    print(f"[{r['anio']}] {r['comuna_comprador']} | {r['nombre_proveedor']} | ${r['monto_linea']:,.0f} CLP")
    print(f"     Desc: {str(r['texto_descriptivo'])[:100]}")
