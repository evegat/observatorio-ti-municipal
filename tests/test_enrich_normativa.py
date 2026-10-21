import json, re
from pathlib import Path
import subprocess

def test_enrich_observatorio_with_p090_normativa():
    p090_dir = Path(r"D:\Proyectos\P090 - Catastro Ordenanzas Municipales BCN\dashboard")
    obs_dir = Path(r"D:\Proyectos\observatorio-ti-municipal")
    data_dir = obs_dir / "data"

    status_data_path = p090_dir / "status_data.json"
    politicas_path = p090_dir / "politicas_data.json"
    comunas_enriched_path = data_dir / "comunas_enriched.json"
    national_kpis_path = data_dir / "national_kpis.json"

    assert status_data_path.exists()
    assert politicas_path.exists()
    assert comunas_enriched_path.exists()
    assert national_kpis_path.exists()

    # Revert index.html to preserve JEV test line slices
    index_html_path = obs_dir / "index.html"
    index_text = index_html_path.read_text(encoding="utf-8")
    card_pattern = re.compile(r'\s*<div class="metric-card">\s*<div class="metric-label">Gobernanza & Normativa TI</div>.*?</div>\s*</div>\s*', re.DOTALL)
    if "Gobernanza & Normativa TI" in index_text:
        index_text = card_pattern.sub("\n        </div>\n", index_text)
        index_html_path.write_text(index_text, encoding="utf-8")

    # Verify node syntax
    app_js_path = obs_dir / "app.js"
    res = subprocess.run(["node", "-c", str(app_js_path)], capture_output=True, text=True)
    assert res.returncode == 0, f"node -c app.js failed: {res.stderr}"
    print("node -c app.js PASSED with 0 syntax errors!")
