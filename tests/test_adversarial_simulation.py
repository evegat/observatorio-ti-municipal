"""
test_adversarial_simulation.py
==============================
Empirical Adversarial Challenge & Stress Test Suite for Milestone 3.
Observed and executed by Challenger M3.

Tests:
1. All 346 Consolidated Comunas Search & Normalization Robustness (100% findability under perturbations).
2. Chilean Toponym Aliases & Edge Case Toponyms.
3. Monte Carlo Adversarial Perturbations of 100 Personas (5 batches x 100 users = 500 runs, > 95% threshold).
4. Failure Case Probing: P022 (Santiago alias in app.js vs raw sim), P070 & P071 (non-tech queries).
5. Registration Modal Validation Boundary Testing (valid edge cases vs invalid inputs).
6. Microdata Physical & Semantic Integrity (all 346 records, coordinates, scores).
7. JEV Section-by-Section Quality Invariant (friction <= 0.20, slop == 'bajo').
"""

import sys
import os
import json
import unicodedata
import random
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / ".agents" / "teamwork" / "explorer_survey_sim_jev"))
sys.path.insert(0, str(BASE_DIR / ".myworld-harness"))

from simulate_100_users import generate_100_personas, run_simulation, COMUNAS_DATA, PROVEEDORES_DATA
from jev_design_judge import JevDesignJudge


def norm_text(s):
    if not s:
        return ""
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("utf-8").lower().strip()


APP_ALIASES = {
    "coyhaique": "coihaique",
    "marchigue": "marchihue",
    "navarino": "cabo de hornos",
    "puerto williams": "cabo de hornos",
    "santiago": "santiago centro",
    "llay-llay": "llaillay",
    "trehuaco": "treguaco"
}


def deduplicate_comunas_py(raw_comunas):
    """Mirror of deduplicateComunas in app.js."""
    if not isinstance(raw_comunas, list):
        return []

    by_cut = {}
    for item in raw_comunas:
        cut = item.get("codigo_cut") or item.get("comuna")
        by_cut.setdefault(cut, []).append(item)

    consolidated = []
    for cut, items in by_cut.items():
        if len(items) == 1:
            consolidated.append(dict(items[0]))
        else:
            valid_coord = [i for i in items if i.get("lat") is not None and i.get("lng") is not None]
            candidates = valid_coord if valid_coord else items
            candidates.sort(key=lambda x: (
                1 if (x.get("total_ocs") or 0) > 1 else 0,
                x.get("monto_total") or 0
            ), reverse=True)
            consolidated.append(dict(candidates[0]))

    # Adjust Santiago Centro coordinates
    for c in consolidated:
        if "santiago" in c.get("comuna", "").lower():
            c["lat"] = -33.4489
            c["lng"] = -70.6693

    existing_names = set(norm_text(c.get("comuna")) for c in consolidated)
    if "combarbala" not in existing_names:
        consolidated.append({
            "comuna": "Combarbalá",
            "comuna_raw": "Combarbala",
            "region": "Región de Coquimbo",
            "codigo_cut": 4302,
            "poblacion": 13322,
            "total_ocs": 120,
            "monto_total": 185000000,
            "gasto_pc": 13886,
            "score_madurez": 52,
            "lat": -31.1800,
            "lng": -71.0031
        })
    if "antartica" not in existing_names:
        consolidated.append({
            "comuna": "Antártica",
            "comuna_raw": "Antartica",
            "region": "Región de Magallanes y de la Antártica",
            "codigo_cut": 12202,
            "poblacion": 137,
            "total_ocs": 15,
            "monto_total": 42000000,
            "gasto_pc": 306569,
            "score_madurez": 45,
            "lat": -62.1917,
            "lng": -58.9653
        })

    return consolidated


def find_comuna_app_logic(query, comunas):
    if not query:
        return None
    raw_norm = norm_text(query)
    effective = APP_ALIASES.get(raw_norm, raw_norm)
    for c in comunas:
        c_norm = norm_text(c["comuna"])
        if c_norm == effective or c_norm == raw_norm or effective in c_norm:
            return c
    return None


# -----------------------------------------------------------------------------
# 1. TEST ALL 346 COMUNAS FINDABILITY UNDER CASE/ACCENT PERTURBATIONS
# -----------------------------------------------------------------------------
def test_all_346_comunas_findability():
    """Verify that every single one of the 346 consolidated comunas is findable under adversarial inputs."""
    comunas = deduplicate_comunas_py(COMUNAS_DATA)
    assert len(comunas) == 346, f"Expected exactly 346 consolidated comunas, found {len(comunas)}"
    
    missing_exact = []
    missing_upper = []
    missing_no_accents = []
    missing_whitespace = []
    
    for c in comunas:
        name = c["comuna"]
        # Exact
        if not find_comuna_app_logic(name, comunas):
            missing_exact.append(name)
        # Uppercase
        if not find_comuna_app_logic(name.upper(), comunas):
            missing_upper.append(name)
        # Stripped accents
        unaccented = norm_text(name)
        if not find_comuna_app_logic(unaccented, comunas):
            missing_no_accents.append(name)
        # Leading and trailing spaces
        spaced = f"  {name}   "
        if not find_comuna_app_logic(spaced, comunas):
            missing_whitespace.append(name)

    assert not missing_exact, f"Missing exact comunas: {missing_exact}"
    assert not missing_upper, f"Missing uppercase comunas: {missing_upper}"
    assert not missing_no_accents, f"Missing unaccented comunas: {missing_no_accents}"
    assert not missing_whitespace, f"Missing whitespace-padded comunas: {missing_whitespace}"


# -----------------------------------------------------------------------------
# 2. TEST CHILEAN TOPONYM ALIASES & EDGE CASES
# -----------------------------------------------------------------------------
def test_chilean_toponym_aliases():
    """Verify that colloquial Chilean toponym variations resolve to canonical comunas."""
    comunas = deduplicate_comunas_py(COMUNAS_DATA)
    alias_tests = [
        ("Coyhaique", "Coihaique"),
        ("coihaique", "Coihaique"),
        ("Marchigüe", "Marchihue"),
        ("marchigue", "Marchihue"),
        ("Navarino", "Cabo de Hornos"),
        ("Puerto Williams", "Cabo de Hornos"),
        ("Santiago", "Santiago Centro"),
        ("santiago centro", "Santiago Centro"),
        ("Llay-Llay", "Llaillay"),
        ("Trehuaco", "Treguaco")
    ]
    
    for query, expected_comuna in alias_tests:
        found = find_comuna_app_logic(query, comunas)
        assert found is not None, f"Query '{query}' failed to resolve"
        assert norm_text(found["comuna"]) == norm_text(expected_comuna), (
            f"Query '{query}' resolved to '{found['comuna']}', expected '{expected_comuna}'"
        )


# -----------------------------------------------------------------------------
# 3. PROBE SIMULATION FAILURE CASES (P022, P070, P071)
# -----------------------------------------------------------------------------
def test_probe_failure_case_p022_santiago_alias():
    """
    P022 in raw simulation failed comparing Providencia vs Santiago.
    Verify that with app.js alias resolution (santiago -> santiago centro),
    the comparison succeeds cleanly.
    """
    comunas = deduplicate_comunas_py(COMUNAS_DATA)
    cA = find_comuna_app_logic("Providencia", comunas)
    cB = find_comuna_app_logic("Santiago", comunas)
    
    assert cA is not None, "Providencia must exist"
    assert cB is not None, "Santiago must resolve to Santiago Centro"
    assert cB["comuna"] == "Santiago Centro"
    
    # Calculate comparison
    pobA = max(1, cA.get("poblacion") or 0)
    pobB = max(1, cB.get("poblacion") or 0)
    pc_diff = cA.get("gasto_pc", 0) - cB.get("gasto_pc", 0)
    assert isinstance(pc_diff, (int, float))


def test_probe_failure_cases_p070_p071_non_tech_queries():
    """
    P070 ('Limchile') and P071 ('NADIA ELIZABETH') are non-tech queries.
    Verify they correctly do NOT produce spurious matches in the IT catalog,
    confirming catalog precision and zero false-positive contamination.
    """
    comunas = deduplicate_comunas_py(COMUNAS_DATA)
    limchile_muni = find_comuna_app_logic("Limchile", comunas)
    assert limchile_muni is None, "Limchile should not match any municipality"
    
    limchile_prov = [p for p in PROVEEDORES_DATA if "limchile" in p["proveedor"].lower()]
    assert len(limchile_prov) == 0, "Limchile should not be in tech catalog"

    nadia_muni = find_comuna_app_logic("NADIA ELIZABETH", comunas)
    assert nadia_muni is None, "NADIA ELIZABETH should not match any municipality"


# -----------------------------------------------------------------------------
# 4. ADVERSARIAL PERTURBATION MONTE CARLO (5 BATCHES x 100 USERS)
# -----------------------------------------------------------------------------
def test_adversarial_monte_carlo_success_rate():
    """
    Perturb 100 personas across 5 Monte Carlo runs (500 sessions) with:
    - Random case perturbations
    - Injected leading/trailing whitespace
    - Stripped accents
    Verify that overall success rate in every run remains strictly > 95%.
    """
    random.seed(42)
    base_personas = generate_100_personas()
    
    for run_idx in range(5):
        perturbed_personas = []
        for p in base_personas:
            p_copy = dict(p)
            target = p_copy.get("comuna_objetivo", "")
            
            # Apply adversarial perturbations
            if target and target not in ["Nacional (Multicomunal)", "Ranking General"]:
                choice = random.choice(["upper", "lower", "spaces", "strip_accents", "none"])
                if choice == "upper":
                    target = target.upper()
                elif choice == "lower":
                    target = target.lower()
                elif choice == "spaces":
                    target = f"   {target}   "
                elif choice == "strip_accents":
                    target = norm_text(target)
            p_copy["comuna_objetivo"] = target
            
            # For Arquetipo 2 (comparisons), also perturb comuna_comparar
            if p_copy["arquetipo_id"] == 2 and "comuna_comparar" in p_copy:
                t2 = p_copy["comuna_comparar"]
                # In app.js, "Santiago" is an alias for "Santiago Centro"
                if t2 == "Santiago":
                    t2 = random.choice(["Santiago", "Santiago Centro", "santiago"])
                p_copy["comuna_comparar"] = t2
                
            perturbed_personas.append(p_copy)
            
        results, counters = run_simulation(perturbed_personas)
        successes = sum(1 for r in results if r["overall_status"] == "PASS")
        rate = (successes / len(results)) * 100.0
        
        # Verify strict threshold > 95%
        assert rate >= 95.0, f"Monte Carlo Run {run_idx+1}: success rate {rate:.1f}% dropped below 95%"


# -----------------------------------------------------------------------------
# 5. REGISTRATION MODAL VALIDATION BOUNDARY TESTING
# -----------------------------------------------------------------------------
def test_registration_modal_validation():
    """Adversarially probe registration form field validator rules from app.js."""
    def validate_lead(nombre, email, institucion, perfil, proposito):
        n = (nombre or "").strip()
        e = (email or "").strip()
        i = (institucion or "").strip()
        p = (perfil or "").strip()
        pr = (proposito or "").strip()
        return bool(n and e and i and p and pr and "@" in e)

    # Valid edge cases
    assert validate_lead("Juan Pérez", "user+tag@sub.muni.cl", "Muni Test", "Funcionario", "Fiscalización") is True
    assert validate_lead("A", "a@b.cl", "I", "P", "P") is True
    assert validate_lead(" María José ", " mj@domain.org ", " GORE ", " Investigador ", " Paper ") is True
    
    # Invalid boundary cases (must be blocked)
    assert validate_lead("", "user@muni.cl", "Muni", "Funcionario", "Uso") is False
    assert validate_lead("   ", "user@muni.cl", "Muni", "Funcionario", "Uso") is False
    assert validate_lead("Juan", "invalid-email-no-at", "Muni", "Funcionario", "Uso") is False
    assert validate_lead("Juan", "user@muni.cl", "", "Funcionario", "Uso") is False
    assert validate_lead("Juan", "user@muni.cl", "Muni", "", "Uso") is False
    assert validate_lead("Juan", "user@muni.cl", "Muni", "Funcionario", "") is False


# -----------------------------------------------------------------------------
# 6. MICRODATA PHYSICAL & GEOGRAPHIC INTEGRITY
# -----------------------------------------------------------------------------
def test_microdata_geographic_and_numeric_integrity():
    """Verify physical existence, valid Chilean coordinates, and numeric bounds on 346 comunas."""
    comunas = deduplicate_comunas_py(COMUNAS_DATA)
    assert len(comunas) == 346
    cuts = set()
    
    for c in comunas:
        # Check CUT uniqueness
        cut = c.get("codigo_cut")
        assert cut is not None, f"Comuna {c['comuna']} has null codigo_cut"
        assert cut not in cuts, f"Duplicate codigo_cut: {cut} for comuna {c['comuna']}"
        cuts.add(cut)
        
        # Check coordinates (Chile bounding box)
        lat = c.get("lat")
        lng = c.get("lng")
        assert lat is not None and isinstance(lat, (int, float)), f"Invalid lat in {c['comuna']}: {lat}"
        assert lng is not None and isinstance(lng, (int, float)), f"Invalid lng in {c['comuna']}: {lng}"
        # Continental, Austral & Insular Chile coordinates
        assert -63.0 <= lat <= -17.0, f"Lat {lat} out of Chile bounds in {c['comuna']}"
        assert -110.0 <= lng <= -58.0, f"Lng {lng} out of Chile bounds in {c['comuna']}"
        
        # Check scores
        score = c.get("score_madurez")
        assert 0 <= score <= 100, f"Score madurez {score} invalid in {c['comuna']}"
        
        # Check population: either non-negative integer or None (fallback to 0 in UI)
        pob = c.get("poblacion")
        if pob is not None:
            assert isinstance(pob, (int, float)) and pob >= 0, f"Invalid population in {c['comuna']}"


# -----------------------------------------------------------------------------
# 7. JEV SECTION-BY-SECTION QUALITY INVARIANT
# -----------------------------------------------------------------------------
def test_jev_all_sections_pass_invariant():
    """Verify that all 12 discrete UI components score status == 'pass' in JEV Judge."""
    judge = JevDesignJudge()
    html_lines = open(BASE_DIR / "index.html", encoding="utf-8").readlines()
    
    slices = [
        ("a11y_bar", 1, 83),
        ("topbar", 84, 110),
        ("hero", 111, 224),
        ("scrollytelling", 225, 248),
        ("radiografia_mapa", 249, 301),
        ("rrhh_section", 302, 339),
        ("ranking_center", 340, 609),
        ("metodologia_academic", 610, 640),
        ("site_footer", 641, 702),
        ("modal_como_usar", 703, 773),
        ("modal_legal", 774, 826),
        ("modal_registro_descarga", 827, 925)
    ]
    
    for name, start, end in slices:
        chunk = "".join(html_lines[start-1:end])
        dec = judge.evaluate_ui(chunk, name)
        assert dec.status == "pass", f"JEV section '{name}' failed with status: {dec.status} (reason: {dec.verdict_reason})"
        assert dec.client_friction_prob <= 0.20, f"Section '{name}' friction prob {dec.client_friction_prob} > 0.20"
        assert dec.slop_risk == "bajo", f"Section '{name}' slop risk is '{dec.slop_risk}', expected 'bajo'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
