#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for M1 (R1 & R2)
Author: challenger_m1_2
"""
import json
import re
from pathlib import Path
import duckdb

BASE_DIR = Path("D:/Proyectos/observatorio-ti-municipal")
DATA_DIR = BASE_DIR / "data"

PARQUET_FILE = DATA_DIR / "catastro_ti_saneado.parquet"
ENRICHED_FILE = DATA_DIR / "comunas_enriched.json"
COMPRAS_FILE = DATA_DIR / "compras_saneadas_por_comuna.json"
KPIS_FILE = DATA_DIR / "national_kpis.json"
PROV_FILE = DATA_DIR / "proveedores_ranking.json"
REGIONES_FILE = DATA_DIR / "regiones_enriched.json"

con = duckdb.connect()

print("=" * 80)
print("1. INVESTIGATING ARTIFACTS AND RECORD COUNTS")
print("=" * 80)

with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
    enriched = json.load(f)
with open(COMPRAS_FILE, "r", encoding="utf-8") as f:
    compras = json.load(f)
with open(KPIS_FILE, "r", encoding="utf-8") as f:
    kpis = json.load(f)

print(f"comunas_enriched length: {len(enriched)}")
print(f"compras_saneadas length: {len(compras)}")

parquet_total_rows = con.execute(f"SELECT count(*) FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')").fetchone()[0]
parquet_total_ocs = con.execute(f"SELECT count(distinct codigo_orden) FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')").fetchone()[0]
parquet_total_monto = con.execute(f"SELECT round(sum(monto_linea), 0) FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')").fetchone()[0]

print(f"parquet_total_rows: {parquet_total_rows}")
print(f"parquet_total_ocs: {parquet_total_ocs}")
print(f"parquet_total_monto: {parquet_total_monto:,.0f}")
print(f"kpis total_ocs: {kpis.get('total_ocs')}")
print(f"kpis monto_total_clp: {kpis.get('monto_total_clp'):,.0f}")
print(f"kpis total_entidades: {kpis.get('total_entidades')}")

sum_enriched_monto = sum(c.get("monto_total", 0) for c in enriched)
sum_enriched_ocs = sum(c.get("total_ocs", 0) for c in enriched)
print(f"Sum of monto_total in comunas_enriched: {sum_enriched_monto:,.0f}")
print(f"Sum of total_ocs in comunas_enriched: {sum_enriched_ocs}")
print(f"Difference in monto: {parquet_total_monto - sum_enriched_monto:,.0f}")

print("\n" + "=" * 80)
print("2. CHECKING 345 VS 346 COMUNAS / MUNICIPALITIES")
print("=" * 80)
cut_codes_enriched = {c["codigo_cut"] for c in enriched}
names_enriched = {c["comuna"] for c in enriched}
print(f"Unique CUTs in enriched: {len(cut_codes_enriched)}")
print(f"Unique Names in enriched: {len(names_enriched)}")
if "Antártica" in names_enriched or "Antartica" in names_enriched:
    print("Antártica is present in enriched")
else:
    print("Antártica is NOT present in enriched (CUT 12202)")

if "Combarbalá" in names_enriched or "Combarbala" in names_enriched:
    print("Combarbalá is present in enriched")
else:
    print("Combarbalá is NOT present in enriched")

print("\n" + "=" * 80)
print("3. CHECKING UNMATCHED COMUNAS IN PARQUET")
print("=" * 80)
parquet_comunas = con.execute(f"""
    SELECT comuna_comprador, count(distinct codigo_orden) as ocs, round(sum(monto_linea), 0) as monto
    FROM read_parquet('{str(PARQUET_FILE).replace('\\', '/')}')
    GROUP BY comuna_comprador
    ORDER BY monto DESC
""").fetchall()

print(f"Distinct comuna_comprador in parquet: {len(parquet_comunas)}")
unmatched_in_enriched = []
for p_comuna, p_ocs, p_monto in parquet_comunas:
    # check if p_comuna matches any in enriched
    matched = False
    for c in enriched:
        if c["comuna"].lower() == str(p_comuna).lower() or c.get("comuna_raw", "").lower() == str(p_comuna).lower():
            matched = True
            break
    if not matched:
        unmatched_in_enriched.append((p_comuna, p_ocs, p_monto))

print(f"Unmatched comuna_comprador in parquet: {len(unmatched_in_enriched)}")
for u in unmatched_in_enriched[:20]:
    print(f"  Unmatched: '{u[0]}' -> OCs: {u[1]}, Monto: {u[2]:,.0f}")

print("\n" + "=" * 80)
print("4. ADVERSARIAL STRESS TEST: top_contratos_recientes")
print("=" * 80)
recientes_issues = []
non_2025_or_2026 = []
sorting_issues_recientes = []
required_keys_rec = ["codigo_oc", "proveedor", "anio", "fecha_aceptacion", "monto", "descripcion", "url_mercadopublico"]

for c in enriched:
    c_name = c["comuna"]
    rec = c.get("top_contratos_recientes", [])
    if not isinstance(rec, list):
        recientes_issues.append((c_name, "top_contratos_recientes is not a list"))
        continue
    
    # Check max length
    if len(rec) > 6:
        recientes_issues.append((c_name, f"Length > 6 ({len(rec)})"))
        
    prev_date = None
    prev_monto = None
    for idx, oc in enumerate(rec):
        # Check required keys
        for k in required_keys_rec:
            if k not in oc or oc[k] is None or oc[k] == "":
                if k == "descripcion" and oc[k] == "":
                    pass
                else:
                    recientes_issues.append((c_name, f"Item {idx} missing/null key '{k}'"))
        
        # Check anio >= 2025
        anio = oc.get("anio")
        if anio is None or anio < 2025:
            non_2025_or_2026.append((c_name, oc.get("codigo_oc"), anio))
            
        # Check date format
        f_ac = oc.get("fecha_aceptacion", "")
        # Should be date format like YYYY-MM-DD
        
        # Check sorting: ORDER BY fecha_aceptacion DESC, monto DESC
        curr_date = str(f_ac)
        curr_monto = float(oc.get("monto", 0))
        if prev_date is not None:
            if curr_date > prev_date:
                sorting_issues_recientes.append((c_name, f"Date inversion: item {idx-1} date '{prev_date}' < item {idx} date '{curr_date}'"))
            elif curr_date == prev_date:
                if curr_monto > prev_monto:
                    sorting_issues_recientes.append((c_name, f"Monto tie-break inversion: item {idx-1} monto '{prev_monto}' < item {idx} monto '{curr_monto}'"))
        prev_date = curr_date
        prev_monto = curr_monto

print(f"Recientes issues found: {len(recientes_issues)}")
for iss in recientes_issues[:10]:
    print("  ", iss)
print(f"Recientes with anio < 2025: {len(non_2025_or_2026)}")
for n in non_2025_or_2026[:10]:
    print("  ", n)
print(f"Recientes sorting issues: {len(sorting_issues_recientes)}")
for s in sorting_issues_recientes[:10]:
    print("  ", s)

print("\n" + "=" * 80)
print("5. ADVERSARIAL STRESS TEST: top_contratos_historicos")
print("=" * 80)
historicos_issues = []
sorting_issues_hist = []
required_keys_hist = ["codigo_oc", "proveedor", "anio", "fecha_aceptacion", "monto", "descripcion", "url_mercadopublico"]

for c in enriched:
    c_name = c["comuna"]
    hist = c.get("top_contratos_historicos", [])
    if not isinstance(hist, list):
        historicos_issues.append((c_name, "top_contratos_historicos is not a list"))
        continue
    
    if len(hist) > 4:
        historicos_issues.append((c_name, f"Length > 4 ({len(hist)})"))
        
    prev_monto = None
    for idx, oc in enumerate(hist):
        for k in required_keys_hist:
            if k not in oc or oc[k] is None or oc[k] == "":
                if k == "descripcion" and oc[k] == "":
                    pass
                else:
                    historicos_issues.append((c_name, f"Item {idx} missing/null key '{k}'"))
        
        curr_monto = float(oc.get("monto", 0))
        if prev_monto is not None:
            if curr_monto > prev_monto:
                sorting_issues_hist.append((c_name, f"Monto inversion: item {idx-1} monto {prev_monto} < item {idx} monto {curr_monto}"))
        prev_monto = curr_monto

print(f"Historicos issues found: {len(historicos_issues)}")
for iss in historicos_issues[:10]:
    print("  ", iss)
print(f"Historicos sorting issues: {len(sorting_issues_hist)}")
for s in sorting_issues_hist[:10]:
    print("  ", s)

print("\n" + "=" * 80)
print("6. ADVERSARIAL NON-TI LEXICON SCAN (ALL 345 COMUNAS)")
print("=" * 80)
non_ti_patterns = [
    r"\bcarpa(s)?\b", r"\btoldo(s)?\b", r"\bbanquete(s)?\b", r"\bcatering\b",
    r"\bcoctel(es)?\b", r"\bcóctel(es)?\b", r"\bcamar[ií]n(es)?\b", r"\bescenario(s)?\b",
    r"\bcuranto\b", r"\bgrupo\s+folcl[oó]rico\b", r"\bproductora\s+de\s+evento(s)?\b",
    r"\bgas\s+licuado\b", r"\bgas\s+envasado\b", r"\bzapato(s)?\s+de\s+seguridad\b",
    r"\bbota(s)?\s+de\s+seguridad\b", r"\bcalzado\s+de\s+seguridad\b", r"\bcamioneta(s)?\b",
    r"\bcanasta(s)?\s+de\s+alimento(s)?\b", r"\bobras?\s+civiles?\b", r"\bpavimentaci[oó]n\b",
    r"\bdesratizaci[oó]n\b", r"\bfumigaci[oó]n\b", r"\bneum[aá]tico(s)?\b",
    r"\bpetr[oó]leo\s+diesel\b", r"\bgasolina\b", r"\bap[ií]col[aa](s)?\b",
    r"\becograf[ií]a(s)?\b", r"\bpreuniversitario\b"
]
compiled_patterns = [re.compile(p, re.IGNORECASE) for p in non_ti_patterns]

spurious_findings = []

for c in enriched:
    c_name = c["comuna"]
    # Check top_proveedores
    for p in c.get("top_proveedores", []):
        prov_name = p.get("proveedor", "")
        for pat in compiled_patterns:
            if pat.search(prov_name):
                spurious_findings.append((c_name, "top_proveedores", prov_name, pat.pattern))
    
    # Check top_contratos_historicos
    for oc in c.get("top_contratos_historicos", []):
        desc = oc.get("descripcion", "")
        prov = oc.get("proveedor", "")
        for pat in compiled_patterns:
            if pat.search(desc):
                spurious_findings.append((c_name, "historicos:desc", oc.get("codigo_oc"), desc, pat.pattern))
            if pat.search(prov):
                spurious_findings.append((c_name, "historicos:prov", oc.get("codigo_oc"), prov, pat.pattern))

    # Check top_contratos_recientes
    for oc in c.get("top_contratos_recientes", []):
        desc = oc.get("descripcion", "")
        prov = oc.get("proveedor", "")
        for pat in compiled_patterns:
            if pat.search(desc):
                spurious_findings.append((c_name, "recientes:desc", oc.get("codigo_oc"), desc, pat.pattern))
            if pat.search(prov):
                spurious_findings.append((c_name, "recientes:prov", oc.get("codigo_oc"), prov, pat.pattern))

print(f"Spurious non-TI findings across all feeds: {len(spurious_findings)}")
for sf in spurious_findings[:15]:
    print("  ", sf)

print("\n" + "=" * 80)
print("7. REMOTE & RURAL COMUNAS AUDIT")
print("=" * 80)
remote_comunas_to_check = [
    "Juan Fernández", "Cabo de Hornos", "Colchane", "Ollagüe", "General Lagos",
    "Primavera", "Timaukel", "Torres del Paine", "O'Higgins", "Tortel",
    "Guaitecas", "Palena", "Futaleufú", "Hualaihué", "Chaitén",
    "Alhué", "San Pedro", "Camiña", "Huara", "Pica", "Pozo Almonte",
    "Putre", "Camarones", "Laguna Blanca", "San Gregorio", "Río Verde",
    "Combarbalá", "Rapa Nui", "Isla de Pascua"
]

remote_audit = []
for r_name in remote_comunas_to_check:
    match = next((c for c in enriched if c["comuna"].lower() == r_name.lower() or c.get("comuna_raw", "").lower() == r_name.lower()), None)
    if not match:
        remote_audit.append((r_name, "MISSING from comunas_enriched.json", None, None))
    else:
        ocs = match.get("total_ocs", 0)
        monto = match.get("monto_total", 0)
        rec_count = len(match.get("top_contratos_recientes", []))
        hist_count = len(match.get("top_contratos_historicos", []))
        remote_audit.append((r_name, "PRESENT", f"OCs={ocs}, Monto={monto:,.0f}", f"Rec={rec_count}, Hist={hist_count}"))

for ra in remote_audit:
    print(f"  {ra[0]:<20} | {ra[1]:<10} | {ra[2]} | {ra[3]}")
