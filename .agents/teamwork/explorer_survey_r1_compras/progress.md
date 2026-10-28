# Progress — explorer_survey_r1_compras

- Last visited: 2026-10-24T16:04:00Z
- Status: Completed (Task Complete)
- Milestone: survey_r1_compras

## Log de Actividades Completadas
1. Lectura obligatoria de `ORIGINAL_REQUEST.md` (requisitos R1 y R2).
2. Exploración de arquitectura de datos y localización de los 153.770 contratos en `PUB021/data/catastro_ti_municipal_completo_clasificado.parquet` y `P049/data/processed/candidatos_tecnologicos.parquet`.
3. Descubrimiento de la causa raíz de falsos positivos: prefiltrado léxico sin código ONU y bug catastrófico de substring `%rpa%` sobre `c-a-r-p-a-s` ($63.420 millones en carpas falsamente asignados a IA).
4. Localización del contrato espurio de Peñalolén: OC `2403-315-SE22` de *Alcalde y Asociados Ltda* por $88.935.000 CLP (arriendo de carpas).
5. Localización de los proveedores espurios de Providencia: *Carpas Araos y Pérez* ($221M) y *Lagos Carpas* ($122M).
6. Verificación de existencia de datos 2025 y 2026 en disco: 12 meses de 2025 y 9 meses de 2026 en `P049/DataCompleta/` (477 archivos CSV) y 14.459 OCs TI en base clasificada cubriendo 370 comunas.
7. Diagnóstico de por qué 175 comunas parecían congeladas en 2024: el generador web ordenaba solo por `monto DESC` histórico, sepultando las adquisiciones recientes.
8. Simulación empírica de purga y saneamiento: purga de 60.012 OCs espurias ($140.32 MM CLP, 44,9% del monto original); retención de 96.255 OCs puramente tecnológicas ($172.25 MM CLP).
9. Redacción del informe técnico exhaustivo en `survey_compras.md`.
10. Redacción del reporte de traspaso formal de 5 componentes en `handoff.md`.
