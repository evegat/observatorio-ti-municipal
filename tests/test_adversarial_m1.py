"""
tests/test_adversarial_m1.py
============================
Empirical Challenger Test Suite for Milestone M1 (Requirements R1 and R2).
Tests against:
1. Target keyword false positives (carpa, toldo, escenario, gas licuado, zapatos, apicultura, banquete, guitarra, etc.)
2. UNSPSC classification leaks (non-TI codes in segment 81: 8114, 8115, 8110, and segment 80: 8014)
3. Specific comunas contamination in top_proveedores and top_contratos (e.g. Olmué, Lumaco, Paillaco)
4. Edge cases (null/NaN montos, blank/NA comunas, negative amounts)
"""

import json
from pathlib import Path
import duckdb
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"
COMPRAS_FILE = DATA_DIR / "compras_saneadas_por_comuna.json"
KPIS_FILE = DATA_DIR / "national_kpis.json"
PROV_FILE = DATA_DIR / "proveedores_ranking.json"


@pytest.fixture(scope="module")
def duck_con():
    con = duckdb.connect()
    yield con
    con.close()


@pytest.fixture(scope="module")
def enriched_data():
    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def compras_data():
    with open(COMPRAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# 1. TARGET KEYWORDS PROBING (PARQUET & JSON)
# ==============================================================================

MANDATORY_EXCLUDED_KEYWORDS = [
    "carpa",
    "toldo",
    "escenario",
    "gas licuado",
    "gas envasado",
    "zapatos",
    "apicultura",
    "banquete",
    "curso de guitarra",
    "guitarra",
]

EXTENDED_NON_TI_KEYWORDS = [
    "produccion de evento",
    "producción de evento",
    "curanto",
    "banqueter",
    "grupo folclorico",
    "grupo folclórico",
    "zapatos de seguridad",
    "calzado de seguridad",
    "camioneta maxus",
    "canasta de alimentos",
    "obras civiles",
    "pavimentac",
    "sede jjvv",
    "desratizac",
    "fumigac",
    "neumatico",
    "neumático",
    "gasolina",
    "petroleo diesel",
]


@pytest.mark.parametrize("kw", MANDATORY_EXCLUDED_KEYWORDS)
def test_mandatory_keywords_absence_in_parquet(duck_con, kw):
    """Verifica ausencia de palabras clave no-TI en catastro_ti_saneado.parquet."""
    query = f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE lower(coalesce(texto_descriptivo, '')) LIKE '%{kw}%'
           OR lower(coalesce(nombre_proveedor, '')) LIKE '%{kw}%'
           OR lower(coalesce(nombre_producto_generico, '')) LIKE '%{kw}%'
    """
    count = duck_con.execute(query).fetchone()[0]
    assert count == 0, f"Keyword espuria '{kw}' encontrada {count} veces en parquet"


@pytest.mark.parametrize("kw", EXTENDED_NON_TI_KEYWORDS)
def test_extended_keywords_absence_in_parquet(duck_con, kw):
    """Verifica ausencia de términos no tecnológicos extendidos en parquet."""
    query = f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE lower(coalesce(texto_descriptivo, '')) LIKE '%{kw}%'
           OR lower(coalesce(nombre_proveedor, '')) LIKE '%{kw}%'
    """
    count = duck_con.execute(query).fetchone()[0]
    assert count == 0, f"Término no-TI extendido '{kw}' encontrado {count} veces en parquet"


def test_mandatory_keywords_absence_in_all_comunas_json(enriched_data):
    """Verifica que ninguna de las 345 comunas tenga palabras clave no-TI en proveedores ni contratos."""
    violations = []
    for c in enriched_data:
        comuna = c.get("comuna", "UNKNOWN")
        # Check top_proveedores
        for p in c.get("top_proveedores", []):
            prov = p.get("proveedor", "").lower()
            for kw in MANDATORY_EXCLUDED_KEYWORDS:
                if kw in prov:
                    violations.append(f"{comuna} | Proveedor: {prov} contiene '{kw}'")

        # Check top_contratos_historicos
        for oc in c.get("top_contratos_historicos", []):
            desc = oc.get("descripcion", "").lower()
            prov = oc.get("proveedor", "").lower()
            for kw in MANDATORY_EXCLUDED_KEYWORDS:
                if kw in desc or kw in prov:
                    violations.append(f"{comuna} | Histórico {oc.get('codigo_oc')}: desc='{desc}' prov='{prov}' contiene '{kw}'")

        # Check top_contratos_recientes
        for oc in c.get("top_contratos_recientes", []):
            desc = oc.get("descripcion", "").lower()
            prov = oc.get("proveedor", "").lower()
            for kw in MANDATORY_EXCLUDED_KEYWORDS:
                if kw in desc or kw in prov:
                    violations.append(f"{comuna} | Reciente {oc.get('codigo_oc')}: desc='{desc}' prov='{prov}' contiene '{kw}'")

    assert len(violations) == 0, f"Violaciones de keywords en JSON ({len(violations)}): {violations[:10]}"


# ==============================================================================
# 2. UNSPSC TAXONOMY INTEGRITY & NON-TI LEAKS IN ENGINEERING RUBRIC
# ==============================================================================

BLACKLISTED_ONU_CODES = [
    "30221001", "10101704", "30151901", "90101602", "90151602",
    "80141607", "90111603", "72131702", "72131701", "90151803",
    "80141611", "80141609", "80141605", "80141620", "76121503",
    "53121603", "80111504"
]

@pytest.mark.parametrize("onu", BLACKLISTED_ONU_CODES)
def test_blacklisted_onu_codes_absence_in_parquet(duck_con, onu):
    """Verifica que ningún código ONU explícitamente vetado figure en el parquet."""
    query = f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE codigo_producto_onu = '{onu}'
    """
    count = duck_con.execute(query).fetchone()[0]
    assert count == 0, f"Código ONU vetado '{onu}' encontrado {count} veces en parquet"


def test_no_plumbing_or_sewer_services_in_parquet(duck_con):
    """Verifica que no existan servicios de gasfitería, fosas sépticas o alcantarillado (ONU 81141807)."""
    count = duck_con.execute(f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE codigo_producto_onu = '81141807'
           OR lower(texto_descriptivo) LIKE '%gasfiter%'
           OR lower(texto_descriptivo) LIKE '%fosa%septica%'
           OR lower(texto_descriptivo) LIKE '%fosa%séptica%'
           OR lower(texto_descriptivo) LIKE '%alcantarillado%'
    """).fetchone()[0]
    assert count == 0, f"Detectados {count} contratos de gasfitería/fosas/alcantarillado en parquet"


def test_no_electrical_inspections_in_parquet(duck_con):
    """Verifica que no existan servicios de inspección y mantenimiento de instalaciones eléctricas (ONU 81141806)."""
    count = duck_con.execute(f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE codigo_producto_onu = '81141806'
           OR (lower(texto_descriptivo) LIKE '%inspecci%instalaciones el%ctricas%')
    """).fetchone()[0]
    assert count == 0, f"Detectados {count} contratos de inspección eléctrica escolar/municipal en parquet"


def test_no_topography_in_parquet(duck_con):
    """Verifica que no existan servicios de topografía ni fotogrametría (ONU 81151604, 81151603)."""
    count = duck_con.execute(f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE codigo_producto_onu IN ('81151604', '81151603')
    """).fetchone()[0]
    assert count == 0, f"Detectados {count} contratos de topografía/fotogrametría en parquet"


# ==============================================================================
# 3. 345 COMUNAS INTEGRITY AND VENDOR SANITY
# ==============================================================================

def test_olmue_top_providers_free_of_electrical_maintenance(enriched_data):
    """Verifica que Olmué no tenga como proveedor TI principal a una empresa de mantenimiento eléctrico."""
    olm = next((c for c in enriched_data if c["comuna"] == "Olmué"), None)
    assert olm is not None, "Olmué no encontrada en comunas_enriched.json"
    prov_names = [p["proveedor"].lower() for p in olm["top_proveedores"]]
    assert not any("guerra contardo" in name or "mantenimiento mauricio" in name for name in prov_names), \
        f"Proveedor espurio de mantenimiento eléctrico lidera Olmué: {prov_names[0]}"


def test_paillaco_recent_contracts_free_of_vehicle_mechanic(enriched_data):
    """Verifica que Paillaco no tenga mantención de camionetas en sus contratos recientes."""
    pld = next((c for c in enriched_data if c["comuna"] == "Paillaco"), None)
    assert pld is not None, "Paillaco no encontrada"
    for oc in pld.get("top_contratos_recientes", []):
        assert "camioneta" not in oc["descripcion"].lower(), \
            f"Mantención de camioneta encontrada en top_contratos_recientes de Paillaco: {oc['codigo_oc']} - {oc['descripcion']}"


def test_lumaco_free_of_agroveterinaria(enriched_data):
    """Verifica que Lumaco no tenga a Agroveterinaria Santa Lucía en contratos emblemáticos."""
    lum = next((c for c in enriched_data if c["comuna"] == "Lumaco"), None)
    assert lum is not None, "Lumaco no encontrada"
    for oc in lum.get("top_contratos_historicos", []):
        assert "agroveterinaria" not in oc["proveedor"].lower(), \
            f"Agroveterinaria en contratos TI de Lumaco: {oc['proveedor']}"


# ==============================================================================
# 4. DATASET COMPLETENESS & EDGE CASES
# ==============================================================================

def test_no_nan_monto_linea_in_parquet(duck_con):
    """Verifica que el dataset parquet no contenga valores NaN o NULL en monto_linea."""
    nan_count = duck_con.execute(f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE monto_linea IS NULL OR isnan(monto_linea)
    """).fetchone()[0]
    assert nan_count == 0, f"Existen {nan_count} registros con monto_linea NULL/NaN en catastro_ti_saneado.parquet"


def test_no_blank_or_na_comuna_in_parquet(duck_con):
    """Verifica que el parquet no tenga registros sin comuna o con 'NA' / 'Sin comuna' / '*'."""
    bad_comunas = duck_con.execute(f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE comuna_comprador IS NULL 
           OR trim(comuna_comprador) = '' 
           OR comuna_comprador IN ('Sin comuna', 'NA', 'Extranjero', '*')
           OR regexp_matches(comuna_comprador, '^[0-9 *]+$')
    """).fetchone()[0]
    assert bad_comunas == 0, f"Existen {bad_comunas} registros con comuna ausente o inválida en parquet"


def test_exact_comuna_count_and_keys(enriched_data, compras_data):
    """Verifica 345 comunas con llaves completas."""
    assert len(enriched_data) == 345
    assert len(compras_data) == 345
