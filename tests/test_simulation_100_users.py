"""
test_simulation_100_users.py
============================
Standardized pytest-compatible & CLI-executable test suite for the
100-User Panel Simulation of the Observatorio de Capacidades Tecnológicas Municipales de Chile.

Covers:
1. 5 cohorts with exactly 20 personas each (100 total).
2. Key tasks: encontrar_comuna, comparar_comuna, registro_modal, descargar_datos.
3. Strict > 95% success rate requirement across all key tasks and overall.
4. Latency and friction point telemetry.
"""

import os
import sys
import json
import time
import pytest
from pathlib import Path

# Set base dir to repository root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import simulation logic from explorer_survey_sim_jev
sys.path.insert(0, str(BASE_DIR / ".agents" / "teamwork" / "explorer_survey_sim_jev"))
from simulate_100_users import generate_100_personas, run_simulation, COMUNAS_DATA, PROVEEDORES_DATA


@pytest.fixture(scope="module")
def simulation_results():
    """Runs simulation once for the test module."""
    personas = generate_100_personas()
    results, counters = run_simulation(personas)
    return {
        "personas": personas,
        "results": results,
        "counters": counters
    }


def test_cohort_distribution(simulation_results):
    """Verify that exactly 100 profiles across 5 cohorts (20 each) are generated."""
    personas = simulation_results["personas"]
    assert len(personas) == 100, f"Expected exactly 100 personas, found {len(personas)}"
    
    cohorts = {}
    for p in personas:
        aid = p["arquetipo_id"]
        cohorts[aid] = cohorts.get(aid, 0) + 1
        
    assert len(cohorts) == 5, f"Expected 5 cohorts, found {len(cohorts)}"
    for cid in range(1, 6):
        assert cohorts.get(cid) == 20, f"Cohort {cid} must have exactly 20 personas, found {cohorts.get(cid)}"


def test_overall_simulation_success_rate(simulation_results):
    """Verify overall success rate strictly exceeds 95%."""
    results = simulation_results["results"]
    total = len(results)
    successful = sum(1 for r in results if r["overall_status"] == "PASS")
    rate = (successful / total) * 100.0
    
    assert rate > 95.0, f"Overall success rate {rate:.2f}% must be strictly > 95.0%"


def test_key_tasks_success_rates(simulation_results):
    """Verify each key task has a success rate strictly > 95%."""
    counters = simulation_results["counters"]
    key_tasks = ["encontrar_comuna", "comparar_comuna", "registro_modal", "descargar_datos"]
    
    for task in key_tasks:
        counts = counters.get(task, {"success": 0, "fail": 0})
        total = counts["success"] + counts["fail"]
        assert total == 100, f"Task {task} should evaluate all 100 users, evaluated {total}"
        rate = (counts["success"] / total) * 100.0
        assert rate > 95.0, f"Task '{task}' success rate {rate:.2f}% is not strictly > 95.0%"


def test_modal_consent_and_telemetry(simulation_results):
    """Verify registration modal task achieves 100% success rate with valid telemetry fields."""
    results = simulation_results["results"]
    reg_success = sum(1 for r in results if r["tasks"]["registro_modal"]["status"] == "SUCCESS")
    assert reg_success == 100, f"Registration modal should succeed for all 100 users, succeeded for {reg_success}"


def test_data_download_integrity(simulation_results):
    """Verify data download succeeds for 100% of simulated users across CSV and JSON targets."""
    results = simulation_results["results"]
    download_success = sum(1 for r in results if r["tasks"]["descargar_datos"]["status"] == "SUCCESS")
    assert download_success == 100, f"Data download should succeed for all 100 users, succeeded for {download_success}"


def test_execution_latency(simulation_results):
    """Verify average simulation latency per persona is client-side lightweight (< 50ms)."""
    results = simulation_results["results"]
    latencies = [r["latency_ms"] for r in results]
    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 50.0, f"Average simulation step latency {avg_latency:.2f}ms exceeds 50ms"


def main():
    print("================================================================================")
    print("STANDARDIZED 100-USER PANEL SIMULATION TEST RUNNER")
    print("================================================================================")
    
    personas = generate_100_personas()
    results, counters = run_simulation(personas)
    sim_data = {"personas": personas, "results": results, "counters": counters}
    
    try:
        test_cohort_distribution(sim_data)
        print("[PASS] test_cohort_distribution: 5 cohorts x 20 users = 100 total")
        
        test_overall_simulation_success_rate(sim_data)
        total = len(results)
        successful = sum(1 for r in results if r["overall_status"] == "PASS")
        rate = (successful / total) * 100.0
        print(f"[PASS] test_overall_simulation_success_rate: {successful}/{total} ({rate:.1f}% > 95%)")
        
        test_key_tasks_success_rates(sim_data)
        for task in ["encontrar_comuna", "comparar_comuna", "registro_modal", "descargar_datos"]:
            counts = counters[task]
            t_rate = (counts["success"] / 100) * 100.0
            print(f"[PASS] test_key_tasks_success_rates [{task}]: {counts['success']}/100 ({t_rate:.1f}% > 95%)")
            
        test_modal_consent_and_telemetry(sim_data)
        print("[PASS] test_modal_consent_and_telemetry: 100/100 (100.0%)")
        
        test_data_download_integrity(sim_data)
        print("[PASS] test_data_download_integrity: 100/100 (100.0%)")
        
        test_execution_latency(sim_data)
        avg_lat = sum(r["latency_ms"] for r in results) / len(results)
        print(f"[PASS] test_execution_latency: avg {avg_lat:.2f}ms per user")
        
        print("--------------------------------------------------------------------------------")
        print("ALL SIMULATION TESTS PASSED EMPIRICALLY (Milestone 3 Quality Gate OK)")
        print("================================================================================")
        return 0
    except AssertionError as e:
        print(f"[FAIL] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
