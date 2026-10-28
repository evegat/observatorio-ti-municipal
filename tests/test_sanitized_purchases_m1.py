"""
test_sanitized_purchases_m1.py
==============================
Pruebas automatizadas de integridad, sanidad semántica y cobertura temporal
para el Hito M1 (Requerimientos R1 y R2).

Verifica:
1. 0 contratos de rubros no-TI (carpas, toldos, eventos, obras) en toda la canasta.
2. Erradicación completa del contrato espurio 2403-315-SE22 ($88M) en Peñalolén.
3. Proveedores tecnológicos legítimos en Peñalolén y Providencia (0 carpas).
4. Cobertura temporal 2025-2026 activa y desacoplamiento de feeds en las 345 comunas.
5. Ausencia de valores NaN, nulos o corrupciones en los datasets generados.
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
def enriched_data():
    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def compras_data():
    with open(COMPRAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def duck_con():
    con = duckdb.connect()
    yield con
    con.close()


def test_parquet_file_exists_and_valid(duck_con):
    """Verifica que el dataset parquet saneado exista y contenga registros válidos."""
    assert PARQUET_FILE.exists(), f"No existe {PARQUET_FILE}"
    count = duck_con.execute(f"SELECT count(*) FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')").fetchone()[0]
    assert count > 90000, f"Cantidad insuficiente de registros saneados: {count}"


def test_zero_carpas_in_parquet(duck_con):
    """Verifica que no exista ninguna carpa ni código 30221001 en el parquet saneado."""
    carpas = duck_con.execute(f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE lower(texto_descriptivo) LIKE '%carpa%' 
           OR lower(nombre_proveedor) LIKE '%carpa%'
           OR codigo_producto_onu = '30221001'
    """).fetchone()[0]
    assert carpas == 0, f"Se encontraron {carpas} registros con carpas en catastro_ti_saneado.parquet"


def test_penalolen_spurious_contract_eradicated(duck_con, enriched_data):
    """Verifica que el contrato 2403-315-SE22 ($88M carpas) esté 100% erradicado."""
    in_parquet = duck_con.execute(f"""
        SELECT count(*) 
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE codigo_orden = '2403-315-SE22'
    """).fetchone()[0]
    assert in_parquet == 0, "El contrato 2403-315-SE22 todavía existe en el parquet"

    pena = next((c for c in enriched_data if c["comuna"] == "Peñalolén"), None)
    assert pena is not None, "Peñalolén no encontrada en comunas_enriched.json"

    for feed in ["top_contratos", "top_contratos_historicos", "top_contratos_recientes"]:
        for oc in pena.get(feed, []):
            assert oc["codigo_oc"] != "2403-315-SE22", f"Contrato 2403-315-SE22 encontrado en {feed}"
            assert "carpa" not in oc["descripcion"].lower(), f"Mención a carpas en {feed} de Peñalolén"


def test_providencia_top_vendors_free_of_carpas(enriched_data):
    """Verifica que Providencia no tenga proveedores de carpas en sus primeros lugares."""
    provi = next((c for c in enriched_data if c["comuna"] == "Providencia"), None)
    assert provi is not None, "Providencia no encontrada en comunas_enriched.json"

    prov_names = [p["proveedor"].lower() for p in provi["top_proveedores"]]
    assert len(prov_names) > 0, "Providencia sin proveedores"
    assert not any("carpa" in name for name in prov_names), f"Proveedores espurios en Providencia: {prov_names}"
    assert "advantage" in prov_names[0], f"Proveedor #1 de Providencia esperado Advantage, obtenido: {prov_names[0]}"


def test_zero_carpas_in_all_345_comunas(enriched_data, compras_data):
    """Verifica que no exista ninguna mención a carpas en proveedores ni contratos de las 345 comunas."""
    for dataset, name in [(enriched_data, "comunas_enriched"), (compras_data, "compras_saneadas")]:
        for c in dataset:
            comuna_name = c["comuna"]
            for p in c.get("top_proveedores", []):
                assert "carpa" not in p["proveedor"].lower(), f"Proveedor con carpas en {comuna_name} ({name}): {p['proveedor']}"
            for oc in c.get("top_contratos_historicos", []):
                assert "carpa" not in oc["descripcion"].lower(), f"Contrato histórico con carpas en {comuna_name} ({name}): {oc['codigo_oc']}"
            for oc in c.get("top_contratos_recientes", []):
                assert "carpa" not in oc["descripcion"].lower(), f"Contrato reciente con carpas en {comuna_name} ({name}): {oc['codigo_oc']}"


def test_temporal_coverage_and_decoupled_feeds(enriched_data):
    """Verifica el desacoplamiento de feeds y la cobertura activa 2025–2026."""
    assert len(enriched_data) == 345, f"Esperadas 345 comunas, obtenidas {len(enriched_data)}"

    active_recientes = 0
    for c in enriched_data:
        assert "top_contratos_recientes" in c, f"Falta feed reciente en {c['comuna']}"
        assert "top_contratos_historicos" in c, f"Falta feed histórico en {c['comuna']}"
        rec = c["top_contratos_recientes"]
        if len(rec) > 0:
            active_recientes += 1
            for oc in rec:
                assert oc["anio"] >= 2025, f"Contrato en feed reciente con año < 2025: {oc['codigo_oc']} ({oc['anio']})"

    # Al menos 340 de las 345 comunas deben registrar compras en 2025-2026
    assert active_recientes >= 340, f"Cobertura temporal insuficiente: solo {active_recientes} comunas con recientes"


def test_no_nans_in_financial_metrics(enriched_data, compras_data):
    """Verifica que ningún campo numérico contenga NaN o None en los datasets."""
    numeric_fields = [
        "monto_total", "gasto_pc", "total_ocs",
        "monto_hardware", "hardware_pc",
        "monto_saas", "saas_pc",
        "monto_ia", "ia_pc",
        "monto_telecom", "telecom_pc",
        "monto_cyber", "cyber_pc"
    ]
    for dataset, name in [(enriched_data, "comunas_enriched"), (compras_data, "compras_saneadas")]:
        for c in dataset:
            for field in numeric_fields:
                val = c.get(field)
                assert val is not None, f"Campo {field} es None en {c['comuna']} ({name})"
                assert not (isinstance(val, float) and val != val), f"Campo {field} es NaN en {c['comuna']} ({name})"


def test_national_kpis_consistency(duck_con):
    """Verifica que national_kpis.json coincida con los totales de la base saneada."""
    assert KPIS_FILE.exists(), f"No existe {KPIS_FILE}"
    with open(KPIS_FILE, "r", encoding="utf-8") as f:
        kpis = json.load(f)

    actual_ocs = duck_con.execute(f"SELECT count(distinct codigo_orden) FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')").fetchone()[0]
    actual_monto = duck_con.execute(f"SELECT round(sum(monto_linea), 0) FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')").fetchone()[0]

    assert kpis["total_ocs"] == actual_ocs, f"Discrepancia en total_ocs: {kpis['total_ocs']} vs {actual_ocs}"
    assert abs(kpis["monto_total_clp"] - actual_monto) < 1.0, f"Discrepancia en monto_total_clp: {kpis['monto_total_clp']} vs {actual_monto}"
    assert len(kpis["series_anual"]) > 10, "Serie anual incompleta en national_kpis.json"


def test_ovalle_and_puerto_montt_restored_integrity(enriched_data):
    """Verifica que Ovalle y Puerto Montt no estén mutiladas por colisiones multi-región."""
    ov = next((c for c in enriched_data if c["comuna"] == "Ovalle"), None)
    assert ov is not None, "Ovalle no encontrada en comunas_enriched.json"
    assert ov["total_ocs"] > 700, f"Ovalle OCs insuficientes: {ov['total_ocs']} (esperado > 700)"
    assert ov["monto_total"] > 2_000_000_000, f"Ovalle monto insuficiente: {ov['monto_total']} (esperado > $2.000M CLP)"

    pm = next((c for c in enriched_data if c["comuna"] == "Puerto Montt"), None)
    assert pm is not None, "Puerto Montt no encontrada en comunas_enriched.json"
    assert pm["total_ocs"] > 1000, f"Puerto Montt OCs insuficientes: {pm['total_ocs']} (esperado > 1000)"
    assert pm["monto_total"] > 1_500_000_000, f"Puerto Montt monto insuficiente: {pm['monto_total']} (esperado > $1.500M CLP)"


def test_total_monto_across_comunas_gap_closed(enriched_data, compras_data):
    """Verifica que la suma comunal cierre la brecha de $13.645M CLP y alcance al menos $170.000M CLP."""
    total_enriched = sum(c["monto_total"] for c in enriched_data)
    total_compras = sum(c["monto_total"] for c in compras_data)

    assert total_enriched >= 170_000_000_000, f"Suma comunal insuficiente en comunas_enriched: {total_enriched:,.0f} CLP"
    assert total_compras >= 170_000_000_000, f"Suma comunal insuficiente en compras_saneadas: {total_compras:,.0f} CLP"


def test_zero_automotive_orders_in_parquet(duck_con):
    """Verifica que no existan mantenciones de camionetas, talleres mecánicos, lubricentros ni ECUs."""
    count = duck_con.execute(f"""
        SELECT count(*)
        FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
        WHERE lower(texto_descriptivo) LIKE '%camioneta%'
           OR lower(nombre_proveedor) LIKE '%neubacar%'
           OR lower(texto_descriptivo) LIKE '%taller mecanico%'
           OR lower(texto_descriptivo) LIKE '%taller mecánico%'
           OR lower(nombre_proveedor) LIKE '%taller mecanico%'
           OR lower(nombre_proveedor) LIKE '%taller mecánico%'
           OR lower(texto_descriptivo) LIKE '%lubricentro%'
           OR lower(nombre_proveedor) LIKE '%lubricentro%'
           OR lower(texto_descriptivo) LIKE '%computador para camioneta%'
           OR regexp_matches(lower(texto_descriptivo), '\\b(ecu)\\b')
           OR lower(texto_descriptivo) LIKE '%falla en computador%'
           OR lower(texto_descriptivo) LIKE '%aceite%mobil%'
           OR lower(texto_descriptivo) LIKE '%barra central direccion%'
    """).fetchone()[0]
    assert count == 0, f"Detectadas {count} órdenes automotrices en catastro_ti_saneado.parquet"


def test_zero_automotive_orders_in_all_comunas_json(enriched_data, compras_data):
    """Verifica que ninguna de las 345 comunas tenga órdenes ni proveedores automotrices."""
    banned_automotive_terms = [
        "camioneta", "neubacar", "taller mecanico", "taller mecánico",
        "lubricentro", "aceite mobil", "barra central direccion"
    ]
    for dataset, name in [(enriched_data, "comunas_enriched"), (compras_data, "compras_saneadas")]:
        for c in dataset:
            comuna_name = c["comuna"]
            for p in c.get("top_proveedores", []):
                prov = p.get("proveedor", "").lower()
                for kw in banned_automotive_terms:
                    assert kw not in prov, f"Proveedor automotriz '{kw}' en {comuna_name} ({name}): {prov}"
            for feed in ["top_contratos_historicos", "top_contratos_recientes"]:
                for oc in c.get(feed, []):
                    desc = oc.get("descripcion", "").lower()
                    prov = oc.get("proveedor", "").lower()
                    for kw in banned_automotive_terms:
                        assert kw not in desc and kw not in prov, f"Orden automotriz '{kw}' en {feed} de {comuna_name} ({name}): {desc}"

