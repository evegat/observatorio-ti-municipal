# Observatorio de Capacidades Tecnológicas Municipales de Chile (2014–2026)

[![Plataforma en Producción](https://img.shields.io/badge/Web-observatoriotimunicipal.evegat.cl-002b49?style=flat-square)](https://observatoriotimunicipal.evegat.cl)
[![Licencia](https://img.shields.io/badge/Licencia-MIT%20%2F%20Open%20Data-b38209?style=flat-square)](LICENSE)
[![Datos Auditados](https://img.shields.io/badge/Auditor%C3%ADa-$307.852%20MM%20CLP-146e66?style=flat-square)](data/national_kpis.json)
[![Cobertura Territorial](https://img.shields.io/badge/Municipios-345%20Corporaciones%20Edilicias-2b5c8f?style=flat-square)](data/comunas_enriched.json)
[![QA & Test Suite](https://img.shields.io/badge/QA%20Tests-2.513%20PASS%20(100%25)-forest?style=flat-square)](tests/)
[![WCAG 2.1 AA](https://img.shields.io/badge/Accesibilidad-WCAG%202.1%20AA%20(66%2F66)-forest?style=flat-square)](tests/test_wcag_contrast_m2.py)

**Autor e Investigador Principal:** Eduardo Vega Toledo  
*Ecosistema de Inteligencia Pública y Datos Abiertos*  
Sitio web y portafolio: [evegat.cl](https://evegat.cl)  
Plataforma oficial interactiva: [observatoriotimunicipal.evegat.cl](https://observatoriotimunicipal.evegat.cl)

---

## 📌 Resumen de la Investigación

Esta plataforma es el visualizador interactivo y repositorio de microdatos abiertos de la investigación sobre **Capacidades Tecnológicas, Tecnoestructura y Transformación Digital en los Gobiernos Locales de Chile**. 

El estudio realiza un cruce empírico longitudinal de **12 años continuos (2014–2026)** integrando dos dimensiones complementarias:
1. **Inversión Pública en Tecnologías:** La totalidad de las compras transadas en Mercado Público / ChileCompra clasificadas en 11 canastas tecnológicas funcionales.
2. **Tecnoestructura y Recursos Humanos:** Registros de dotación informados bajo la Ley N° 20.285 ante el Consejo para la Transparencia (CPLT), analizando escalafón, calidad jurídica (Planta, Contrata, Honorarios), brechas salariales y el **Ratio de Externalización de la Tecnoestructura (RET)**.

### Cifras Clave Consolidadas
* **Monto Total Analizado:** **$307.852 millones de pesos** chilenos en contrataciones de TI.
* **Órdenes de Compra Auditadas:** **149.954 órdenes de compra** en Mercado Público.
* **Líneas de Compra Granulares:** **197.662 ítems transados** clasificados multidimensionalmente.
* **Cobertura Institucional:** **345 municipalidades del país (346 comunas)** conforme al régimen territorial del DFL N° 1-19.704 (donde la I. Municipalidad de Cabo de Hornos administra conjuntamente Cabo de Hornos y Antártica).

---

## 🔍 Dimensiones Técnicas y Hallazgos de Política Pública

1. **Fierro vs. Espejismo de la Inteligencia Artificial:**  
   El **47,88% ($143.698 MM)** del gasto se destina a equipamiento físico básico (computadores de escritorio, impresoras, servidores y cableado). La inversión clasificada en automatización e IA (26,48%) se encuentra concentrada casi en su totalidad en control biométrico de asistencia y mensajería municipal, sin adopción analítica predictiva de fondo.
2. **Estructura del Mercado de Software de Gestión Municipal:**  
   El análisis del segmento de sistemas de gestión (ERPs y plataformas de rentas/finanzas) evidencia un alto nivel de concentración sectorial (HHI superior a 7.000 puntos). Se documenta la distribución empírica de contratos según las adjudicaciones registradas en Mercado Público.
3. **Marginación del Software Libre y Código Abierto:**  
   El Software Libre (FOSS) representa menos del **0,2%** del gasto municipal acumulado, evidenciando una fuerte dependencia de licencias comerciales privativas con costos recurrentes de soporte.
4. **Disparidad Territorial y Gasto Per Cápita:**  
   Existe una brecha sustancial en la capacidad de financiamiento tecnológico entre gobiernos locales metropolitanos e intermedios frente a más de un centenar de comunas rurales de menor escala presupuestaria.

---

## 🛡️ Aseguramiento de Calidad, Trazabilidad y Arquitectura Client-Side

El observatorio sigue los estándares de ingeniería del **Arnés MyWorld v1**:

* **Arquitectura SPA sin dependencias externas:** Desarrollado en JavaScript vainilla nativo modular, CSS3 y HTML5 semántico. Los mapas corren sobre **Leaflet 1.9.4 empaquetado en local** en `assets/leaflet/`, garantizando resiliencia y cero rastreo por CDN de terceros.
* **Batería de Pruebas Automatizadas (100% PASS):**
  * `tests/test_search_normalization_stress.js`: 2.513 pruebas de tolerancia toponímica, desambiguación de tildes/eñes, inyección de caracteres y enrutamiento por hash (`#comuna=...`).
  * `tests/test_wcag_contrast_m2.py`: 66 pares cromáticos auditados matemáticamente contra las directrices **WCAG 2.1 Nivel AA** en temas Claro, Oscuro y Alto Contraste.
  * `tests/test_adversarial_simulation.py`: Simulación de 100 perfiles de usuarios (funcionarios DAF, concejales, periodistas, analistas y ciudadanos).
* **Trazabilidad y Seguridad Estática:** Análisis continuo de vulnerabilidades y secretos con **Trivy** y **Gitleaks** mediante compuertas de calidad pre-commit y pre-push.
* **Privacidad por Diseño (Ley N° 21.719):** Los microdatos de personal municipal aplican seudonimización criptográfica en tránsito y regla de celda mínima ($k \ge 3$), resguardando la privacidad de funcionarios públicos sin exponer RUTs ni identidades individuales.

---

## 📂 Microdatos Abiertos (`data/`)

Los datos están disponibles para descarga pública irrestricta en formatos abiertos:

* [`data/comunas_enriched.json`](data/comunas_enriched.json): Panel consolidado de las 345 municipalidades con población Censo/INE, índice continuo de madurez (0–100), gasto per cápita, dotación RRHH, ratio RET y top contratos enlazados a Mercado Público.
* [`data/national_kpis.json`](data/national_kpis.json): Series macroeconómicas anuales, índices de concentración HHI y distribución agregada por cuadrantes de capacidad estatal.
* [`data/proveedores_ranking.json`](data/proveedores_ranking.json): Métricas de las 30 principales empresas proveedoras de tecnología municipal en Mercado Público.
* [`data/regiones_enriched.json`](data/regiones_enriched.json): Inversión y dotación consolidada por las 16 regiones de Chile.
* [`data/comunas.geojson`](data/comunas.geojson): Polígonos vectoriales cartográficos de límites comunales oficiales.

---

## 🚀 Ejecución en Local

```bash
git clone https://github.com/evegat/observatorio-ti-municipal.git
cd observatorio-ti-municipal

# Levantar servidor HTTP local
python -m http.server 8000
```
Abrir `http://localhost:8000` en el navegador.

---

## 📖 Cómo Citar este Trabajo

```bibtex
@misc{vega2026observatoriotimunicipal,
  author = {Vega Toledo, Eduardo},
  title = {Observatorio de Capacidades Tecnológicas Municipales de Chile (2014–2026)},
  year = {2026},
  howpublished = {\url{https://observatoriotimunicipal.evegat.cl}},
  note = {Plataforma interactiva de microdatos abiertos, tecnoestructura y compras públicas}
}
```

---

## 📜 Licencia

* **Código de la plataforma:** Licencia [MIT](LICENSE).
* **Bases de datos consolidadas:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
