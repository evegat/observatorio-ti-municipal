## 2026-10-24T16:04:47Z
You are a Worker agent (identity: worker_m1_compras).
Your working directory is: D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/worker_m1_compras
Project root is: D:/Proyectos/observatorio-ti-municipal

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP: Read ORIGINAL_REQUEST.md at:
D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/ORIGINAL_REQUEST.md
Specifically requirements R1 and R2 under timestamp 2026-10-24T15:40:58Z:
- R1: Saneamiento Semántico y Erradicación de Falsos Positivos en Compras Públicas:
  * Auditar y purgar la base de datos eliminando contratos espurios no tecnológicos (ej. arriendo de carpas en Peñalolén por $88M).
  * Restringir la canasta a códigos ONU y rubros tecnológicos auditables (Hardware, SaaS, Telecomunicaciones, IA, Ciberseguridad).
  * Garantizar que ninguna orden de compra no tecnológica contamine los indicadores comunales.
- R2: Cobertura Temporal y Extensión a 2025–2026:
  * Poner al día las compras públicas de todas las comunas rezagadas a 2024, integrando las órdenes de compra transadas en 2025 y lo acumulado de 2026.
  * Desacoplar en la estructura de datos: lista de «Últimas Compras Tecnológicas (2025–2026)» cronológica diferenciada de los «Contratos Emblemáticos de Mayor Cuantía (Histórico)».

DETAILED TECHNICAL INPUTS:
Read the investigation and reference scripts prepared by explorer_survey_r1_compras:
- D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_r1_compras/handoff.md
- D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_r1_compras/survey_compras.md
- D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/explorer_survey_r1_compras/simulate_sanitized_basket.py
- D:/Proyectos/observatorio-ti-municipal/PROJECT.md

YOUR EXCLUSIVE FILE OWNERSHIP:
- scripts/build_sanitized_observatorio_data.py
- Any generated parquet/json datasets in data/ related to purchases (e.g. data/catastro_ti_saneado.parquet, data/compras_saneadas_por_comuna.json).
Do NOT edit app.js or index.html in this milestone (that belongs to M3).

TASKS:
1. Implement `scripts/build_sanitized_observatorio_data.py` based on the 2-layer filter validated in `simulate_sanitized_basket.py`:
   - Blacklist non-TI UNSPSC codes and keywords (carpas, toldos, arriendo de escenarios, gas licuado, zapatos sherpa, cursos de capacitación agrícola/apicultura, etc.).
   - Whitelist genuine tech categories: Hardware, SaaS/Software, Telecomunicaciones, IA/Automatización real (avoiding substring `%rpa%` on carpa/escarpe/zarpas), Ciberseguridad.
   - For items with rubro NA / code 0, only accept if unequivocal tech keywords exist in description.
2. Ingest/classify purchases from 2014 through 2026 (including 2025 and 2026-01 to 2026-09) from the raw data files in D:/Proyectos/P049 - Compras publicas tecnologicas e IA publica/DataCompleta and D:/Proyectos/PUB021 - Paper Adopcion IA y Tecnologias en Municipios/data/catastro_ti_municipal_completo_clasificado.parquet.
3. For each of the 345 comunas, compute:
   - Sanitized total tech expenditure (monto_total) and gasto per cápita (gasto_pc).
   - Category breakdowns: monto_hardware, monto_saas, monto_ia, monto_telecom, monto_cyber.
   - `top_contratos_recientes`: chronological feed of 2025-2026 purchases (ordered by date/year DESC).
   - `top_contratos_historicos`: emblematic contracts (ordered by monto DESC) strictly free of non-TI items.
   - `top_proveedores`: top real tech vendors (verify Peñalolén has GTD/Technosystems and 0 carpas; Providencia has Advantage/telecom and 0 carpas).
4. Run comprehensive test checks and print empirical metrics:
   - 0 carpas in all 345 comunas.
   - Peñalolén 2403-315-SE22 eradicated.
   - Active 2025-2026 purchases present for all relevant comunas.
5. Save the output and document all verification commands and exact results in:
   D:/Proyectos/observatorio-ti-municipal/.agents/teamwork/worker_m1_compras/handoff.md
6. Update progress.md and send a message back to parent when done.
