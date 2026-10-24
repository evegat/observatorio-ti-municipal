#!/usr/bin/env python3
"""
build_sanitized_observatorio_data.py
=====================================
Pipeline Maestro de Saneamiento Semántico y Cobertura Temporal de Compras Públicas TI (R1 / R2)
para el Observatorio de Capacidades Tecnológicas Municipales de Chile.

Características:
1. Filtro de Dos Capas Auditables:
   - Capa 1 (Blacklist): Erradica contratos espurios no tecnológicos (carpas, toldos, productoras de eventos,
     escenarios, gas licuado, zapatos sherpa, camionetas, cursos agrícolas/sociales, códigos ONU espurios).
   - Capa 2 (Whitelist Taxonómica UNSPSC): Restringe la canasta a familias genuinamente tecnológicas
     (Hardware, SaaS/Cloud, Telecomunicaciones, Ciberseguridad, Televigilancia y Reloj Biométrico).
   - Substring %rpa% reparado: Detección estricta de IA y automatización mediante límites de palabra (\b),
     eliminando falsos positivos en carpa, escarpe y zarpas.
2. Integración Temporal Completa 2014–2026 (incluye 2025 completo y 2026 acumulado a septiembre).
3. Desacoplamiento de Feeds:
   - top_contratos_recientes: Feed cronológico 2025–2026 (ORDER BY fecha_aceptacion DESC, monto DESC).
   - top_contratos_historicos: Contratos emblemáticos de mayor cuantía histórica (ORDER BY monto DESC).
4. Generación y Sincronización de Artefactos:
   - data/catastro_ti_saneado.parquet: Dataset granular de órdenes de compra saneadas.
   - data/compras_saneadas_por_comuna.json: Microdatos comunales de compras TI saneadas.
   - data/comunas_enriched.json: Actualización de compras preservando RRHH y demografía.
   - data/national_kpis.json: Recalibración de KPIs agregados y serie histórica anual saneada.
   - data/proveedores_ranking.json: Ranking nacional de proveedores tecnológicos auditados.
   - data/regiones_enriched.json: Rollup regional con montos e indicadores saneados.

Autor: worker_m1_compras (Observatorio TI Municipal)
Fecha: Octubre 2026
"""

from __future__ import annotations

import json
import logging
import re
import sys
import unicodedata
from pathlib import Path
import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BuildSanitizedData")

# Configurar stdout para UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PARQUET_IN = Path(r"D:\Proyectos\PUB021 - Paper Adopcion IA y Tecnologias en Municipios\data\catastro_ti_municipal_completo_clasificado.parquet")
PARQUET_OUT = DATA_DIR / "catastro_ti_saneado.parquet"
COMPRAS_JSON_OUT = DATA_DIR / "compras_saneadas_por_comuna.json"
ENRICHED_JSON = DATA_DIR / "comunas_enriched.json"
KPIS_JSON = DATA_DIR / "national_kpis.json"
PROV_JSON = DATA_DIR / "proveedores_ranking.json"
REGIONES_JSON = DATA_DIR / "regiones_enriched.json"


def normalize_text(s: str | None) -> str:
    """Normaliza texto eliminando acentos, mayúsculas y caracteres especiales."""
    if not s:
        return ""
    s = str(s).lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s.strip()


# Diccionario de equivalencias y toponimia municipal
COMUNA_ALIASES: dict[str, str] = {
    "santiago": "santiago",
    "santiago centro": "santiago",
    "estacion central": "estacion central",
    "la calera": "calera",
    "calera": "calera",
    "trehuaco": "treguaco",
    "treguaco": "treguaco",
    "marchigue": "marchihue",
    "marchihue": "marchihue",
    "las guaitecas": "guaitecas",
    "guaitecas": "guaitecas",
    "o higgins": "ohiggins",
    "ohiggins": "ohiggins",
    "til til": "tiltil",
    "tiltil": "tiltil",
    "san vicente de tagua tagua": "san vicente",
    "san vicente": "san vicente",
    "paihuano": "paiguano",
    "paiguano": "paiguano",
    "coyhaique": "coihaique",
    "coihaique": "coihaique",
    "puerto natales": "natales",
    "natales": "natales",
    "torres del payne": "torres del paine",
    "torres del paine": "torres del paine",
    "alto bio bio": "alto biobio",
    "alto biobio": "alto biobio",
    "chol chol": "cholchol",
    "cholchol": "cholchol",
    "puerto saavedra": "saavedra",
    "saavedra": "saavedra",
    "llayllay": "llaillay",
    "llay llay": "llaillay",
    "llaillay": "llaillay",
    "los alamos": "los alamos",
    "los angeles": "los angeles",
    "vichuquen": "vichuquen",
    "navarino": "cabo de hornos",
    "puerto williams": "cabo de hornos",
    "cabo de hornos": "cabo de hornos"
}


def sanitize_purchases(con: duckdb.DuckDBPyConnection) -> None:
    """Ejecuta el filtro de dos capas auditables sobre el catastro completo en DuckDB."""
    logger.info("Aplicando filtro de dos capas auditables en DuckDB...")

    filter_sql = f"""
    CREATE TABLE saneado_raw AS
    WITH base AS (
        SELECT 
            *,
            coalesce(rubro_nivel1, 'SIN_RUBRO') as rubro,
            coalesce(codigo_producto_onu, '0') as onu,
            lower(coalesce(texto_descriptivo, '')) as txt,
            lower(coalesce(nombre_proveedor, '')) as prov
        FROM read_parquet('{str(PARQUET_IN).replace("\\", "/")}')
    ),
    flagged AS (
        SELECT 
            base.*,
            
            -- CAPA 1: BLACKLIST DE TÉRMINOS Y CÓDIGOS ONU ESPURIOS NO-TI
            (
                txt LIKE '%carpa%' OR prov LIKE '%carpa%' OR txt LIKE '%toldo%' OR
                txt LIKE '%produccion de evento%' OR txt LIKE '%producción de evento%' OR
                txt LIKE '%productora%' OR txt LIKE '%fiesta%' OR txt LIKE '%banquete%' OR
                txt LIKE '%camarin%' OR txt LIKE '%camarín%' OR txt LIKE '%escenario%' OR
                txt LIKE '%curanto%' OR txt LIKE '%aniversario%' OR txt LIKE '%coctel%' OR
                txt LIKE '%cóctel%' OR txt LIKE '%banqueter%' OR txt LIKE '%amplificacion%' OR
                txt LIKE '%amplificación%' OR txt LIKE '%grupo folclorico%' OR
                txt LIKE '%grupo folclórico%' OR
                txt LIKE '%gas licuado%' OR txt LIKE '%gas envasado%' OR
                txt LIKE '%estanque%gas%' OR txt LIKE '%estaciones de servicio (storage)%' OR
                txt LIKE '%zapatos de seguridad%' OR txt LIKE '%zapato%seguridad%' OR
                txt LIKE '%botas de seguridad%' OR txt LIKE '%calzado de seguridad%' OR
                txt LIKE '%camioneta maxus%' OR txt LIKE '%canasta de alimentos%' OR
                txt LIKE '%obras civiles%' OR txt LIKE '%pavimentac%' OR
                txt LIKE '%sede jjvv%' OR txt LIKE '%apicol%' OR txt LIKE '%apícol%' OR
                txt LIKE '%violencia escolar%' OR txt LIKE '%clima laboral%' OR
                txt LIKE '%salud mental%' OR txt LIKE '%ecografia%' OR txt LIKE '%ecografía%' OR
                txt LIKE '%preuniversitario%' OR txt LIKE '%torneo extraescolar%' OR
                txt LIKE '%desratizac%' OR txt LIKE '%fumigac%' OR
                txt LIKE '%neumatico%' OR txt LIKE '%neumático%' OR
                txt LIKE '%combustible%' OR txt LIKE '%gasolina%' OR txt LIKE '%petroleo diesel%' OR
                
                -- Exclusiones añadidas: guitarra, sanitaria, fosas, topografía, eléctrica, agroveterinaria
                txt LIKE '%guitarra%' OR prov LIKE '%guitarra%' OR
                txt LIKE '%fosa%septica%' OR txt LIKE '%fosa%séptica%' OR
                txt LIKE '%gasfiter%' OR txt LIKE '%alcantarillado%' OR
                txt LIKE '%agroveterinaria%' OR prov LIKE '%agroveterinaria%' OR
                txt LIKE '%veterinaria%' OR prov LIKE '%veterinaria%' OR
                txt LIKE '%topogra%' OR prov LIKE '%topogra%' OR
                txt LIKE '%fotogrametria%' OR txt LIKE '%fotogrametría%' OR
                txt LIKE '%instalaciones electricas%' OR txt LIKE '%instalaciones eléctricas%' OR
                
                -- Exclusiones automotrices y mecánicas
                txt LIKE '%camioneta%' OR prov LIKE '%neubacar%' OR
                txt LIKE '%taller mecanico%' OR txt LIKE '%taller mecánico%' OR
                prov LIKE '%taller mecanico%' OR prov LIKE '%taller mecánico%' OR
                txt LIKE '%lubricentro%' OR prov LIKE '%lubricentro%' OR
                txt LIKE '%aceite%mobil%' OR txt LIKE '%aceite%15w40%' OR
                txt LIKE '%barra central direccion%' OR txt LIKE '%barra central dirección%' OR
                txt LIKE '%computador para camioneta%' OR
                regexp_matches(txt, '\\b(ecu)\\b') OR
                txt LIKE '%falla en computador%' OR
                ((txt LIKE '%vehiculo%' OR txt LIKE '%vehículo%') AND txt NOT LIKE '%gps%') OR
                
                onu IN ('30221001', '10101704', '30151901', '90101602', '90151602', 
                        '80141607', '90111603', '72131702', '72131701', '90151803', 
                        '80141611', '80141609', '80141605', '80141620', '76121503',
                        '53121603', '80111504',
                        '81141806', '81141807', '81151604', '81151603', '81141602', '80141600')
            ) as es_espurio_obvio,

            -- CAPA 2: WHITELIST TAXONÓMICA UNSPSC DE RUBROS Y CÓDIGOS TI
            (
                -- 1. Rubro TI principal
                rubro = 'Tecnologías de la información, telecomunicaciones y radiodifusión'
                
                -- 2. Rubro Servicios TI e Ingeniería (SOLO servicios informáticos 8111)
                OR (rubro = 'Servicios basados en ingeniería, ciencias sociales y tecnología de la información' AND onu LIKE '8111%')
                
                -- 3. Servicios básicos: SOLO Internet y Telecom
                OR (rubro = 'Servicios básicos y de información pública' AND onu IN ('83121703', '83121700', '83111601', '83111600'))
                
                -- 4. Servicios profesionales: SOLO desarrollo de software, consultoría TI, BI, bases de datos
                OR (rubro = 'Servicios profesionales, administrativos y consultorías de gestión empresarial' 
                    AND (
                        onu IN ('80111711', '80101507', '80111609', '80111712', '80111610', '80161503', '80161506')
                        OR (onu = '80101508' AND (
                            txt LIKE '%inteligencia artificial%' OR txt LIKE '%software%' OR 
                            txt LIKE '%datos%' OR regexp_matches(txt, '\\bbi\\b') OR 
                            txt LIKE '%cloud%' OR txt LIKE '%ciberseguridad%' OR txt LIKE '%business intelligence%'
                        ))
                    )
                )
                
                -- 5. Equipos de seguridad: SOLO CCTV / Televigilancia / Control acceso
                OR (rubro = 'Equipos y suministros de defensa, orden público, protección y seguridad' 
                    AND (onu LIKE '461716%' OR txt LIKE '%camara%' OR txt LIKE '%cctv%' OR txt LIKE '%televigilancia%'))
                
                -- 6. Oficina: SOLO reloj control biométrico
                OR (rubro = 'Equipos, accesorios y suministros de oficina' AND onu = '44103201')
                
                -- 7. Registros con rubro NA / Sin rubro / código 0: SOLO si tienen descripción técnica TI inequívoca
                OR ((rubro = 'SIN_RUBRO' OR rubro = 'NA' OR onu = '0') AND (
                    txt LIKE '%servidor%' OR txt LIKE '%software%' OR txt LIKE '%licencia%' OR
                    txt LIKE '%hosting%' OR txt LIKE '%internet%' OR txt LIKE '%computador%' OR
                    txt LIKE '%notebook%' OR txt LIKE '%ciberseguridad%' OR txt LIKE '%antivirus%' OR
                    txt LIKE '%base de datos%' OR txt LIKE '%soporte ti%' OR txt LIKE '%infraestructura ti%'
                ))
            ) as es_tecnologico_valido,

            -- Banderas funcionales reevaluadas
            (
                regexp_matches(txt, '\\b(inteligencia artificial|machine learning|aprendizaje automatico|aprendizaje automático|deep learning|ia generativa)\\b')
                OR regexp_matches(txt, '\\b(chatbot|asistente virtual|vision artificial|visión artificial|reconocimiento facial|analitica de video|analítica de video|vision computacional|visión computacional)\\b')
                OR regexp_matches(txt, '\\b(rpa|robotic process automation|automatizacion de procesos|automatización de procesos|automatizacion documental|automatización documental)\\b')
            ) as flag_ia_saneada,

            (
                onu LIKE '4321%' OR onu LIKE '4322%' OR onu LIKE '4320%' OR
                txt LIKE '%servidor%' OR txt LIKE '%server%' OR txt LIKE '%computador%' OR 
                txt LIKE '%desktop%' OR txt LIKE '%notebook%' OR txt LIKE '%laptop%' OR 
                txt LIKE '%tablet%' OR txt LIKE '%all in one%' OR txt LIKE '%pantalla%' OR 
                txt LIKE '%monitor%' OR txt LIKE '%disco duro%' OR txt LIKE '%ssd%' OR 
                txt LIKE '%ups%' OR txt LIKE '%rack%' OR txt LIKE '%datacenter%' OR 
                txt LIKE '%almacenamiento san%' OR txt LIKE '%storage%'
            ) as flag_hardware_saneada,

            (
                onu LIKE '4323%' OR onu IN ('81112105', '81111812', '81111503', '81111508') OR
                txt LIKE '%saas%' OR txt LIKE '%software as a service%' OR txt LIKE '%suscripci%' OR 
                txt LIKE '%licenciamiento anual%' OR txt LIKE '%nube%' OR txt LIKE '%cloud%' OR 
                txt LIKE '%microsoft 365%' OR txt LIKE '%office 365%' OR txt LIKE '%m365%' OR 
                txt LIKE '%azure%' OR txt LIKE '%google workspace%' OR txt LIKE '%g suite%' OR 
                txt LIKE '%aws%' OR txt LIKE '%amazon web services%' OR txt LIKE '%hosting%' OR 
                txt LIKE '%vps%' OR prov LIKE '%microsoft%' OR prov LIKE '%amazon%' OR prov LIKE '%google%'
            ) as flag_saas_saneada,

            (
                onu LIKE '8312%' OR onu LIKE '8311%' OR onu IN ('83121703', '83121700', '83111601', '83111600') OR
                txt LIKE '%enlace%' OR txt LIKE '%fibra optica%' OR txt LIKE '%fibra óptica%' OR 
                txt LIKE '%internet dedicado%' OR txt LIKE '%conexion de internet%' OR 
                txt LIKE '%telefonia ip%' OR txt LIKE '%telefonía ip%' OR 
                txt LIKE '%central telefonica%' OR txt LIKE '%central telefónica%' OR 
                prov LIKE '%gtd%' OR prov LIKE '%entel%' OR prov LIKE '%telefonica%' OR 
                prov LIKE '%telefónica%' OR prov LIKE '%claro%' OR prov LIKE '%mundo pacifico%' OR prov LIKE '%vtr%'
            ) as flag_telecom_saneada,

            (
                txt LIKE '%ciberseguridad%' OR txt LIKE '%seguridad de la informacion%' OR 
                txt LIKE '%seguridad informatica%' OR txt LIKE '%seguridad informática%' OR 
                txt LIKE '%firewall%' OR txt LIKE '%fortinet%' OR txt LIKE '%palo alto%' OR 
                txt LIKE '%antivirus%' OR txt LIKE '%soc%' OR txt LIKE '%edr%' OR 
                txt LIKE '%pentesting%' OR txt LIKE '%hacking etico%' OR txt LIKE '%hacking ético%' OR 
                txt LIKE '%veeam%'
            ) as flag_cyber_saneada,

            (
                onu LIKE '461716%' OR txt LIKE '%camara%' OR txt LIKE '%cámara%' OR 
                txt LIKE '%cctv%' OR txt LIKE '%televigilancia%' OR txt LIKE '%domo ptz%' OR 
                txt LIKE '%portico%' OR txt LIKE '%pórtico%' OR txt LIKE '%lpr%'
            ) as flag_televigilancia_saneada,

            (
                txt LIKE '%atencion ciudadana%' OR txt LIKE '%atención ciudadana%' OR 
                txt LIKE '%chatbot municipal%' OR txt LIKE '%portal de tramites%' OR 
                txt LIKE '%portal de trámites%' OR txt LIKE '%ventanilla unica%' OR 
                txt LIKE '%ventanilla única%' OR txt LIKE '%totem%' OR 
                txt LIKE '%tótem de autoatencion%' OR txt LIKE '%fila virtual%'
            ) as flag_atencion_saneada,

            (
                txt LIKE '%cas-chile%' OR txt LIKE '%cas chile%' OR txt LIKE '%caschile%' OR 
                prov LIKE '%cas-chile%' OR prov LIKE '%cas chile%' OR 
                prov LIKE '%asesorias y sistemas computacionales%' OR 
                txt LIKE '%unidigital%' OR prov LIKE '%unidigital%' OR 
                txt LIKE '%smat%' OR txt LIKE '%sistema de administracion y tributacion%' OR 
                txt LIKE '%thomson reuters%' OR prov LIKE '%thomson reuters%'
            ) as flag_legado_saneada,

            (
                txt LIKE '%open source%' OR txt LIKE '%codigo abierto%' OR txt LIKE '%código abierto%' OR 
                txt LIKE '%software libre%' OR txt LIKE '%linux%' OR txt LIKE '%ubuntu%' OR 
                txt LIKE '%postgresql%' OR txt LIKE '%postgres%' OR txt LIKE '%mysql%' OR 
                txt LIKE '%moodle%' OR txt LIKE '%nextcloud%' OR txt LIKE '%qgis%'
            ) as flag_foss_saneada

        FROM base
    )
    SELECT * FROM flagged
    WHERE es_tecnologico_valido AND NOT es_espurio_obvio
    """
    con.execute(filter_sql)

    # Crear tabla final limpia con reemplazo de flags
    con.execute("""
    CREATE TABLE catastro_ti_saneado AS
    SELECT 
        item_id,
        codigo_orden,
        correlativo,
        fecha_aceptacion,
        anio,
        mes,
        rut_comprador,
        nombre_comprador,
        tipo_organismo,
        CASE 
            WHEN comuna_comprador = 'Santiago Centro' THEN 'Santiago' 
            WHEN comuna_comprador = 'Alto Bio Bio' THEN 'Alto Biobío'
            WHEN comuna_comprador = 'Calera' THEN 'La Calera'
            WHEN comuna_comprador = 'Chol Chol' THEN 'Cholchol'
            WHEN comuna_comprador = 'Coihaique' THEN 'Coyhaique'
            WHEN comuna_comprador = 'Las Guaitecas' THEN 'Guaitecas'
            WHEN comuna_comprador = 'Llay-Llay' THEN 'Llaillay'
            WHEN comuna_comprador = 'Los Alamos' THEN 'Los Álamos'
            WHEN comuna_comprador = 'Los Angeles' THEN 'Los Ángeles'
            WHEN comuna_comprador = 'Marchigue' THEN 'Marchihue'
            WHEN comuna_comprador = 'Puerto Natales' THEN 'Natales'
            ELSE comuna_comprador 
        END as comuna_comprador,
        region_comprador,
        rut_proveedor,
        nombre_proveedor,
        codigo_producto_onu,
        nombre_producto_generico,
        rubro_nivel1,
        rubro_nivel2,
        rubro_nivel3,
        cantidad,
        precio_neto,
        CASE WHEN monto_linea IS NULL OR isnan(monto_linea) THEN 0.0 ELSE monto_linea END as monto_linea,
        texto_descriptivo,
        subtipo_institucional,
        modalidad_compra,
        flag_saas_saneada as flag_saas_cloud,
        flag_legado_saneada as flag_legacy_muni,
        flag_foss_saneada as flag_open_source,
        flag_hardware_saneada as flag_infra_hardware,
        flag_telecom_saneada as flag_redes_telecom,
        flag_cyber_saneada as flag_ciberseguridad,
        flag_televigilancia_saneada as flag_televigilancia,
        flag_atencion_saneada as flag_atencion_ciudadana,
        flag_ia_saneada as flag_ia_automatizacion,
        flag_consultoria_desarrollo,
        flag_gestion_documental_firma
    FROM saneado_raw
    WHERE comuna_comprador IS NOT NULL 
      AND trim(comuna_comprador) != ''
      AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
      AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
    """)

    # Exportar Parquet Saneado
    logger.info(f"Exportando dataset granular a: {PARQUET_OUT}")
    con.execute(f"COPY catastro_ti_saneado TO '{str(PARQUET_OUT).replace('\\', '/')}' (FORMAT PARQUET)")


def compute_comuna_metrics(con: duckdb.DuckDBPyConnection) -> dict:
    """Calcula agregaciones por comuna, proveedores y contratos."""
    logger.info("Calculando métricas agregadas por comuna...")

    # 1. Agregados comunales (agrupación estricta por comuna_comprador para evitar clobbering multi-región)
    comunas_df = con.execute("""
        SELECT 
            comuna_comprador as comuna,
            count(distinct codigo_orden) as total_ocs,
            round(coalesce(sum(monto_linea), 0), 0) as monto_total,
            round(coalesce(sum(case when flag_infra_hardware then monto_linea else 0 end), 0), 0) as monto_hardware,
            round(coalesce(sum(case when flag_saas_cloud then monto_linea else 0 end), 0), 0) as monto_saas,
            round(coalesce(sum(case when flag_ia_automatizacion then monto_linea else 0 end), 0), 0) as monto_ia,
            round(coalesce(sum(case when flag_redes_telecom then monto_linea else 0 end), 0), 0) as monto_telecom,
            round(coalesce(sum(case when flag_ciberseguridad then monto_linea else 0 end), 0), 0) as monto_cyber,
            round(coalesce(sum(case when flag_televigilancia then monto_linea else 0 end), 0), 0) as monto_televigilancia,
            round(coalesce(sum(case when flag_atencion_ciudadana then monto_linea else 0 end), 0), 0) as monto_atencion,
            round(coalesce(sum(case when flag_legacy_muni then monto_linea else 0 end), 0), 0) as monto_legado,
            round(coalesce(sum(case when flag_open_source then monto_linea else 0 end), 0), 0) as monto_foss,
            
            -- Score de madurez tecnológica (0 a 100)
            least(100, round(
                (case when sum(case when flag_infra_hardware then 1 else 0 end) > 5 then 20 else 0 end) +
                (case when sum(case when flag_atencion_ciudadana then 1 else 0 end) > 0 then 20 else 0 end) +
                (case when sum(case when flag_saas_cloud then 1 else 0 end) > 0 then 20 else 0 end) +
                (case when sum(case when flag_ciberseguridad then 1 else 0 end) > 0 then 20 else 0 end) +
                (case when sum(case when flag_ia_automatizacion then 1 else 0 end) > 0 then 20 else 0 end)
            , 0)) as score_madurez,
            (sum(case when flag_open_source then 1 else 0 end) > 0) as tiene_foss,
            (sum(case when flag_infra_hardware then 1 else 0 end) > 10) as tiene_infra_propia,
            (sum(case when flag_legacy_muni then 1 else 0 end) > 0) as tiene_lockin_legado
        FROM catastro_ti_saneado
        WHERE comuna_comprador IS NOT NULL 
          AND trim(comuna_comprador) != ''
          AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
          AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
        GROUP BY comuna_comprador
        HAVING sum(monto_linea) IS NOT NULL AND sum(monto_linea) > 0
    """).df()

    # 2. Top Proveedores por comuna (Top 3-5)
    top_prov_df = con.execute("""
        WITH ranked AS (
            SELECT 
                comuna_comprador as comuna,
                coalesce(nombre_proveedor, 'Proveedor no especificado') as proveedor,
                round(coalesce(sum(monto_linea), 0), 0) as monto,
                count(distinct codigo_orden) as ocs,
                ROW_NUMBER() OVER(PARTITION BY comuna_comprador ORDER BY sum(monto_linea) DESC) as rnk
            FROM catastro_ti_saneado
            WHERE comuna_comprador IS NOT NULL AND comuna_comprador NOT IN ('Sin comuna', 'NA')
              AND nombre_proveedor IS NOT NULL
            GROUP BY comuna_comprador, coalesce(nombre_proveedor, 'Proveedor no especificado')
            HAVING sum(monto_linea) > 0
        )
        SELECT comuna, proveedor, monto, ocs
        FROM ranked
        WHERE rnk <= 5
    """).df()

    prov_by_comuna: dict[str, list[dict]] = {}
    for _, r in top_prov_df.iterrows():
        c = str(r["comuna"]).strip()
        prov_by_comuna.setdefault(c, []).append({
            "proveedor": str(r["proveedor"]).strip(),
            "monto": float(r["monto"]),
            "ocs": int(r["ocs"])
        })

    # 3. Top Contratos Emblemáticos Históricos (ORDER BY monto DESC, max 4)
    top_hist_df = con.execute("""
        WITH ocs_grouped AS (
            SELECT 
                comuna_comprador as comuna,
                codigo_orden as codigo_oc,
                coalesce(nombre_proveedor, 'Proveedor no especificado') as proveedor,
                coalesce(anio, 2024) as anio,
                coalesce(fecha_aceptacion, 'NA') as fecha_aceptacion,
                round(coalesce(sum(monto_linea), 0), 0) as monto,
                arbitrary(texto_descriptivo) as descr_raw
            FROM catastro_ti_saneado
            WHERE comuna_comprador IS NOT NULL 
              AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
              AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
              AND codigo_orden IS NOT NULL
            GROUP BY comuna_comprador, codigo_orden, coalesce(nombre_proveedor, 'Proveedor no especificado'),
                     coalesce(anio, 2024), coalesce(fecha_aceptacion, 'NA')
            HAVING sum(monto_linea) > 0
        ),
        ranked AS (
            SELECT 
                comuna, codigo_oc, proveedor, anio, fecha_aceptacion, monto, descr_raw,
                ROW_NUMBER() OVER(PARTITION BY comuna ORDER BY monto DESC) as rnk
            FROM ocs_grouped
        )
        SELECT comuna, codigo_oc, proveedor, anio, fecha_aceptacion, monto, descr_raw
        FROM ranked
        WHERE rnk <= 4
    """).df()

    def clean_description(d: str | None) -> str:
        raw = str(d or "").replace("\r", " ").replace("\n", " ").strip()
        clean = re.sub(r"\s+", " ", raw)
        if len(clean) > 130:
            clean = clean[:127] + "..."
        return clean if clean and clean != "None" else "Sin descripción de ítem"

    hist_by_comuna: dict[str, list[dict]] = {}
    for _, r in top_hist_df.iterrows():
        c = str(r["comuna"]).strip()
        cod = str(r["codigo_oc"]).strip()
        hist_by_comuna.setdefault(c, []).append({
            "codigo_oc": cod,
            "proveedor": str(r["proveedor"]).strip(),
            "anio": int(r["anio"]),
            "fecha_aceptacion": str(r["fecha_aceptacion"]).strip(),
            "monto": float(r["monto"]),
            "descripcion": clean_description(r["descr_raw"]),
            "url_mercadopublico": f"https://www.mercadopublico.cl/Ficha/FichaOrdenCompra.aspx?CodigoOC={cod}"
        })

    # 4. Top Contratos Recientes 2025–2026 (ORDER BY fecha_aceptacion DESC, monto DESC, max 6)
    top_rec_df = con.execute("""
        WITH ocs_grouped AS (
            SELECT 
                comuna_comprador as comuna,
                codigo_orden as codigo_oc,
                coalesce(nombre_proveedor, 'Proveedor no especificado') as proveedor,
                coalesce(anio, 2025) as anio,
                coalesce(fecha_aceptacion, '2025-01-01') as fecha_aceptacion,
                round(coalesce(sum(monto_linea), 0), 0) as monto,
                arbitrary(texto_descriptivo) as descr_raw
            FROM catastro_ti_saneado
            WHERE comuna_comprador IS NOT NULL 
              AND comuna_comprador NOT IN ('Sin comuna', 'NA', 'Extranjero', '*')
              AND NOT regexp_matches(comuna_comprador, '^[0-9 *]+$')
              AND codigo_orden IS NOT NULL
              AND anio >= 2025
            GROUP BY comuna_comprador, codigo_orden, coalesce(nombre_proveedor, 'Proveedor no especificado'),
                     coalesce(anio, 2025), coalesce(fecha_aceptacion, '2025-01-01')
            HAVING sum(monto_linea) > 0
        ),
        ranked AS (
            SELECT 
                comuna, codigo_oc, proveedor, anio, fecha_aceptacion, monto, descr_raw,
                ROW_NUMBER() OVER(PARTITION BY comuna ORDER BY fecha_aceptacion DESC, monto DESC) as rnk
            FROM ocs_grouped
        )
        SELECT comuna, codigo_oc, proveedor, anio, fecha_aceptacion, monto, descr_raw
        FROM ranked
        WHERE rnk <= 6
    """).df()

    rec_by_comuna: dict[str, list[dict]] = {}
    for _, r in top_rec_df.iterrows():
        c = str(r["comuna"]).strip()
        cod = str(r["codigo_oc"]).strip()
        rec_by_comuna.setdefault(c, []).append({
            "codigo_oc": cod,
            "proveedor": str(r["proveedor"]).strip(),
            "anio": int(r["anio"]),
            "fecha_aceptacion": str(r["fecha_aceptacion"]).strip(),
            "monto": float(r["monto"]),
            "descripcion": clean_description(r["descr_raw"]),
            "url_mercadopublico": f"https://www.mercadopublico.cl/Ficha/FichaOrdenCompra.aspx?CodigoOC={cod}"
        })

    return {
        "comunas_df": comunas_df,
        "prov_by_comuna": prov_by_comuna,
        "hist_by_comuna": hist_by_comuna,
        "rec_by_comuna": rec_by_comuna
    }


def merge_and_save_data(con: duckdb.DuckDBPyConnection, metrics: dict) -> None:
    """Combina los datos saneados con la información comunal y RRHH existente y actualiza archivos."""
    logger.info("Cargando comunas_enriched.json existente...")
    with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
        comunas_existing = json.load(f)

    comunas_df = metrics["comunas_df"]
    prov_by_comuna = metrics["prov_by_comuna"]
    hist_by_comuna = metrics["hist_by_comuna"]
    rec_by_comuna = metrics["rec_by_comuna"]

    # Crear mapa de búsqueda para métricas de compras por nombre normalizado (con protección anti-clobbering)
    duck_metrics_by_norm: dict[str, dict] = {}
    for _, row in comunas_df.iterrows():
        raw_name = str(row["comuna"]).strip()
        norm_name = normalize_text(raw_name)
        resolved = COMUNA_ALIASES.get(norm_name, norm_name)
        monto = float(row["monto_total"])
        
        # Protección contra clobbering: si ya existe la llave, solo actualizar si el nuevo registro tiene mayor monto_total
        if resolved not in duck_metrics_by_norm or monto > duck_metrics_by_norm[resolved]["row"]["monto_total"]:
            duck_metrics_by_norm[resolved] = {
                "row": row,
                "raw_name": raw_name
            }
        if norm_name not in duck_metrics_by_norm or monto > duck_metrics_by_norm[norm_name]["row"]["monto_total"]:
            duck_metrics_by_norm[norm_name] = {
                "row": row,
                "raw_name": raw_name
            }

    updated_comunas = []
    compras_saneadas_list = []

    for item in comunas_existing:
        c_name = item.get("comuna", "")
        c_raw = item.get("comuna_raw", c_name)
        norm_c = normalize_text(c_name)
        norm_raw = normalize_text(c_raw)
        resolved_c = COMUNA_ALIASES.get(norm_c, norm_c)

        # Buscar en duck_metrics
        match = duck_metrics_by_norm.get(resolved_c) or duck_metrics_by_norm.get(norm_c) or duck_metrics_by_norm.get(norm_raw)

        poblacion = item.get("poblacion") or 1

        if match:
            r = match["row"]
            raw_match_name = match["raw_name"]
            monto_total = float(r["monto_total"])
            total_ocs = int(r["total_ocs"])
            monto_hw = float(r["monto_hardware"])
            monto_saas = float(r["monto_saas"])
            monto_ia = float(r["monto_ia"])
            monto_telecom = float(r["monto_telecom"])
            monto_cyber = float(r["monto_cyber"])
            monto_atencion = float(r["monto_atencion"])
            monto_televigilancia = float(r["monto_televigilancia"])
            monto_legado = float(r["monto_legado"])
            monto_foss = float(r["monto_foss"])
            score_madurez = int(r["score_madurez"])
            tiene_foss = bool(r["tiene_foss"])
            tiene_infra_propia = bool(r["tiene_infra_propia"])
            tiene_lockin_legado = bool(r["tiene_lockin_legado"])

            provs = prov_by_comuna.get(raw_match_name) or prov_by_comuna.get(c_raw) or prov_by_comuna.get(c_name) or []
            hist = hist_by_comuna.get(raw_match_name) or hist_by_comuna.get(c_raw) or hist_by_comuna.get(c_name) or []
            rec = rec_by_comuna.get(raw_match_name) or rec_by_comuna.get(c_raw) or rec_by_comuna.get(c_name) or []
        else:
            # Comunas sin compras en el catastro (ej. Combarbalá)
            monto_total = 0.0
            total_ocs = 0
            monto_hw = 0.0
            monto_saas = 0.0
            monto_ia = 0.0
            monto_telecom = 0.0
            monto_cyber = 0.0
            monto_atencion = 0.0
            monto_televigilancia = 0.0
            monto_legado = 0.0
            monto_foss = 0.0
            score_madurez = 0
            tiene_foss = False
            tiene_infra_propia = False
            tiene_lockin_legado = False
            provs = []
            hist = []
            rec = []

        gasto_pc = round(monto_total / poblacion, 0) if poblacion and poblacion > 0 else 0.0
        hw_pc = round(monto_hw / poblacion, 0) if poblacion and poblacion > 0 else 0.0
        saas_pc = round(monto_saas / poblacion, 0) if poblacion and poblacion > 0 else 0.0
        ia_pc = round(monto_ia / poblacion, 0) if poblacion and poblacion > 0 else 0.0
        telecom_pc = round(monto_telecom / poblacion, 0) if poblacion and poblacion > 0 else 0.0
        cyber_pc = round(monto_cyber / poblacion, 0) if poblacion and poblacion > 0 else 0.0

        if score_madurez >= 80:
            nivel_madurez = "Madurez Avanzada"
        elif score_madurez >= 60:
            nivel_madurez = "Madurez Intermedia"
        elif score_madurez >= 40:
            nivel_madurez = "Madurez Inicial"
        else:
            nivel_madurez = "Rezago Digital"

        # Actualizar campos de compras en item
        item["total_ocs"] = total_ocs
        item["monto_total"] = monto_total
        item["gasto_pc"] = gasto_pc
        item["score_madurez"] = score_madurez
        item["nivel_madurez"] = nivel_madurez
        item["monto_hardware"] = monto_hw
        item["hardware_pc"] = hw_pc
        item["monto_saas"] = monto_saas
        item["saas_pc"] = saas_pc
        item["monto_ia"] = monto_ia
        item["ia_pc"] = ia_pc
        item["monto_telecom"] = monto_telecom
        item["telecom_pc"] = telecom_pc
        item["monto_cyber"] = monto_cyber
        item["cyber_pc"] = cyber_pc
        item["monto_atencion"] = monto_atencion
        item["monto_televigilancia"] = monto_televigilancia
        item["monto_legado"] = monto_legado
        item["monto_foss"] = monto_foss
        item["tiene_foss"] = tiene_foss
        item["tiene_infra_propia"] = tiene_infra_propia
        item["tiene_lockin_legado"] = tiene_lockin_legado
        item["top_proveedores"] = provs
        item["top_contratos_recientes"] = rec
        item["top_contratos_historicos"] = hist
        item["top_contratos"] = hist  # Retrocompatibilidad

        updated_comunas.append(item)

        # Microobjeto específico para compras_saneadas_por_comuna.json
        compras_saneadas_list.append({
            "codigo_cut": item["codigo_cut"],
            "comuna": item["comuna"],
            "comuna_raw": item.get("comuna_raw", item["comuna"]),
            "region": item["region"],
            "poblacion": item["poblacion"],
            "total_ocs": total_ocs,
            "monto_total": monto_total,
            "gasto_pc": gasto_pc,
            "score_madurez": score_madurez,
            "nivel_madurez": nivel_madurez,
            "monto_hardware": monto_hw,
            "hardware_pc": hw_pc,
            "monto_saas": monto_saas,
            "saas_pc": saas_pc,
            "monto_ia": monto_ia,
            "ia_pc": ia_pc,
            "monto_telecom": monto_telecom,
            "telecom_pc": telecom_pc,
            "monto_cyber": monto_cyber,
            "cyber_pc": cyber_pc,
            "monto_atencion": monto_atencion,
            "monto_televigilancia": monto_televigilancia,
            "monto_legado": monto_legado,
            "monto_foss": monto_foss,
            "tiene_foss": tiene_foss,
            "tiene_infra_propia": tiene_infra_propia,
            "tiene_lockin_legado": tiene_lockin_legado,
            "top_proveedores": provs,
            "top_contratos_recientes": rec,
            "top_contratos_historicos": hist
        })

    # Guardar comunas_enriched.json
    logger.info(f"Guardando comunas_enriched.json actualizado ({len(updated_comunas)} comunas)...")
    ENRICHED_JSON.write_text(json.dumps(updated_comunas, ensure_ascii=False, indent=2), encoding="utf-8")

    # Guardar compras_saneadas_por_comuna.json
    logger.info(f"Guardando compras_saneadas_por_comuna.json ({len(compras_saneadas_list)} comunas)...")
    COMPRAS_JSON_OUT.write_text(json.dumps(compras_saneadas_list, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Actualizar national_kpis.json
    logger.info("Recalculando national_kpis.json con datos saneados...")
    if KPIS_JSON.exists():
        with open(KPIS_JSON, "r", encoding="utf-8") as f:
            kpis_data = json.load(f)
    else:
        kpis_data = {}

    tot_kpis = con.execute("""
        SELECT 
            count(distinct codigo_orden) as total_ocs,
            count(distinct rut_comprador) as total_entidades,
            round(sum(monto_linea), 0) as monto_total_clp
        FROM catastro_ti_saneado
    """).fetchone()

    # Serie anual saneada
    series_df = con.execute("""
        SELECT 
            anio,
            count(distinct codigo_orden) as ocs,
            round(sum(monto_linea), 0) as total_clp,
            round(sum(case when flag_infra_hardware then monto_linea else 0 end), 0) as hardware_clp,
            round(sum(case when flag_ia_automatizacion then monto_linea else 0 end), 0) as ia_clp,
            round(sum(case when flag_saas_cloud then monto_linea else 0 end), 0) as saas_clp,
            round(sum(case when flag_legacy_muni then monto_linea else 0 end), 0) as legado_clp,
            round(sum(case when flag_open_source then monto_linea else 0 end), 0) as foss_clp
        FROM catastro_ti_saneado
        WHERE anio BETWEEN 2015 AND 2026
        GROUP BY anio
        ORDER BY anio
    """).df()

    kpis_data["total_ocs"] = int(tot_kpis[0])
    kpis_data["total_entidades"] = len(updated_comunas)
    kpis_data["monto_total_clp"] = float(tot_kpis[2])
    kpis_data["series_anual"] = series_df.to_dict(orient="records")

    KPIS_JSON.write_text(json.dumps(kpis_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Actualizar proveedores_ranking.json (Top 40 nacional)
    logger.info("Recalculando ranking de proveedores tecnológicos en proveedores_ranking.json...")
    top_nat_df = con.execute("""
        WITH prov_totals AS (
            SELECT 
                nombre_proveedor as proveedor,
                coalesce(rut_proveedor, 'S/R') as rut,
                count(*) as total_lineas,
                count(distinct codigo_orden) as total_ocs,
                count(distinct comuna_comprador) as total_munis,
                round(sum(monto_linea), 0) as monto_total_clp,
                round(sum(case when flag_infra_hardware then monto_linea else 0 end), 0) as monto_hw,
                round(sum(case when flag_saas_cloud then monto_linea else 0 end), 0) as monto_saas,
                round(sum(case when flag_redes_telecom then monto_linea else 0 end), 0) as monto_telecom,
                round(sum(case when flag_ciberseguridad then monto_linea else 0 end), 0) as monto_cyber,
                round(sum(case when flag_legacy_muni then monto_linea else 0 end), 0) as monto_legado
            FROM catastro_ti_saneado
            WHERE nombre_proveedor IS NOT NULL AND trim(nombre_proveedor) != ''
            GROUP BY nombre_proveedor, coalesce(rut_proveedor, 'S/R')
            HAVING sum(monto_linea) > 0
        )
        SELECT 
            proveedor,
            rut,
            total_lineas,
            total_ocs,
            total_munis,
            monto_total_clp,
            round(monto_total_clp * 100.0 / sum(monto_total_clp) over(), 2) as cuota_mercado_pct,
            CASE 
                WHEN monto_hw >= greatest(monto_saas, monto_telecom, monto_cyber, monto_legado) THEN 'Hardware e Infraestructura'
                WHEN monto_telecom >= greatest(monto_hw, monto_saas, monto_cyber, monto_legado) THEN 'Telecomunicaciones y Conectividad'
                WHEN monto_saas >= greatest(monto_hw, monto_telecom, monto_cyber, monto_legado) THEN 'SaaS y Servicios Cloud'
                WHEN monto_cyber >= greatest(monto_hw, monto_saas, monto_telecom, monto_legado) THEN 'Ciberseguridad y Protección'
                WHEN monto_legado >= greatest(monto_hw, monto_saas, monto_telecom, monto_cyber) THEN 'Sistemas Municipales Legados'
                ELSE 'Tecnologías de la Información'
            END as rubro_principal
        FROM prov_totals
        ORDER BY monto_total_clp DESC
        LIMIT 40
    """).df()

    prov_list = top_nat_df.to_dict(orient="records")
    PROV_JSON.write_text(json.dumps(prov_list, ensure_ascii=False, indent=2), encoding="utf-8")

    # 7. Actualizar regiones_enriched.json
    logger.info("Recalculando rollup regional en regiones_enriched.json...")
    regiones_summary: dict[str, dict] = {}
    for c in updated_comunas:
        reg = c["region"]
        if reg not in regiones_summary:
            regiones_summary[reg] = {
                "region": reg,
                "total_comunas": 0,
                "total_poblacion": 0,
                "monto_total": 0.0,
                "total_ocs": 0,
                "monto_hardware": 0.0,
                "monto_ia": 0.0,
                "monto_saas": 0.0,
                "monto_cyber": 0.0,
                "monto_telecom": 0.0,
                "comunas_con_lockin": 0,
                "comunas_con_foss": 0,
                "comunas": []
            }
        rs = regiones_summary[reg]
        rs["total_comunas"] += 1
        if c.get("poblacion"):
            rs["total_poblacion"] += c["poblacion"]
        rs["monto_total"] += c["monto_total"]
        rs["total_ocs"] += c["total_ocs"]
        rs["monto_hardware"] += c["monto_hardware"]
        rs["monto_ia"] += c["monto_ia"]
        rs["monto_saas"] += c["monto_saas"]
        rs["monto_cyber"] += c["monto_cyber"]
        rs["monto_telecom"] += c["monto_telecom"]
        if c.get("tiene_lockin_legado"):
            rs["comunas_con_lockin"] += 1
        if c.get("tiene_foss"):
            rs["comunas_con_foss"] += 1
        rs["comunas"].append(c["comuna"])

    for reg, rs in regiones_summary.items():
        p = rs["total_poblacion"]
        rs["gasto_pc"] = round(rs["monto_total"] / p, 0) if p > 0 else 0.0

    regiones_list = sorted(list(regiones_summary.values()), key=lambda x: x["monto_total"], reverse=True)
    REGIONES_JSON.write_text(json.dumps(regiones_list, ensure_ascii=False, indent=2), encoding="utf-8")


def run_verification_suite(con: duckdb.DuckDBPyConnection) -> None:
    """Ejecuta una batería exhaustiva de aserciones de calidad sobre los datos generados."""
    logger.info("=== BATERÍA DE VERIFICACIÓN EMPÍRICA Y CALIDAD DE DATOS ===")

    # 1. Verificación de 0 carpas en la base saneada
    carpas_parquet = con.execute("""
        SELECT count(*) 
        FROM catastro_ti_saneado 
        WHERE lower(texto_descriptivo) LIKE '%carpa%' 
           OR lower(nombre_proveedor) LIKE '%carpa%'
           OR codigo_producto_onu = '30221001'
    """).fetchone()[0]
    assert carpas_parquet == 0, f"Violación de integridad: {carpas_parquet} carpas encontradas en catastro_ti_saneado.parquet"
    logger.info(f"[PASS] 0 carpas en catastro_ti_saneado.parquet (detectadas: {carpas_parquet})")

    # 2. Verificación de contrato 2403-315-SE22 en Peñalolén
    pena_carpa = con.execute("""
        SELECT count(*) 
        FROM catastro_ti_saneado 
        WHERE codigo_orden = '2403-315-SE22'
    """).fetchone()[0]
    assert pena_carpa == 0, "Violación de integridad: Contrato 2403-315-SE22 aún presente en Peñalolén"
    logger.info(f"[PASS] Contrato 2403-315-SE22 de Peñalolén erradicado al 100% (count: {pena_carpa})")

    # 3. Verificación de Peñalolén en comunas_enriched.json
    with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
        comunas = json.load(f)

    comunas_by_name = {c["comuna"]: c for c in comunas}
    pena = comunas_by_name.get("Peñalolén")
    assert pena is not None, "Peñalolén no encontrada en comunas_enriched.json"

    # Verificar que ningún proveedor ni contrato de Peñalolén mencione carpas
    for p in pena["top_proveedores"]:
        assert "carpa" not in p["proveedor"].lower(), f"Proveedor espurio en Peñalolén: {p['proveedor']}"
    for oc in pena["top_contratos_historicos"]:
        assert "carpa" not in oc["descripcion"].lower(), f"Contrato histórico espurio en Peñalolén: {oc['codigo_oc']}"
        assert oc["codigo_oc"] != "2403-315-SE22", "Contrato 2403-315-SE22 presente en top_contratos_historicos"
    for oc in pena["top_contratos_recientes"]:
        assert "carpa" not in oc["descripcion"].lower(), f"Contrato reciente espurio en Peñalolén: {oc['codigo_oc']}"
        assert oc["anio"] >= 2025, f"Contrato reciente con año no 2025/2026: {oc['anio']}"
    logger.info(f"[PASS] Peñalolén saneada: {len(pena['top_proveedores'])} proveedores TI, {len(pena['top_contratos_recientes'])} contratos 2025-2026, 0 carpas.")

    # 4. Verificación de Providencia en comunas_enriched.json
    provi = comunas_by_name.get("Providencia")
    assert provi is not None, "Providencia no encontrada en comunas_enriched.json"
    provi_prov_names = [p["proveedor"].lower() for p in provi["top_proveedores"]]
    assert not any("carpa" in name for name in provi_prov_names), f"Carpas en proveedores de Providencia: {provi_prov_names}"
    assert "advantage" in provi_prov_names[0], f"Proveedor #1 de Providencia no es Advantage: {provi_prov_names[0]}"
    logger.info(f"[PASS] Providencia saneada: Top 1 es {provi['top_proveedores'][0]['proveedor']}, 0 carpas.")

    # 5. Verificación de 0 carpas en TODAS las 345 comunas
    total_carpas_in_json = 0
    for c in comunas:
        for p in c.get("top_proveedores", []):
            if "carpa" in p["proveedor"].lower():
                total_carpas_in_json += 1
        for oc in c.get("top_contratos_historicos", []):
            if "carpa" in oc["descripcion"].lower() or "carpa" in oc["proveedor"].lower():
                total_carpas_in_json += 1
        for oc in c.get("top_contratos_recientes", []):
            if "carpa" in oc["descripcion"].lower() or "carpa" in oc["proveedor"].lower():
                total_carpas_in_json += 1
    assert total_carpas_in_json == 0, f"Violación de integridad: {total_carpas_in_json} menciones de carpas en comunas_enriched.json"
    logger.info("[PASS] 0 contratos ni proveedores de carpas en las 345 comunas de comunas_enriched.json")

    # 6. Cobertura Temporal 2025–2026
    comunas_con_recientes = sum(1 for c in comunas if len(c.get("top_contratos_recientes", [])) > 0)
    logger.info(f"[PASS] Cobertura 2025–2026: {comunas_con_recientes} de {len(comunas)} comunas tienen compras activas 2025–2026.")
    assert comunas_con_recientes >= 300, f"Cobertura temporal 2025-2026 insuficiente: {comunas_con_recientes} comunas"

    # 7. Verificación de archivo de compras saneadas
    assert COMPRAS_JSON_OUT.exists(), f"Archivo no encontrado: {COMPRAS_JSON_OUT}"
    with open(COMPRAS_JSON_OUT, "r", encoding="utf-8") as f:
        compras_data = json.load(f)
    assert len(compras_data) == 345, f"compras_saneadas_por_comuna.json tiene {len(compras_data)} comunas en lugar de 345"
    logger.info(f"[PASS] compras_saneadas_por_comuna.json validado con {len(compras_data)} comunas.")

    # 8. Verificación de integridad comunal: Ovalle y Puerto Montt recuperadas
    ovalle = comunas_by_name.get("Ovalle")
    assert ovalle is not None, "Ovalle no encontrada en comunas_enriched.json"
    assert ovalle["total_ocs"] > 700, f"Ovalle OCs insuficientes tras remediación: {ovalle['total_ocs']}"
    assert ovalle["monto_total"] > 2_000_000_000, f"Ovalle monto insuficiente: {ovalle['monto_total']}"
    logger.info(f"[PASS] Ovalle recuperada: {ovalle['total_ocs']} OCs, ${ovalle['monto_total']:,.0f} CLP.")

    pm = comunas_by_name.get("Puerto Montt")
    assert pm is not None, "Puerto Montt no encontrada en comunas_enriched.json"
    assert pm["total_ocs"] > 1000, f"Puerto Montt OCs insuficientes tras remediación: {pm['total_ocs']}"
    assert pm["monto_total"] > 1_500_000_000, f"Puerto Montt monto insuficiente: {pm['monto_total']}"
    logger.info(f"[PASS] Puerto Montt recuperada: {pm['total_ocs']} OCs, ${pm['monto_total']:,.0f} CLP.")

    # 9. Verificación de cierre de brecha nacional comunal (>= $170.000M CLP)
    total_comunal_monto = sum(c["monto_total"] for c in comunas)
    assert total_comunal_monto >= 170_000_000_000, f"Brecha comunal sin cerrar: ${total_comunal_monto:,.0f} CLP"
    logger.info(f"[PASS] Brecha comunal cerrada: ${total_comunal_monto:,.0f} CLP agregados en 345 comunas.")

    # 10. Verificación de 0 contratos automotrices en Parquet y JSONs
    auto_parquet = con.execute("""
        SELECT count(*) 
        FROM catastro_ti_saneado
        WHERE lower(texto_descriptivo) LIKE '%camioneta%'
           OR lower(nombre_proveedor) LIKE '%neubacar%'
           OR lower(texto_descriptivo) LIKE '%taller mecanico%'
           OR lower(texto_descriptivo) LIKE '%taller mecánico%'
           OR lower(nombre_proveedor) LIKE '%taller mecanico%'
           OR lower(nombre_proveedor) LIKE '%taller mecánico%'
           OR lower(texto_descriptivo) LIKE '%lubricentro%'
           OR lower(nombre_proveedor) LIKE '%lubricentro%'
           OR regexp_matches(lower(texto_descriptivo), '\\b(ecu)\\b')
    """).fetchone()[0]
    assert auto_parquet == 0, f"Detectadas {auto_parquet} órdenes automotrices en catastro_ti_saneado.parquet"
    logger.info("[PASS] 0 órdenes automotrices en catastro_ti_saneado.parquet.")

    # 11. Verificación de 0 contratos no-TI específicos (guitarra, gasfitería, fosas, eléctrica, topografía)
    non_ti_parquet = con.execute("""
        SELECT count(*) 
        FROM catastro_ti_saneado
        WHERE lower(texto_descriptivo) LIKE '%guitarra%'
           OR lower(nombre_proveedor) LIKE '%guitarra%'
           OR codigo_producto_onu IN ('81141806', '81141807', '81151604', '81151603')
           OR lower(texto_descriptivo) LIKE '%gasfiter%'
           OR lower(texto_descriptivo) LIKE '%fosa%septica%'
           OR lower(texto_descriptivo) LIKE '%fosa%séptica%'
           OR lower(texto_descriptivo) LIKE '%alcantarillado%'
    """).fetchone()[0]
    assert non_ti_parquet == 0, f"Detectadas {non_ti_parquet} órdenes no-TI en catastro_ti_saneado.parquet"
    logger.info("[PASS] 0 órdenes de guitarra, gasfitería, fosas, eléctrica o topografía en parquet.")

    # 12. Verificación de saneamiento en Olmué, Paillaco y Lumaco
    olm = comunas_by_name.get("Olmué")
    assert olm is not None, "Olmué no encontrada"
    assert not any("guerra contardo" in p["proveedor"].lower() for p in olm["top_proveedores"]), "Contratista eléctrico en Olmué"

    pai = comunas_by_name.get("Paillaco")
    assert pai is not None, "Paillaco no encontrada"
    for oc in pai.get("top_contratos_recientes", []):
        assert "camioneta" not in oc["descripcion"].lower(), f"Camioneta en recientes de Paillaco: {oc['codigo_oc']}"

    lum = comunas_by_name.get("Lumaco")
    assert lum is not None, "Lumaco no encontrada"
    for oc in lum.get("top_contratos_historicos", []):
        assert "agroveterinaria" not in oc["proveedor"].lower(), f"Agroveterinaria en Lumaco: {oc['proveedor']}"
    logger.info("[PASS] Olmué, Paillaco y Lumaco completamente libres de contaminación no-TI.")

    logger.info("=== TODAS LAS ASERCIONES DE INTEGRIDAD PASARON EXITOSAMENTE ===")


def main():
    logger.info("=== INICIANDO PIPELINE DE SANEAMIENTO Y COBERTURA DE COMPRAS PÚBLICAS TI ===")
    if not PARQUET_IN.exists():
        logger.error(f"Archivo de entrada no existe: {PARQUET_IN}")
        sys.exit(1)

    con = duckdb.connect()

    # Paso 1: Ejecutar filtro de saneamiento
    sanitize_purchases(con)

    # Paso 2: Calcular métricas comunales
    metrics = compute_comuna_metrics(con)

    # Paso 3: Combinar y persistir artefactos
    merge_and_save_data(con, metrics)

    # Paso 4: Ejecutar suite de aserciones
    run_verification_suite(con)

    con.close()
    logger.info("=== PIPELINE COMPLETADO EXITOSAMENTE ===")


if __name__ == "__main__":
    main()
