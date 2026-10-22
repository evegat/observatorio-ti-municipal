"""Sincronizador Automático de Dotación y Métricas de RRHH Municipal (P166 -> Observatorio TI).
Actualiza data/comunas_enriched.json con las métricas observadas reales de Transparencia Activa CPLT.
"""
from __future__ import annotations

import json
import logging
import unicodedata
from pathlib import Path
import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SyncRRHH")

BASE_DIR = Path(__file__).resolve().parents[1]
ENRICHED_JSON = BASE_DIR / "data/comunas_enriched.json"
P166_DUCKDB = Path(r"D:\Proyectos\P166 - Personal Municipal de Chile\data\personal_municipal.duckdb")

def normalizar(txt: str) -> str:
    n = unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8").lower()
    return "".join(c for c in n if c.isalnum() or c == " ").strip()

def main():
    if not P166_DUCKDB.exists():
        logger.error(f"Base DuckDB P166 no encontrada en: {P166_DUCKDB}")
        return

    logger.info("Conectando a personal_municipal.duckdb...")
    con = duckdb.connect(str(P166_DUCKDB), read_only=True)

    query = """
    WITH latest_obs AS (
        SELECT 
            comuna_id,
            MAX(anio * 100 + mes) as latest_period
        FROM rrhh_personal
        GROUP BY comuna_id
    )
    SELECT 
        p.comuna_id,
        COUNT(DISTINCT p.id_persona_hash) as dotacion_total,
        COUNT(DISTINCT CASE WHEN p.calidad_juridica = 'PLANTA' THEN p.id_persona_hash END) as planta,
        COUNT(DISTINCT CASE WHEN p.calidad_juridica = 'CONTRATA' THEN p.id_persona_hash END) as contrata,
        COUNT(DISTINCT CASE WHEN p.calidad_juridica = 'HONORARIOS' THEN p.id_persona_hash END) as honorarios,
        
        -- TI Total
        COUNT(DISTINCT CASE WHEN (
            p.cargo_funcion ILIKE '%informat%' OR p.cargo_funcion ILIKE '%sistema%' OR 
            p.cargo_funcion ILIKE '%comput%' OR p.cargo_funcion ILIKE '%software%' OR 
            p.cargo_funcion ILIKE '%programad%' OR p.cargo_funcion ILIKE '%ciberseguridad%' OR
            p.cargo_funcion ILIKE '%redes%' OR p.cargo_funcion ILIKE '%soporte tecnic%' OR
            p.profesion ILIKE '%informat%' OR p.profesion ILIKE '%comput%' OR p.profesion ILIKE '%software%'
        ) THEN p.id_persona_hash END) as dotacion_ti,

        -- TI Planta
        COUNT(DISTINCT CASE WHEN (
            p.cargo_funcion ILIKE '%informat%' OR p.cargo_funcion ILIKE '%sistema%' OR 
            p.cargo_funcion ILIKE '%comput%' OR p.profesion ILIKE '%informat%'
        ) AND p.calidad_juridica = 'PLANTA' THEN p.id_persona_hash END) as ti_planta,

        -- TI Contrata
        COUNT(DISTINCT CASE WHEN (
            p.cargo_funcion ILIKE '%informat%' OR p.cargo_funcion ILIKE '%sistema%' OR 
            p.cargo_funcion ILIKE '%comput%' OR p.profesion ILIKE '%informat%'
        ) AND p.calidad_juridica = 'CONTRATA' THEN p.id_persona_hash END) as ti_contrata,

        -- TI Honorarios
        COUNT(DISTINCT CASE WHEN (
            p.cargo_funcion ILIKE '%informat%' OR p.cargo_funcion ILIKE '%sistema%' OR 
            p.cargo_funcion ILIKE '%comput%' OR p.profesion ILIKE '%informat%'
        ) AND p.calidad_juridica = 'HONORARIOS' THEN p.id_persona_hash END) as ti_honorarios,

        -- Remuneración mediana general
        MEDIAN(p.remuneracion_bruta) as remun_mediana,

        -- Remuneración mediana TI
        MEDIAN(CASE WHEN 
            p.cargo_funcion ILIKE '%informat%' OR p.cargo_funcion ILIKE '%sistema%' OR 
            p.cargo_funcion ILIKE '%comput%' OR p.profesion ILIKE '%informat%'
        THEN p.remuneracion_bruta END) as remun_mediana_ti

    FROM rrhh_personal p
    JOIN latest_obs lo ON p.comuna_id = lo.comuna_id AND (p.anio * 100 + p.mes) = lo.latest_period
    GROUP BY p.comuna_id
    """

    rows = con.execute(query).fetchall()
    con.close()
    logger.info(f"Métricas extraídas para {len(rows)} comunas observadas.")

    # Mapear métricas por comuna normalizada
    rrhh_map = {}
    for r in rows:
        cid = str(r[0]).strip().lower()
        norm_key = normalizar(cid)
        rrhh_map[norm_key] = {
            "dotacion_total": r[1],
            "dotacion_planta": r[2],
            "dotacion_contrata": r[3],
            "dotacion_honorarios": r[4],
            "dotacion_ti": r[5],
            "ti_planta": r[6],
            "ti_contrata": r[7],
            "ti_honorarios": r[8],
            "remun_mediana": round(r[9] or 0.0, 0),
            "remun_mediana_ti": round(r[10] or 0.0, 0),
        }

    # Cargar comunas_enriched.json
    data = json.loads(ENRICHED_JSON.read_text(encoding="utf-8"))
    logger.info(f"Cargadas {len(data)} comunas de {ENRICHED_JSON.name}")

    actualizadas = 0
    mantenidas_modelo = 0

    for c in data:
        c_nom = c.get("comuna", "")
        c_raw = c.get("comuna_raw", "")
        k1 = normalizar(c_nom)
        k2 = normalizar(c_raw)

        m = rrhh_map.get(k1) or rrhh_map.get(k2)
        if m and m["dotacion_total"] > 0:
            tot = m["dotacion_total"]
            planta = m["dotacion_planta"]
            contrata = m["dotacion_contrata"]
            hono = m["dotacion_honorarios"]
            ti_tot = m["dotacion_ti"]
            ti_formal = m["ti_planta"] + m["ti_contrata"]
            ti_hono = m["ti_honorarios"]

            c["dotacion_total"] = tot
            c["dotacion_planta"] = planta
            c["dotacion_contrata"] = contrata
            c["dotacion_honorarios"] = hono
            c["pct_honorarios"] = round((hono / tot * 100), 1) if tot > 0 else 0.0
            c["pct_planta_contrata"] = round(((planta + contrata) / tot * 100), 1) if tot > 0 else 0.0
            
            c["dotacion_ti"] = ti_tot
            c["dotacion_ti_formal"] = ti_formal
            c["dotacion_ti_honorarios"] = ti_hono

            if m["remun_mediana"] > 0:
                c["remuneracion_mediana_clp"] = m["remun_mediana"]
                c["gasto_remuneraciones_anual_clp"] = round(tot * m["remun_mediana"] * 12, 0)

            remun_ti = m["remun_mediana_ti"] if m["remun_mediana_ti"] > 0 else m["remun_mediana"]
            c["gasto_rrhh_ti_anual"] = round(ti_tot * remun_ti * 12, 0)

            # Recalcular ret_ratio si tiene gasto TI y gasto RRHH TI
            monto_ti_tech = c.get("monto_total", 0.0)
            if c["gasto_rrhh_ti_anual"] > 0:
                c["ret_ratio"] = round(monto_ti_tech / c["gasto_rrhh_ti_anual"], 2)

            c["fuente_rrhh"] = "CPLT Transparencia Activa (Observado)"
            actualizadas += 1
        else:
            mantenidas_modelo += 1

    ENRICHED_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Sincronización completada:")
    logger.info(f" - Comunas con datos CPLT observados reales: {actualizadas}")
    logger.info(f" - Comunas con modelo paramétrico complementario: {mantenidas_modelo}")

if __name__ == "__main__":
    main()
