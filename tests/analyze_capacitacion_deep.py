import duckdb
import pandas as pd

con = duckdb.connect()
p_raw = r"D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet"

q = f"""
    SELECT 
        anio,
        codigo_orden,
        comuna_comprador,
        nombre_proveedor,
        nombre_producto_generico,
        texto_descriptivo,
        monto_linea
    FROM '{p_raw}'
    WHERE (
        texto_descriptivo ILIKE '%capacita%' OR
        texto_descriptivo ILIKE '%curso%' OR
        texto_descriptivo ILIKE '%taller%comput%' OR
        texto_descriptivo ILIKE '%alfabetiza%digital%' OR
        nombre_producto_generico ILIKE '%capacita%' OR
        nombre_producto_generico ILIKE '%entrenamiento%'
    )
    AND (
        texto_descriptivo ILIKE '%excel%' OR
        texto_descriptivo ILIKE '%ofimat%' OR
        texto_descriptivo ILIKE '%word%' OR
        texto_descriptivo ILIKE '%computac%' OR
        texto_descriptivo ILIKE '%informat%' OR
        texto_descriptivo ILIKE '%software%' OR
        texto_descriptivo ILIKE '%tecnolog%' OR
        texto_descriptivo ILIKE '%ciberseguridad%' OR
        texto_descriptivo ILIKE '%seguridad de la informac%' OR
        texto_descriptivo ILIKE '%siaper%' OR
        texto_descriptivo ILIKE '%erp%' OR
        texto_descriptivo ILIKE '%cas-chile%' OR
        texto_descriptivo ILIKE '%gestion documental%' OR
        texto_descriptivo ILIKE '%docdigital%' OR
        texto_descriptivo ILIKE '%transformacion digital%' OR
        texto_descriptivo ILIKE '%inteligencia artificial%' OR
        texto_descriptivo ILIKE '%programac%' OR
        texto_descriptivo ILIKE '%redes%'
    )
    -- Blacklist para evitar catering y coffe break en capacitaciones
    AND NOT (
        texto_descriptivo ILIKE '%coffee%' OR
        texto_descriptivo ILIKE '%coffe break%' OR
        texto_descriptivo ILIKE '%banquete%' OR
        texto_descriptivo ILIKE '%colacion%' OR
        texto_descriptivo ILIKE '%sandwich%' OR
        texto_descriptivo ILIKE '%almuerzo%' OR
        texto_descriptivo ILIKE '%desayuno%'
    )
"""

df = con.execute(q).df()
print(f"Total registros clasificados de capacitación tecnológica: {len(df)}")
print(f"Total OCs únicas: {df['codigo_orden'].nunique()}")
print(f"Total comunas compradoras: {df['comuna_comprador'].nunique()}")
print(f"Monto total: ${df['monto_linea'].sum():,.0f} CLP")

def categorizar_curso(txt):
    t = str(txt).lower()
    if any(k in t for k in ['ciberseguridad', 'seguridad de la informaci', 'seguridad informatica', 'proteccion de datos', 'ley 21.719']):
        return 'Ciberseguridad y Datos'
    elif any(k in t for k in ['siaper', 'cas-chile', 'erp', 'gestion documental', 'docdigital', 'sigfe', 'sistema de personal', 'sistemas de gestion']):
        return 'Sistemas y ERP Municipal'
    elif any(k in t for k in ['alfabetizacion digital', 'adulto mayor', 'adultos mayores', 'comunitaria', 'vecinos', 'junta de vecinos']):
        return 'Alfabetización Digital Comunitaria'
    elif any(k in t for k in ['inteligencia artificial', 'ia ', 'ciencia de datos', 'python', 'business intelligence', 'power bi', 'transformacion digital']):
        return 'Innovación, BI e IA'
    elif any(k in t for k in ['excel', 'ofimatica', 'office', 'word', 'powerpoint', 'computacion basica', 'computacion intermedia', 'computacion avanzada']):
        return 'Ofimática y Productividad'
    else:
        return 'Otras Tecnologías y Habilidades Digitales'

df['categoria_capacitacion'] = df['texto_descriptivo'].apply(categorizar_curso)

print("\n--- DISTRIBUCIÓN POR CATEGORÍA DE CAPACITACIÓN TI ---")
cat_summary = df.groupby('categoria_capacitacion').agg(
    ocs=('codigo_orden', 'nunique'),
    comunas=('comuna_comprador', 'nunique'),
    monto_total=('monto_linea', 'sum')
).sort_values(by='monto_total', ascending=False)

cat_summary['monto_formateado'] = cat_summary['monto_total'].apply(lambda x: f"${x:,.0f} CLP")
print(cat_summary[['ocs', 'comunas', 'monto_formateado']])

print("\n--- TOP 10 COMUNAS QUE MÁS INVIERTEN EN CAPACITACIÓN TECNOLÓGICA ---")
muni_summary = df.groupby('comuna_comprador').agg(
    ocs=('codigo_orden', 'nunique'),
    monto_total=('monto_linea', 'sum')
).sort_values(by='monto_total', ascending=False).head(10)
for muni, r in muni_summary.iterrows():
    print(f"  - {muni:<25}: ${r['monto_total']:,.0f} CLP | {r['ocs']} OCs")

print("\n--- TOP 10 PROVEEDORES / OTEC DE CAPACITACIÓN TI MUNICIPAL ---")
prov_summary = df.groupby('nombre_proveedor').agg(
    ocs=('codigo_orden', 'nunique'),
    comunas=('comuna_comprador', 'nunique'),
    monto_total=('monto_linea', 'sum')
).sort_values(by='monto_total', ascending=False).head(10)
for prov, r in prov_summary.iterrows():
    print(f"  - {prov:<40}: ${r['monto_total']:,.0f} CLP | {r['comunas']} comunas")
