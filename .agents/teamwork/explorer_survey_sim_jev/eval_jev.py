import sys
import os
import json
from dataclasses import asdict

sys.path.append(os.path.abspath("D:/Proyectos/observatorio-ti-municipal/.myworld-harness"))
from jev_design_judge import JevDesignJudge

html_lines = open("D:/Proyectos/observatorio-ti-municipal/index.html", encoding="utf-8").readlines()
judge = JevDesignJudge()

slices = [
    ("a11y_bar", 1, 83),
    ("topbar", 84, 110),
    ("hero", 111, 218),
    ("scrollytelling", 219, 240),
    ("radiografia_mapa", 241, 291),
    ("rrhh_section", 292, 327),
    ("ranking_center", 328, 473),
    ("metodologia_academic", 474, 503),
    ("site_footer", 504, 563),
    ("modal_como_usar", 564, 634),
    ("modal_legal", 635, 687),
    ("modal_registro_descarga", 688, 781)
]

results = {}
print(f"{'Section':24} | {'Status':12} | {'Hierarchy':10} | {'Density':18} | {'A11y':8} | {'Friction':8} | {'Slop':6} | {'Reason'}")
print("-" * 120)

for name, start, end in slices:
    chunk = "".join(html_lines[start-1:end])
    dec = judge.evaluate_ui(chunk, name)
    results[name] = asdict(dec)
    print(f"{name:24} | {dec.status:12} | {dec.hierarchy_clarity:10} | {dec.information_density:18} | {dec.accessibility_risk:8} | {dec.client_friction_prob:.2f}     | {dec.slop_risk:6} | {dec.verdict_reason}")

full_doc = "".join(html_lines)
full_dec = judge.evaluate_ui(full_doc, "full_document")
results["full_document"] = asdict(full_dec)
print(f"{'full_document':24} | {full_dec.status:12} | {full_dec.hierarchy_clarity:10} | {full_dec.information_density:18} | {full_dec.accessibility_risk:8} | {full_dec.client_friction_prob:.2f}     | {full_dec.slop_risk:6} | {full_dec.verdict_reason}")

with open("D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_sim_jev/jev_evaluation_raw.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
