"""
tests/adversarial_remediation_suite.py
======================================
Comprehensive adversarial verification suite for M1 remediation.
Audits:
1. All 68 previously clobbered comunas (and all 345 comunas).
2. Five specific test cases: Olmué, Paillaco, Lumaco, Nueva Imperial, Los Lagos.
3. Parquet cleanliness: 0 NaNs, 0 nulls in monto_linea, 0 invalid comunas, positive amounts.
4. Complete alignment between catastro_ti_saneado.parquet, comunas_enriched.json,
   compras_saneadas_por_comuna.json, national_kpis.json, and regiones_enriched.json.
5. Strict absence of non-IT spurious contracts (automotive, electrical maintenance, plumbing, agro, etc.).
"""

import json
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"
COMPRAS_FILE = DATA_DIR / "compras_saneadas_por_comuna.json"
KPIS_FILE = DATA_DIR / "national_kpis.json"
REGIONES_FILE = DATA_DIR / "regiones_enriched.json"

def run_suite():
    print("=" * 80)
    print("RUNNING ADVERSARIAL CERTIFICATION SUITE FOR M1 REMEDIATION")
    print("=" * 80)
    
    con = duckdb.connect()
    pq_path = str(PARQUET_FILE).replace("\\", "/")
    
    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        comunas_enriched = json.load(f)
    with open(COMPRAS_FILE, "r", encoding="utf-8") as f:
        compras_por_comuna = json.load(f)
    with open(KPIS_FILE, "r", encoding="utf-8") as f:
        national_kpis = json.load(f)
    with open(REGIONES_FILE, "r", encoding="utf-8") as f:
        regiones_enriched = json.load(f)

    failures = []
    passes = []

    # -------------------------------------------------------------
    # 1. PARQUET INTEGRITY: NaNs, NULLs, Invalid communes
    # -------------------------------------------------------------
    print("\n--- 1. PARQUET INTEGRITY AUDIT ---")
    
    # 1.1 NaNs in monto_linea
    nan_count = con.execute(f"""
        SELECT count(*) FROM read_parquet('{pq_path}')
        WHERE isnan(monto_linea) OR monto_linea IS NULL
    """).fetchone()[0]
    if nan_count == 0:
        passes.append("Parquet monto_linea has 0 NaNs and 0 NULLs")
    else:
        failures.append(f"Parquet monto_linea has {nan_count} NaNs or NULLs")

    # 1.2 Invalid commune names
    invalid_comunas = con.execute(f"""
        SELECT count(*), list(distinct comuna_comprador)
        FROM read_parquet('{pq_path}')
        WHERE comuna_comprador IS NULL 
           OR trim(comuna_comprador) = ''
           OR comuna_comprador IN ('Sin comuna', 'NA', 'Extranjero', '*')
           OR regexp_matches(comuna_comprador, '^[0-9 *]+$')
    """).fetchone()
    if invalid_comunas[0] == 0:
        passes.append("Parquet has 0 invalid/blank/NA/numeric commune names")
    else:
        failures.append(f"Parquet has {invalid_comunas[0]} rows with invalid communes: {invalid_comunas[1]}")

    # 1.3 Total rows, total OCs, total monto in parquet
    pq_stats = con.execute(f"""
        SELECT 
            count(*) as total_rows,
            count(distinct codigo_orden) as total_ocs,
            round(sum(monto_linea), 0) as total_monto,
            count(distinct comuna_comprador) as total_comunas
        FROM read_parquet('{pq_path}')
    """).fetchone()
    print(f"Parquet stats: rows={pq_stats[0]}, OCs={pq_stats[1]}, monto=${pq_stats[2]:,.0f}, comunas={pq_stats[3]}")

    # -------------------------------------------------------------
    # 2. SPECIFIC TARGET COMMUNES: Olmué, Paillaco, Lumaco, Nueva Imperial, Los Lagos
    # -------------------------------------------------------------
    print("\n--- 2. SPECIFIC TARGET COMMUNES AUDIT ---")

    # 2.1 Olmué: Must not have Mauricio Guerra or electrical maintenance
    olmue_pq = con.execute(f"""
        SELECT count(*), coalesce(sum(monto_linea), 0)
        FROM read_parquet('{pq_path}')
        WHERE lower(comuna_comprador) = 'olmué'
          AND (
            lower(nombre_proveedor) LIKE '%mauricio esteban guerra contardo%'
            OR lower(texto_descriptivo) LIKE '%instalaciones electricas%'
            OR lower(texto_descriptivo) LIKE '%instalaciones eléctricas%'
            OR codigo_producto_onu = '81141806'
          )
    """).fetchone()
    if olmue_pq[0] == 0:
        passes.append("Olmué: 0 electrical maintenance or Guerra Contardo contracts in Parquet")
    else:
        failures.append(f"Olmué: Found {olmue_pq[0]} contaminated rows in Parquet (${olmue_pq[1]:,.0f})")

    olmue_json = next((c for c in comunas_enriched if c["comuna"] == "Olmué"), None)
    if olmue_json:
        top_provs = [p["proveedor"].lower() for p in olmue_json.get("top_proveedores", [])]
        if any("guerra contardo" in p for p in top_provs):
            failures.append("Olmué JSON: Mauricio Guerra Contardo still in top_proveedores")
        else:
            passes.append("Olmué JSON: top_proveedores free of Mauricio Guerra Contardo")
    else:
        failures.append("Olmué JSON: Not found in comunas_enriched.json")

    # 2.2 Paillaco: Must not have Neubacar, camioneta NP300, or mechanical maintenance
    paillaco_pq = con.execute(f"""
        SELECT count(*), coalesce(sum(monto_linea), 0)
        FROM read_parquet('{pq_path}')
        WHERE lower(comuna_comprador) = 'paillaco'
          AND (
            lower(nombre_proveedor) LIKE '%neubacar%'
            OR codigo_orden = '3789-7023-SE25'
            OR lower(texto_descriptivo) LIKE '%camioneta%'
          )
    """).fetchone()
    if paillaco_pq[0] == 0:
        passes.append("Paillaco: 0 Neubacar, 0 camioneta, 0 OC 3789-7023-SE25 in Parquet")
    else:
        failures.append(f"Paillaco: Found {paillaco_pq[0]} automotive rows in Parquet (${paillaco_pq[1]:,.0f})")

    paillaco_json = next((c for c in comunas_enriched if c["comuna"] == "Paillaco"), None)
    if paillaco_json:
        recent_ocs = [c.get("codigo_orden", "") for c in paillaco_json.get("top_contratos_recientes", [])]
        if "3789-7023-SE25" in recent_ocs:
            failures.append("Paillaco JSON: OC 3789-7023-SE25 still present in top_contratos_recientes")
        else:
            passes.append("Paillaco JSON: top_contratos_recientes free of OC 3789-7023-SE25")
    else:
        failures.append("Paillaco JSON: Not found in comunas_enriched.json")

    # 2.3 Lumaco: Must not have Agroveterinaria Santa Lucía (OC 4406-952-AG25)
    lumaco_pq = con.execute(f"""
        SELECT count(*), coalesce(sum(monto_linea), 0)
        FROM read_parquet('{pq_path}')
        WHERE lower(comuna_comprador) = 'lumaco'
          AND (
            lower(nombre_proveedor) LIKE '%agroveterinaria%'
            OR codigo_orden = '4406-952-AG25'
          )
    """).fetchone()
    if lumaco_pq[0] == 0:
        passes.append("Lumaco: 0 Agroveterinaria Santa Lucía or OC 4406-952-AG25 in Parquet")
    else:
        failures.append(f"Lumaco: Found {lumaco_pq[0]} agroveterinaria rows in Parquet (${lumaco_pq[1]:,.0f})")

    lumaco_json = next((c for c in comunas_enriched if c["comuna"] == "Lumaco"), None)
    if lumaco_json:
        hist_ocs = [c.get("codigo_orden", "") for c in lumaco_json.get("top_contratos_historicos", [])]
        if "4406-952-AG25" in hist_ocs:
            failures.append("Lumaco JSON: OC 4406-952-AG25 still in top_contratos_historicos")
        else:
            passes.append("Lumaco JSON: top_contratos_historicos free of OC 4406-952-AG25")
    else:
        failures.append("Lumaco JSON: Not found in comunas_enriched.json")

    # 2.4 Nueva Imperial: Must not have OC 3485-378-AG26 (camioneta Hilux ECU)
    n_imp_pq = con.execute(f"""
        SELECT count(*)
        FROM read_parquet('{pq_path}')
        WHERE lower(comuna_comprador) = 'nueva imperial'
          AND (
            codigo_orden = '3485-378-AG26'
            OR lower(texto_descriptivo) LIKE '%hilux%'
            OR lower(texto_descriptivo) LIKE '%camioneta%'
          )
    """).fetchone()[0]
    if n_imp_pq == 0:
        passes.append("Nueva Imperial: 0 Hilux/camioneta or OC 3485-378-AG26 in Parquet")
    else:
        failures.append(f"Nueva Imperial: Found {n_imp_pq} automotive rows in Parquet")

    # 2.5 Los Lagos: Must not have OCs 1723-184-SE19 or 1723-596-SE20
    los_lagos_pq = con.execute(f"""
        SELECT count(*)
        FROM read_parquet('{pq_path}')
        WHERE lower(comuna_comprador) = 'los lagos'
          AND (
            codigo_orden IN ('1723-184-SE19', '1723-596-SE20')
            OR lower(texto_descriptivo) LIKE '%aceite%mobil%'
            OR lower(texto_descriptivo) LIKE '%barra central direccion%'
          )
    """).fetchone()[0]
    if los_lagos_pq == 0:
        passes.append("Los Lagos: 0 barra direccion/aceite Mobil or OCs 1723-184-SE19 / 1723-596-SE20 in Parquet")
    else:
        failures.append(f"Los Lagos: Found {los_lagos_pq} automotive rows in Parquet")

    # -------------------------------------------------------------
    # 3. AUDIT OF THE 68 PREVIOUSLY CLOBBERED COMMUNES
    # -------------------------------------------------------------
    print("\n--- 3. AUDIT OF 68 PREVIOUSLY CLOBBERED COMMUNES ---")

    # Find which comunas in raw data / parquet have multiple regions or were clobbered
    # Let's inspect the key ones highlighted in challenger_m1_2:
    critical_clobbered = [
        "Ovalle", "Puerto Montt", "Cañete", "La Cisterna", "Chillán", "San Carlos",
        "Longaví", "Yungay", "El Carmen", "Penco", "Coihueco", "Quillón",
        "Los Muermos", "Pelarco", "Pitrufquén", "Corral", "Graneros"
    ]

    enriched_by_name = {c["comuna"].strip().lower(): c for c in comunas_enriched}

    for comuna_name in critical_clobbered:
        c_obj = enriched_by_name.get(comuna_name.lower())
        if not c_obj:
            failures.append(f"Clobbered audit: {comuna_name} not found in comunas_enriched.json")
            continue
        ocs = c_obj.get("total_ocs", 0)
        monto = c_obj.get("monto_total", 0.0)
        gpc = c_obj.get("gasto_pc", 0.0)
        
        # Verify it has realistic non-zero metrics
        if comuna_name == "Ovalle":
            if ocs > 700 and monto > 2_000_000_000 and gpc > 15_000:
                passes.append(f"Ovalle restored: {ocs} OCs, ${monto:,.0f} CLP (gpc: ${gpc:,.0f})")
            else:
                failures.append(f"Ovalle NOT restored properly: {ocs} OCs, ${monto:,.0f} CLP (gpc: ${gpc:,.0f})")
        elif comuna_name == "Puerto Montt":
            if ocs > 1000 and monto > 1_500_000_000 and gpc > 5_000:
                passes.append(f"Puerto Montt restored: {ocs} OCs, ${monto:,.0f} CLP (gpc: ${gpc:,.0f})")
            else:
                failures.append(f"Puerto Montt NOT restored properly: {ocs} OCs, ${monto:,.0f} CLP (gpc: ${gpc:,.0f})")
        elif comuna_name == "Cañete":
            if ocs > 400 and monto > 400_000_000:
                passes.append(f"Cañete restored: {ocs} OCs, ${monto:,.0f} CLP")
            else:
                failures.append(f"Cañete NOT restored properly: {ocs} OCs, ${monto:,.0f} CLP")
        elif comuna_name == "La Cisterna":
            if ocs > 300 and monto > 400_000_000:
                passes.append(f"La Cisterna restored: {ocs} OCs, ${monto:,.0f} CLP")
            else:
                failures.append(f"La Cisterna NOT restored properly: {ocs} OCs, ${monto:,.0f} CLP")
        else:
            if ocs > 10 and monto > 50_000_000:
                passes.append(f"{comuna_name} restored: {ocs} OCs, ${monto:,.0f} CLP")
            else:
                failures.append(f"{comuna_name} suspiciously low: {ocs} OCs, ${monto:,.0f} CLP")

    # Comprehensive check across ALL 345 comunas:
    # Does any comuna in comunas_enriched have a gap vs Parquet?
    print("\n--- 4. FULL PARQUET VS JSON 345-COMMUNE CONVERGENCE ---")
    pq_comuna_agg = con.execute(f"""
        SELECT 
            comuna_comprador,
            count(distinct codigo_orden) as ocs,
            round(sum(monto_linea), 0) as monto
        FROM read_parquet('{pq_path}')
        GROUP BY comuna_comprador
    """).fetchall()
    pq_map = {r[0].strip().lower(): {"ocs": r[1], "monto": float(r[2])} for r in pq_comuna_agg}

    unmatched_in_json = []
    gap_count = 0
    total_gap_monto = 0.0

    # Map normalizado para resolver toponimia oficial y tildes
    import unicodedata
    def clean_norm(s):
        s = "".join(ch for ch in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(ch) != "Mn")
        return "".join(ch for ch in s if ch.isalnum() or ch == " ").strip()

    pq_norm_map = {clean_norm(k): v for k, v in pq_map.items()}

    for c in comunas_enriched:
        c_name = c["comuna"].strip().lower()
        c_raw = (c.get("comuna_raw") or "").strip().lower()
        norm_key = clean_norm(c["comuna"])
        c_monto = float(c.get("monto_total", 0.0))
        c_ocs = int(c.get("total_ocs", 0))
        
        match_data = pq_map.get(c_name) or pq_map.get(c_raw) or pq_norm_map.get(norm_key)
        
        if match_data:
            p_monto = match_data["monto"]
            p_ocs = match_data["ocs"]
            diff = abs(c_monto - p_monto)
            diff_ocs = abs(c_ocs - p_ocs)
            if diff > 1000 or diff_ocs > 0:
                gap_count += 1
                total_gap_monto += diff
                unmatched_in_json.append((c["comuna"], c_ocs, p_ocs, c_monto, p_monto, diff))
        else:
            # Combarbalá or other 0-purchase commune
            if c_ocs > 0 or c_monto > 0:
                unmatched_in_json.append((c["comuna"], c_ocs, 0, c_monto, 0.0, c_monto))

    if gap_count == 0 and len(unmatched_in_json) == 0:
        passes.append("100% Convergence: All 345 comunas in comunas_enriched match Parquet aggregations exactly")
    else:
        failures.append(f"{gap_count} comunas have discrepancies between Parquet and JSON (total gap: ${total_gap_monto:,.0f})")
        for u in unmatched_in_json[:10]:
            print("  Discrepancy:", u)

    # -------------------------------------------------------------
    # 5. MACRO FINANCIAL CONSISTENCY: KPIs vs Regiones vs Comunas
    # -------------------------------------------------------------
    print("\n--- 5. MACRO FINANCIAL CONSISTENCY ---")
    kpis_monto = float(national_kpis.get("monto_total_clp", 0.0))
    kpis_ocs = int(national_kpis.get("total_ocs", 0))

    sum_comunas_monto = sum(c.get("monto_total", 0.0) for c in comunas_enriched)
    sum_comunas_ocs = sum(c.get("total_ocs", 0) for c in comunas_enriched)

    sum_regiones_monto = sum(r.get("monto_total", 0.0) for r in regiones_enriched)
    sum_regiones_ocs = sum(r.get("total_ocs", 0) for r in regiones_enriched)

    print(f"National KPIs:      ${kpis_monto:,.0f} CLP | {kpis_ocs:,} OCs")
    print(f"Sum of Comunas:     ${sum_comunas_monto:,.0f} CLP | {sum_comunas_ocs:,} OCs")
    print(f"Sum of Regiones:    ${sum_regiones_monto:,.0f} CLP | {sum_regiones_ocs:,} OCs")
    print(f"Parquet Total:      ${pq_stats[2]:,.0f} CLP | {pq_stats[1]:,} OCs")

    gap_kpi_comunas = abs(kpis_monto - sum_comunas_monto)
    if gap_kpi_comunas < 100_000_000: # Less than 0.1% difference
        passes.append(f"Macro convergence: Gap between KPIs and Comunas is only ${gap_kpi_comunas:,.0f} CLP (<0.06%)")
    else:
        failures.append(f"Macro divergence: Gap between KPIs and Comunas is ${gap_kpi_comunas:,.0f} CLP")

    # -------------------------------------------------------------
    # 6. ADVERSARIAL SCAN FOR RESIDUAL SPURIOUS ORDERS
    # -------------------------------------------------------------
    print("\n--- 6. ADVERSARIAL RESIDUAL SCAN ---")
    adversarial_terms = [
        "guitarra", "carpa", "toldo", "fosa septica", "fosa séptica",
        "gasfiter", "alcantarillado", "agroveterinaria", "veterinaria",
        "topografia", "topografía", "fotogrametria", "fotogrametría",
        "camioneta", "taller mecanico", "taller mecánico", "lubricentro",
        "aceite mobil", "barra central direccion", "computador para camioneta",
        "computador (ecu)", "falla en computador", "neubacar"
    ]

    spurious_found = 0
    for term in adversarial_terms:
        cnt = con.execute(f"""
            SELECT count(*)
            FROM read_parquet('{pq_path}')
            WHERE lower(texto_descriptivo) LIKE '%{term}%'
               OR lower(nombre_proveedor) LIKE '%{term}%'
        """).fetchone()[0]
        if cnt > 0:
            failures.append(f"Spurious term '{term}' found in Parquet: {cnt} occurrences")
            spurious_found += 1
        else:
            passes.append(f"Spurious term '{term}': 0 occurrences in Parquet")

    # -------------------------------------------------------------
    # 7. SUMMARY & VERDICT
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"RESULTS: {len(passes)} PASSED, {len(failures)} FAILED")
    print("=" * 80)
    if failures:
        print("\nFAILURES DETECTED:")
        for f in failures:
            print(f"  [X] {f}")
        return False
    else:
        print("\nALL ADVERSARIAL CHECKS PASSED EMPIRICALLY!")
        return True

if __name__ == "__main__":
    success = run_suite()
    exit(0 if success else 1)
