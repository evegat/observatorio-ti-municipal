# Roadmap del Observatorio TI Municipal

Hoja de ruta estratégica y backlog de evolución tecnológica del **Observatorio de Compras TI y Tecnologías Municipales en Chile (2014–2026)**.

---

## 🎯 Visión General

Consolidar la plataforma como el estándar de referencia nacional en transparencia, auditoría algorítmica y fiscalización cívica del gasto tecnológico en los gobiernos locales de Chile, combinando rigurosidad académica (PUB021) con usabilidad periodística abierta.

---

## 🗺️ Fases y Versiones Planificadas

### [v1.0.0] — Lanzamiento Oficial (Completado · 2026-10-04)
- [x] Visualizador geoespacial con Leaflet 1.9.4 empaquetado offline.
- [x] Termómetro radial SVG de Madurez TI (0–100) en cuatro cuadrantes calibrados.
- [x] Desglose de gasto per cápita en 7 canastas tecnológicas contra padrón INE 2024.
- [x] Extracción y linkeo directo a Top 4 contratos emblemáticos en Mercado Público.
- [x] Comparador comunal directo A vs B (`#comparar=Valdivia,Temuco`).
- [x] Hash router permalinks (`#comuna=...`) y botón compartir al portapapeles.
- [x] Despliegue en producción `https://observatoriotimunicipal.evegat.cl` con CI/CD automatizado.
- [x] Adopción completa del Harness MyWorld v1 (`MYWORLD-HARNESS.json`, githooks, AGENTS.md).

---

### [v1.1.0] — Descarga Masiva y Filtros Temporales (Q4 2026)
- [ ] **Descarga CSV Comunal:** Permitir a periodistas e investigadores descargar el dataset granular de cada comuna en formato CSV/Excel en 1 click desde el drawer.
- [ ] **Filtros por Período Presidencial/Alcaldicio:** Selector temporal para contrastar la inversión entre administraciones (2014–2018, 2018–2022, 2022–2026).
- [ ] **Buscador Léxico de Contratos:** Barra de búsqueda dentro de la comuna para filtrar compras por términos específicos (*televigilancia*, *biometría*, *chatbots*, *SAP*, *antivirus*).
- [ ] **Data Tables Ordenables:** Tabla interactiva en el drawer con paginación para explorar la totalidad de OCs históricas de la comuna.

---

### [v1.2.0] — Red de Concentración y Vendor Lock-in (Q1 2027)
- [ ] **Matriz Territorial de Proveedores:** Visualización gráfica de la penetración regional de los principales contratistas GovTech (CAS-Chile, Acepta, etc.).
- [ ] **Radar de Trato Directo:** Visualizador de la proporción de compras adjudicadas por trato directo vs. licitación pública por comuna y proveedor.
- [ ] **Índice HHI por Subcategoría:** Desglose del nivel de concentración de mercado no solo en ERPs, sino en Ciberseguridad, Telecomunicaciones y Hardware.

---

### [v1.3.0] — Integración Econométrica y Modelación (Q2 2027)
- [ ] **Cruce Político-Electoral:** Incorporación de variables de afiliación política del alcalde, años de elecciones y reelección.
- [ ] **Dependencia del Fondo Común Municipal (FCM):** Análisis de correlación entre autonomía presupuestaria municipal y gasto per cápita en innovación digital.
- [ ] **DuckDB WASM Client-Side:** Ejecución de queries SQL analíticos directamente en el navegador del usuario para análisis exploratorio avanzado sin backend.

---

## 📬 Sugerencias y Contribuciones

Para proponer nuevas funcionalidades o reportar inconsistencias en los datos de Mercado Público:
- Repositorio oficial: [github.com/evegat/observatorio-ti-municipal](https://github.com/evegat/observatorio-ti-municipal)
- Reporte de issues: [github.com/evegat/observatorio-ti-municipal/issues](https://github.com/evegat/observatorio-ti-municipal/issues)
- Licencia: MIT / Open Data CC BY 4.0.
