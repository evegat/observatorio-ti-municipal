# Radiografía 4D: Contrataciones TI y Transformación Digital en Municipios de Chile (2014–2026)

[![Plataforma en Producción](https://img.shields.io/badge/Web-observatoriotimunicipal.evegat.cl-002b49?style=flat-square)](https://observatoriotimunicipal.evegat.cl)
[![Licencia](https://img.shields.io/badge/Licencia-MIT%20%2F%20Open%20Data-b38209?style=flat-square)](LICENSE)
[![Datos Auditados](https://img.shields.io/badge/Auditor%C3%ADa-$300.125%20MM%20CLP-146e66?style=flat-square)](data/national_kpis.json)
[![Cobertura Territorial](https://img.shields.io/badge/Comunas-346%20Gobiernos%20Locales-2b5c8f?style=flat-square)](data/comunas_enriched.json)

**Autor:** Eduardo Vega Toledo  
*Facultad de Gobierno, Universidad de Chile*  
Sitio web personal y portafolio: [evegat.cl](https://evegat.cl)  
Plataforma interactiva oficial: [observatoriotimunicipal.evegat.cl](https://observatoriotimunicipal.evegat.cl)

---

## 📌 Resumen de la Investigación

Esta plataforma es el visualizador interactivo y repositorio de datos abiertos del proyecto de investigación académica **PUB021 / P049**, que analiza la totalidad de las compras públicas de tecnologías de la información, software, infraestructura y algoritmos en el nivel local de Chile durante un horizonte de **12 años longitudinales (2014–2026)**.

### Principales Cifras Auditadas
* **Monto Total Analizado:** **$300.125 millones de pesos** chilenos (~US$ 326,2 millones de dólares).
* **Órdenes de Compra Catalogadas:** **148.652 órdenes de compra** en Mercado Público / ChileCompra.
* **Ítems Transados Desglosados:** **197.662 líneas de compra** clasificadas multidimensionalmente.
* **Compradores Locales:** **630 entidades** (346 municipalidades matrices, corporaciones municipales de educación/salud y asociaciones locales).

---

## 🔍 Hallazgos Estructurales de Política Pública

1. **El Peso del Fierro vs. El Espejismo de la Inteligencia Artificial:**  
   El **47,88% ($143.698 MM)** del gasto total se absorbe exclusivamente en la adquisición y reposición de infraestructura física (computadores, impresoras, servidores y cableado). La categoría de IA (26,48%) se encuentra atomizada en biometría para control de asistencia y chatbots de WhatsApp, sin adopción analítica predictiva sustantiva.
2. **Monopolio Crítico y Vendor Lock-in (CAS-Chile):**  
   En el segmento de sistemas de gestión municipal (ERPs), el índice Herfindahl-Hirschman (HHI) alcanza **7.607,1**, triplicando el umbral antimonopolio de 2.500. **CAS-CHILE S.A.** concentra el **87,2%** del gasto histórico transado ($1.291 MM de $1.481 MM).
3. **Marginación del Software Libre (FOSS):**  
   El Software Libre y de código abierto representa únicamente el **0,17% ($514 MM)** del gasto municipal, evidenciando una dependencia casi total de licencias privativas y costos recurrentes de mantención.
4. **La Fractura Territorial Per Cápita:**  
   Existe una brecha de hasta **30x** entre municipios de alta inversión (Valdivia con **$36.789 CLP/hab** u Ovalle con **$39.404 CLP/hab**) y más de 120 municipios semi-urbanos y rurales que no alcanzan a gastar **$1.500 CLP/hab**.

---

## 🛠️ Arquitectura Tecnológica y Soberanía

* **Zero External Dependencies / Offline-Ready:** Cartografía montada con Leaflet 1.9.4 empaquetado localmente en `assets/leaflet/`. Cero dependencia de CDNs de terceros.
* **Diseño Editorial:** Implementado bajo el sistema de diseño de `evegat.cl` (marfil `#faf8f5`, carbón `#14171a`, oro `#b38209`, azul `#002b49`).
* **Termómetro Radial SVG:** Indicador semicircular 0–100 nativo vectorial sin librerías externas.
* **Comparador Comunal A vs B:** Permite contrastar brechas per cápita en tiempo real mediante hash deeplinking (`#comparar=Valdivia,Temuco`).
* **Fiscalización Ciudadana:** Enlaces directos a las Órdenes de Compra en la Ficha Oficial de Mercado Público.

---

## 📂 Estructura de Datos Abiertos (`data/`)

Los datos están disponibles para descarga pública en formatos abiertos:

* [`data/comunas_enriched.json`](data/comunas_enriched.json): Panel de 395 comunas con población oficial INE 2024, scores de madurez, gasto per cápita, banderas de lock-in, top proveedores y top contratos con enlace a Mercado Público.
* [`data/national_kpis.json`](data/national_kpis.json): Agregados macroeconómicos nacionales, distribución porcentual por canastas e índices HHI.
* [`data/regiones_enriched.json`](data/regiones_enriched.json): Consolidado de inversión y órdenes de compra por región política de Chile.
* [`data/comunas.geojson`](data/comunas.geojson): Polígonos y centroides geográficos comunales de Chile.

---

## 🚀 Ejecución en Local

Para clonar y levantar la plataforma localmente:

```bash
git clone https://github.com/evegat/observatorio-ti-municipal.git
cd observatorio-ti-municipal

# Levantar servidor HTTP estático
python -m http.server 8000
```
Abrir `http://localhost:8000` en tu navegador.

---

## 📖 Cómo Citar este Trabajo

```bibtex
@misc{vega2026observatoriotimunicipal,
  author = {Vega Toledo, Eduardo},
  title = {Radiografía 4D: Contrataciones TI y Transformación Digital Municipal en Chile (2014–2026)},
  year = {2026},
  publisher = {Facultad de Gobierno, Universidad de Chile},
  howpublished = {\url{https://observatoriotimunicipal.evegat.cl}},
  note = {Repositorio de datos abiertos y visualizador geoespacial}
}
```

---

## 📜 Licencia

* **Código de la plataforma:** Licencia [MIT](LICENSE).
* **Bases de datos consolidadas:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
