# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-10-04

### Agregado
- **Observatorio Territorial y Cartografía:** Mapa interactivo con Leaflet 1.9.4 empaquetado en local (cero dependencias de CDNs externas), con capas de Madurez TI (0-100), Gasto Per Cápita, Vendor Lock-in (CAS-Chile), Software Libre (FOSS) e Infraestructura Propia.
- **Dataset Auditado Longitudinal:** 148.652 órdenes de compra y 197.662 ítems de Mercado Público (2014–2026) totalizando $300.125 millones de pesos chilenos en las 346 comunas de Chile.
- **Termómetro Radial SVG:** Indicador gráfico de madurez semicircular (0 a 100 puntos) con cuadrantes calibrados (Rezago Crítico, Inicial, Intermedia, Avanzada) y aguja vectorial sin librerías externas.
- **Gasto Per Cápita por Categoría:** Visualizador desglosado en las 7 canastas clave (Hardware, IA, Telecomunicaciones, Ciberseguridad, SaaS, Legado y FOSS) con cálculo en tiempo real contra el padrón comunal INE 2024.
- **Top Contratos Emblemáticos:** Extracción directa de DuckDB con las 4 mayores contrataciones de cada comuna, montos, proveedores y enlaces permanentes a la Ficha de Mercado Público.
- **Comparador Comunal A vs B:** Módulo de contraste directo entre comunas con cálculo automático de brechas de inversión y permalinks (`#comparar=Valdivia,Temuco`).
- **Deeplinking y Botón Compartir:** Enrutamiento por hash (`#comuna=...`) con sincronización bidireccional y copia instantánea de permalink al portapapeles.
- **Optimización Periodística:** Desactivación de trampa de scroll (`scrollWheelZoom: false`) con activación por foco/click para lectura fluida en dispositivos móviles y de escritorio.
- **Metaetiquetas Sociales:** Open Graph y Twitter Cards configurados para previsualización enriquecida en redes sociales y WhatsApp.
- **Harness MyWorld v1:** Manifiesto `MYWORLD-HARNESS.json`, scripts de compuertas `.myworld-harness/`, githooks y contrato operativo `AGENTS.md`.

### Despliegue e Infraestructura
- Despliegue en producción bajo el dominio oficial `https://observatoriotimunicipal.evegat.cl`.
- Contenedor estático Nginx Alpine en Hostinger VPS (`82.25.70.92`) administrado con Coolify API y Traefik v3.
- Borde y CDN global en Cloudflare Edge con compresión Gzip perimetral y SSL automático.
- Integración Continua / Despliegue Continuo (CI/CD) automatizado mediante webhook de GitHub conectado a Coolify.
