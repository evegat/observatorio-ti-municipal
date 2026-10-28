# Master Orchestration Plan — Request 2026-10-28T02:14:52Z

## Goal
Ingesta, saneamiento, auditoría forense y análisis exhaustivo del 100% de los datos de compras públicas tecnológicas (2014–2026) y dotación de personal municipal de Chile (345 comunas), incorporando la nueva capa integral de capacitaciones y desarrollo de habilidades digitales (ciberseguridad, ERP/sistemas, ofimática, IA y comunitaria) con convergencia matemática al peso ($0 CLP de discrepancia) y validación de gates MyWorld.

## Phases

### Phase 0: Survey & Codebase/Data Reconnaissance
- Spawn 3 Explorers in parallel:
  - `explorer_survey_compras`: Investigate `D:\Proyectos\observatorio-ti-municipal\data`, `D:\Proyectos\P152 - Compras Municipales de Chile`, `catastro_ti_saneado.parquet` or existing pipelines, purchase order taxonomy, and training OCs.
  - `explorer_survey_rrhh`: Investigate `D:\Proyectos\P166 - Personal Municipal de Chile`, DuckDB databases, CPLT/SINIM sources, coverage of 345 comunas, and absence of synthetic ratios.
  - `explorer_survey_capacitaciones`: Investigate existing training order classifications, dual dimension (internal vs community), blacklist criteria (catering, coffee breaks, salones), and JSON output structures.
- Synthesize findings into `PROJECT.md` Feature Inventory & verify architecture.

### Phase 1: Milestone 1 — Auditoría Forense y Consolidación de Datos Base
- 100% compras públicas TI observadas 2014-2026 y dotación municipal observada (345 comunas).
- Loop: 3 Explorers -> 1 Worker -> 2 Reviewers + 2 Challengers + 1 Auditor.

### Phase 2: Milestone 2 — Construcción e Integración de la Capa de Capacitaciones Tecnológicas Dual
- Filtrado y clasificación en dos dimensiones: Funcionarios (Ciberseguridad, ERP, Ofimática, IA) vs Ciudadanía (Alfabetización, personas mayores, talleres DIDECO).
- Blacklist estricta (catering, coffee breaks, colaciones, salones).
- Incorporación en parquet de `flag_capacitacion_ti` y `subcategoria_capacitacion`.
- Loop: 3 Explorers -> 1 Worker -> 2 Reviewers + 2 Challengers + 1 Auditor.

### Phase 3: Milestone 3 — Enriquecimiento de Artefactos de Salida
- Actualización de `data/comunas_enriched.json` (o split summary/detail), `data/national_kpis.json`, `data/regiones_enriched.json` y `data/proveedores_ranking.json`.
- Adición de `monto_capacitacion_ti`, `ocs_capacitacion_ti`, `capacitacion_pc` y desglose por área formativa.
- Loop: 3 Explorers -> 1 Worker -> 2 Reviewers + 2 Challengers + 1 Auditor.

### Phase 4: Milestone 4 — Verificación Adversarial, Convergencia Matemática 100% y Gates MyWorld
- Verificación cruzada Parquet vs JSONs (suma comunas = suma regiones = total nacional, exacto al peso).
- Gates `quality` y `security` del arnés MyWorld validados en verde.
- Loop: 3 Explorers -> 1 Worker -> 2 Reviewers + 2 Challengers + 1 Auditor.
