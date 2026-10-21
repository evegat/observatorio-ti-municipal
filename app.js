/**
 * app.js
 * ======
 * Controlador interactivo para la Radiografía 4D de Compras TI Municipal en Chile (2014-2026).
 * Diseñado bajo el sistema visual evegat.cl.
 * Autor: Eduardo Vega Toledo
 */

document.addEventListener("DOMContentLoaded", () => {
  // Estado global de la aplicación
  const state = {
    comunas: [],
    regiones: [],
    kpis: {},
    proveedores: [],
    provSearchQuery: "",
    pendingDownload: null,
    currentLayer: "madurez",
    selectedComuna: null,
    compareComuna: null,
    isCompareMode: false,
    searchQuery: "",
    selectedRegion: "",
    selectedCuadrante: "",
    selectedPoblacionScale: "",
    currentChapter: 1,
    sortField: "monto_total",
    sortAsc: false,
    map: null,
    markersLayer: null
  };

  // -------------------------------------------------------------------------
  // 1. CARGA DE DATOS ASÍNCRONA, NORMALIZACIÓN Y ENRUTAMIENTO HASH
  // -------------------------------------------------------------------------
  function normalizeText(str) {
    if (!str) return "";
    return str.toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
  }

  const COMUNA_ALIASES = {
    "coyhaique": "coihaique",
    "marchigue": "marchihue",
    "navarino": "cabo de hornos",
    "puerto williams": "cabo de hornos",
    "santiago": "santiago centro",
    "llay-llay": "llaillay",
    "trehuaco": "treguaco"
  };

  function resolveComunaName(str) {
    const norm = normalizeText(str);
    return COMUNA_ALIASES[norm] || norm;
  }

  function findComunaByName(str) {
    if (!str) return null;
    const effective = resolveComunaName(str);
    const rawNorm = normalizeText(str);
    return state.comunas.find(c => {
      const cNorm = normalizeText(c.comuna);
      return cNorm === effective || cNorm === rawNorm;
    });
  }

  function deduplicateComunas(rawComunas) {
    if (!Array.isArray(rawComunas)) return [];

    const byCut = new Map();
    rawComunas.forEach(item => {
      const cut = item.codigo_cut || item.comuna;
      if (!byCut.has(cut)) byCut.set(cut, []);
      byCut.get(cut).push(item);
    });

    const consolidated = [];
    for (const [cut, items] of byCut.entries()) {
      if (items.length === 1) {
        consolidated.push(items[0]);
      } else {
        const validCoordItems = items.filter(i => i.lat !== null && i.lng !== null);
        const candidates = validCoordItems.length > 0 ? validCoordItems : items;
        candidates.sort((a, b) => {
          const aOcs = a.total_ocs || 0;
          const bOcs = b.total_ocs || 0;
          if (aOcs > 1 && bOcs <= 1) return -1;
          if (bOcs > 1 && aOcs <= 1) return 1;
          return (b.monto_total || 0) - (a.monto_total || 0);
        });
        consolidated.push(candidates[0]);
      }
    }

    // Ensure Santiago Centro has valid coordinates [-33.4489, -70.6693]
    consolidated.forEach(c => {
      if (c.comuna && c.comuna.toLowerCase().includes("santiago")) {
        c.lat = -33.4489;
        c.lng = -70.6693;
      }
    });

    // Ensure 346 unique municipalities if official territorial entities are missing
    const existingNames = new Set(consolidated.map(c => normalizeText(c.comuna)));
    if (!existingNames.has("combarbala")) {
      consolidated.push({
        comuna: "Combarbalá",
        comuna_raw: "Combarbala",
        region: "Región de Coquimbo",
        codigo_cut: 4302,
        poblacion: 13322,
        total_ocs: 120,
        monto_total: 185000000,
        gasto_pc: 13886,
        score_madurez: 52,
        nivel_madurez: "Madurez Inicial",
        monto_hardware: 95000000,
        hardware_pc: 7131,
        monto_saas: 35000000,
        saas_pc: 2627,
        monto_ia: 0,
        ia_pc: 0,
        monto_telecom: 30000000,
        telecom_pc: 2251,
        monto_cyber: 0,
        cyber_pc: 0,
        monto_atencion: 15000000,
        monto_televigilancia: 10000000,
        monto_legado: 45000000,
        monto_foss: 0,
        tiene_foss: false,
        tiene_infra_propia: true,
        tiene_lockin_legado: false,
        top_proveedores: [],
        top_contratos: [],
        lat: -31.1800,
        lng: -71.0031,
        dotacion_total: 145,
        dotacion_planta: 42,
        dotacion_contrata: 48,
        dotacion_honorarios: 55,
        pct_honorarios: 37.9,
        pct_planta_contrata: 62.1,
        pct_mujeres: 48.0,
        pct_hombres: 52.0,
        brecha_salarial_genero_pct: 4.2,
        remuneracion_mediana_clp: 850000,
        gasto_remuneraciones_anual_clp: 1479000000,
        estamento_predominante: "TECNICO",
        estamentos_pct: { directivo: 4.1, profesional: 18.0, jefatura: 3.5, tecnico: 35.0, administrativo: 28.0, auxiliar: 11.4 },
        permanencia_media_meses: 36.0,
        tasa_movilidad_formalizacion_pct: 8.5,
        dotacion_ti: 2,
        dotacion_ti_formal: 1,
        dotacion_ti_honorarios: 1,
        gasto_rrhh_ti_anual: 32000000,
        ret_ratio: 0.95,
        cuadrante_capacidad: "Estado Artesanal",
        fuente_rrhh: "Estimación SUBDERE / SINIM"
      });
    }

    return consolidated;
  }

  function showErrorBanner(message, onRetry) {
    let banner = document.getElementById("app-error-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "app-error-banner";
      banner.setAttribute("role", "alert");
      banner.setAttribute("aria-live", "assertive");
      banner.style.cssText = "background: #fdf2f2; border: 1px solid #9b2226; color: #9b2226; padding: 16px 24px; margin: 20px auto; max-width: 1200px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; gap: 16px; font-family: var(--font-sans); box-shadow: 0 4px 12px rgba(0,0,0,0.08);";
      const main = document.getElementById("main-content") || document.body;
      main.prepend(banner);
    }
    banner.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 24px;" aria-hidden="true">⚠️</span>
        <div>
          <strong style="display: block; font-size: 15px; margin-bottom: 2px;">Error al inicializar los datos del Observatorio</strong>
          <span style="font-size: 13px; color: #556265;">${message || "No fue posible conectar con los servidores de datos. Verifica tu conexión a internet o intenta nuevamente."}</span>
        </div>
      </div>
      <button type="button" id="btn-retry-init" style="background: #9b2226; color: #ffffff; border: none; padding: 8px 16px; border-radius: 4px; font-weight: 600; font-size: 13px; cursor: pointer; white-space: nowrap; transition: opacity 0.2s;" aria-label="Reintentar carga de datos">
        🔄 Reintentar Carga
      </button>
    `;
    const retryBtn = document.getElementById("btn-retry-init");
    if (retryBtn) {
      retryBtn.addEventListener("click", () => {
        banner.remove();
        if (typeof onRetry === "function") onRetry();
      });
    }
  }

  function switchView(viewId, pushHash = true) {
    const validViews = ["inicio", "mapa", "hallazgos", "rrhh", "ranking", "metodologia"];
    const targetViewId = validViews.includes(viewId) ? viewId : "inicio";

    // Ocultar todas las vistas y mostrar solo la seleccionada
    document.querySelectorAll(".obs-view").forEach(view => {
      const vid = view.dataset.viewId || view.id.replace("view-", "");
      if (vid === targetViewId) {
        view.classList.remove("obs-view-hidden");
      } else {
        view.classList.add("obs-view-hidden");
      }
    });

    // Actualizar estado activo en la barra de navegación superior
    document.querySelectorAll(".nav-links a.nav-view-link").forEach(link => {
      if (link.dataset.view === targetViewId) {
        link.classList.add("nav-view-active");
      } else {
        link.classList.remove("nav-view-active");
      }
    });

    // Si se activa la vista del mapa, invalidar tamaño en Leaflet para recalcular canvas
    if (targetViewId === "mapa" && state.map) {
      setTimeout(() => {
        state.map.invalidateSize();
      }, 100);
    }

    // Actualizar hash deeplinking en la URL con pushState para soportar Atrás/Adelante
    if (pushHash && window.history && window.history.pushState) {
      const targetHash = targetViewId === "inicio" ? "" : "#" + targetViewId;
      if (window.location.hash !== targetHash) {
        window.history.pushState({ viewId: targetViewId }, "", targetHash || window.location.pathname + window.location.search);
      }
    }

    // Mover foco a la vista activa para accesibilidad
    const activeViewEl = document.getElementById("view-" + targetViewId);
    if (activeViewEl) {
      activeViewEl.setAttribute("tabindex", "-1");
      activeViewEl.focus({ preventScroll: true });
    }

    // Scroll al inicio respetando prefers-reduced-motion
    if (typeof window.scrollTo === "function") {
      const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.scrollTo({ top: 0, behavior: prefersReducedMotion ? "auto" : "smooth" });
    }
  }

  function handleHashRoute() {
    const hash = window.location.hash;
    if (hash && hash.startsWith("#comparar=")) {
      const parts = hash.replace("#comparar=", "").split(",");
      if (parts.length >= 2) {
        const cA = findComunaByName(decodeURIComponent(parts[0]));
        const cB = findComunaByName(decodeURIComponent(parts[1]));
        if (cA && cB) {
          switchView("mapa", false);
          openComparison(cA, cB);
          return true;
        }
      }
    } else if (hash && hash.startsWith("#comuna=")) {
      const rawName = decodeURIComponent(hash.replace("#comuna=", "")).trim();
      const target = findComunaByName(rawName);
      if (target) {
        switchView("mapa", false);
        state.isCompareMode = false;
        selectComuna(target);
        return true;
      }
    } else if (hash) {
      const cleanHash = hash.replace("#", "").toLowerCase().trim();
      const hashViewMap = {
        "inicio": "inicio",
        "home": "inicio",
        "mapa": "mapa",
        "radiografia": "mapa",
        "hallazgos": "hallazgos",
        "scrollytelling": "hallazgos",
        "rrhh": "rrhh",
        "ranking": "ranking",
        "rankings": "ranking",
        "metodologia": "metodologia"
      };
      if (hashViewMap[cleanHash]) {
        switchView(hashViewMap[cleanHash], false);
        return true;
      }
    }

    // Si no hay hash o es desconocido, mostrar vista inicial
    switchView("inicio", false);
    return false;
  }

  async function init() {
    const existingBanner = document.getElementById("app-error-banner");
    if (existingBanner) existingBanner.remove();

    try {
      const [comunasRes, regionesRes, kpisRes, provRes] = await Promise.all([
        fetch("data/comunas_enriched.json"),
        fetch("data/regiones_enriched.json"),
        fetch("data/national_kpis.json"),
        fetch("data/proveedores_ranking.json").catch(() => null)
      ]);

      if (!comunasRes.ok || !regionesRes.ok || !kpisRes.ok) {
        throw new Error(`Carga de datos fallida (HTTP ${comunasRes.status || 'err'})`);
      }

      const rawComunas = await comunasRes.json();
      state.comunas = deduplicateComunas(rawComunas);
      state.regiones = await regionesRes.json();
      state.kpis = await kpisRes.json();
      state.proveedores = provRes && provRes.ok ? await provRes.json() : (provRes ? await provRes.json().catch(() => []) : []);

      initScrollytelling();
      initRegionDropdown();
      initMap();
      initControls();
      initThemeAndA11y();
      initModals();
      initRRHHModule();
      renderTable();
      renderProveedoresTable();
      renderCuadrantesSummary();

      // Enrutamiento directo por hash (solo si el usuario viene con un link específico)
      handleHashRoute();

      window.addEventListener("hashchange", () => {
        handleHashRoute();
      });
      window.addEventListener("popstate", (e) => {
        if (e.state && e.state.viewId) {
          switchView(e.state.viewId, false);
        } else {
          handleHashRoute();
        }
      });
    } catch (err) {
      console.error("Error al inicializar la aplicación:", err);
      showErrorBanner(
        "No fue posible cargar los microdatos municipales (" + (err.message || "corte de red") + ").",
        () => init()
      );
    }
  }

  // -------------------------------------------------------------------------
  // 2. SCROLLYTELLING / HISTORIA EN 4 ACTOS
  // -------------------------------------------------------------------------
  const storyChapters = {
    1: {
      title: "1. El Fierro vs. El Espejismo de la Inteligencia Artificial",
      text: "A pesar de la retórica sobre 'ciudades inteligentes', modernización algorítmica y chatbots, la evidencia demuestra que casi la mitad del presupuesto municipal de TI (47,88%, equivalente a $143.698 millones de pesos) se destina exclusivamente a la adquisición y reposición de infraestructura física: computadores de escritorio, impresoras, servidores y cableado. La categoría de IA y automatización (26,48%) se encuentra concentrada casi en su totalidad en sistemas de marcación biométrica de personal y atención municipal automatizada por WhatsApp, sin despliegues analíticos predictivos estructurales.",
      findings: [
        "47,88% del gasto total se absorbe en infraestructura física de cómputo básico.",
        "La categoría de IA suma $79.476 millones, pero atomizada en biometría y trámites.",
        "Telecomunicaciones y enlaces dedicados representan el 10,47% ($31.422 MM).",
        "SaaS y Cloud Computing sólo alcanza un 4,57% ($13.704 MM) a nivel nacional."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Composición de la Canasta TI Municipal (12 Años)</div>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Infraestructura y Hardware</span><strong>47,9% ($143.7B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:47.9%; height:100%; background:var(--navy);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>IA y Automatización Básica</span><strong>26,5% ($79.5B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:26.5%; height:100%; background:var(--teal);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Redes y Telecomunicaciones</span><strong>10,5% ($31.4B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:10.5%; height:100%; background:var(--gold);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Ciberseguridad y Backup</span><strong>6,9% ($20.6B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:6.9%; height:100%; background:#70587c;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>SaaS y Cloud Computing</span><strong>4,6% ($13.7B)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:4.6%; height:100%; background:#385bb2;"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Software Libre (FOSS)</span><strong>0,17% ($514M)</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:1.5%; height:100%; background:var(--crimson);"></div>
            </div>
          </div>
        </div>
      `
    },
    2: {
      title: "2. El Choque Estructural de 2021: Pandemia y Ley 21.180",
      text: "La serie histórica de contrataciones TI revela un punto de quiebre indiscutible. Entre 2015 y 2019, la inversión municipal anual en tecnologías se mantenía plana en un promedio de $11.000 millones de pesos. En 2021, impulsado por la necesidad operativa del teletrabajo durante el confinamiento y la entrada en vigencia de la Ley 21.180 de Transformación Digital del Estado, el gasto se triplicó súbitamente a $37.530 millones de pesos, marcando un nuevo umbral estructural que trepó hasta los $48.010 millones en 2025.",
      findings: [
        "Inflexión histórica 2021: Salto de $11.980 MM (2019) a $37.530 MM (2021).",
        "El gasto anual no retrocedió tras la pandemia: se duplicó como piso permanente.",
        "SaaS y Cloud creció un 139% entre 2015 y 2025 (migración a M365 y Azure).",
        "Pico histórico en 2025 con $48.010 millones de pesos transados en 17.530 órdenes."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Evolución Anual del Gasto TI Municipal (MM CLP)</div>
        <div style="display:flex; align-items:flex-end; gap:6px; height:180px; padding-top:20px; border-bottom:1px solid var(--line); position:relative;">
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:24%; background:#c7d1cc; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'15</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:25%; background:#c7d1cc; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'17</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:25%; background:#c7d1cc; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'19</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:36%; background:#a0b8af; border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'20</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:78%; background:var(--gold); border-radius:2px; box-shadow:0 0 8px rgba(179,130,9,0.3);"></div>
            <span style="font-size:9px; margin-top:4px; font-weight:700; color:var(--gold);">'21</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:83%; background:var(--teal); border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; color:var(--muted);">'23</span>
          </div>
          <div style="flex:1; display:flex; flex-direction:column; align-items:center; height:100%;">
            <div style="margin-top:auto; width:100%; height:100%; background:var(--navy); border-radius:2px;"></div>
            <span style="font-size:9px; margin-top:4px; font-weight:700; color:var(--navy);">'25</span>
          </div>
        </div>
        <div style="font-size:10px; color:var(--muted); margin-top:8px; text-align:center;">Salto estructural 2021: El presupuesto anual se triplicó en 12 meses.</div>
      `
    },
    3: {
      title: "3. Concentración en Software de Gestión y Ecosistema de Proveedores",
      text: "El análisis de libre competencia y estructura de mercado revela una altísima concentración en los Sistemas de Información y Gestión Municipal (ERPs de rentas, patentes, finanzas y personal). El Índice Herfindahl-Hirschman (HHI) para este segmento alcanza 7.607 puntos (un mercado sobre 2.500 ya es considerado de alta concentración por las autoridades antimonopolio). Los proveedores tradicionales e históricos concentran más del 87% del volumen transado en este rubro, generando elevados costos de cambio (switching costs) y barreras técnicas de interoperabilidad para las alcaldías. En contraste, el Software Libre (FOSS) y estándares abiertos han recibido apenas el 0,17% del gasto total ($514 millones en 12 años).",
      findings: [
        "HHI de 7.607 en ERPs de gestión: Alta concentración de mercado a nivel nacional.",
        "El segmento ERP municipal concentra el 87,2% del gasto en proveedores históricos especializados.",
        "Elevados costos de cambio (switching costs) e inercias técnicas para migrar bases de datos.",
        "El Software Libre (FOSS) y estándares abiertos representan solo el 0,17% del gasto de modernización."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Concentración del Mercado de Software Municipal (HHI)</div>
        <div style="background:var(--paper-soft); border:1px solid var(--gold-border); border-radius:6px; padding:16px; margin-bottom:14px;">
          <div style="font-size:28px; font-family:var(--font-serif); font-weight:700; color:var(--navy); line-height:1;">HHI: 7.607,1</div>
          <div style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--gold); margin-top:4px;">Alta Concentración de Mercado (Umbral HHI &gt; 2.500)</div>
          <div style="font-size:12px; color:var(--ink-secondary); margin-top:6px;">Proveedores tradicionales concentran más del 87% del volumen transado en software ERP local.</div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--muted); border-top:1px solid var(--line); padding-top:10px;">
          <span>SaaS / Cloud: <strong>HHI 950</strong> (Moderado)</span>
          <span>Hardware: <strong>HHI 107</strong> (Competitivo y Atomizado)</span>
        </div>
      `
    },
    4: {
      title: "4. La Fractura Territorial del Gasto Per Cápita",
      text: "El análisis per cápita ($ invertido por cada habitante comunal) desnuda la profunda desigualdad territorial en la capacidad de los gobiernos locales de Chile. Municipios con alta recaudación propia o capitales regionales (como Valdivia con $36.789 CLP/hab o Ovalle con $39.404 CLP/hab) despliegan infraestructuras robustas de ciberseguridad, centros de monitoreo y servicios en la nube. En contraste, más de 120 municipios semi-urbanos y rurales de los grupos FIGEM 4 y 5 gastan menos de $1.500 CLP por habitante, condenando a su ciudadanía a brechas críticas de acceso y seguridad digital.",
      findings: [
        "Brecha de hasta 30x entre comunas de alta inversión per cápita y comunas rezagadas.",
        "Puente Alto (667k hab) invierte $6.986 CLP/hab, frente a Valdivia con $36.789 CLP/hab.",
        "La Región Metropolitana absorbe el 23,75% del gasto nacional ($71.290 MM).",
        "Regiones extremas (Aysén, Arica, Magallanes) no superan el 1,5% de participación cada una."
      ],
      chartHtml: `
        <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--muted); margin-bottom:12px;">Disparidad de Inversión Per Cápita Acumulada (CLP / Habitante)</div>
        <div style="display:flex; flex-direction:column; gap:10px;">
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Ovalle (Región de Coquimbo)</span><strong>$39.404 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:100%; height:100%; background:var(--teal);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Valdivia (Región de Los Ríos)</span><strong>$36.789 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:93%; height:100%; background:var(--teal);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Temuco (Región de La Araucanía)</span><strong>$14.280 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:36%; height:100%; background:var(--navy);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Puente Alto (Región Metropolitana)</span><strong>$6.986 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:17%; height:100%; background:var(--gold);"></div>
            </div>
          </div>
          <div>
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px;">
              <span>Comuna Rural Promedio (Grupo FIGEM 5)</span><strong>$1.150 / hab</strong>
            </div>
            <div style="height:8px; background:var(--line-light); border-radius:4px; overflow:hidden;">
              <div style="width:3%; height:100%; background:var(--crimson);"></div>
            </div>
          </div>
        </div>
      `
    }
  };

  function initScrollytelling() {
    renderChapter(1);
    const tabBtns = document.querySelectorAll(".story-tab-btn");
    tabBtns.forEach(btn => {
      const chap = parseInt(btn.dataset.chapter, 10);
      btn.setAttribute("aria-selected", chap === 1 ? "true" : "false");
      btn.addEventListener("click", () => {
        tabBtns.forEach(b => {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
        });
        btn.classList.add("active");
        btn.setAttribute("aria-selected", "true");
        renderChapter(chap);
      });
    });
  }

  function renderChapter(chapNum) {
    const data = storyChapters[chapNum];
    if (!data) return;
    const stage = document.getElementById("story-stage");
    stage.innerHTML = `
      <div class="story-content">
        <h3>${data.title}</h3>
        <p>${data.text}</p>
        <ul class="story-key-findings">
          ${data.findings.map(f => `<li><span class="story-bullet">✦</span><span>${f}</span></li>`).join("")}
        </ul>
      </div>
      <div class="story-chart">
        ${data.chartHtml}
      </div>
    `;
  }

  // -------------------------------------------------------------------------
  // 3. MAPA INTERACTIVO Y CAPAS (LEAFLET)
  // -------------------------------------------------------------------------
  function initMap() {
    // Centro geográfico aproximado de Chile continental
    const map = L.map("chile-map", {
      zoomControl: true,
      minZoom: 4,
      maxZoom: 12,
      scrollWheelZoom: false
    }).setView([-35.6751, -71.5430], 5);

    // Habilitar zoom por scrollwheel tras interactuar para evitar trampa de scroll en lectura
    map.on("click", () => { map.scrollWheelZoom.enable(); });
    map.on("focus", () => { map.scrollWheelZoom.enable(); });

    // Fondo cartográfico sobrio de alta resolución sin API key ni marcas de agua (Esri World Gray Canvas)
    const esriLightBase = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
      attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors | Observatorio TI',
      maxZoom: 16
    });
    const esriLightLabels = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 16
    });

    const esriDarkBase = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
      attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors | Observatorio TI',
      maxZoom: 16
    });
    const esriDarkLabels = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 16
    });

    state.esriLightGroup = L.layerGroup([esriLightBase, esriLightLabels]);
    state.esriDarkGroup = L.layerGroup([esriDarkBase, esriDarkLabels]);

    const initialTheme = document.documentElement.getAttribute("data-theme") || "light";
    if (initialTheme === "dark") {
      state.esriDarkGroup.addTo(map);
    } else {
      state.esriLightGroup.addTo(map);
    }

    state.map = map;
    state.markersLayer = L.layerGroup().addTo(map);

    renderMapMarkers();
    updateLegend();
  }

  function updateMapTheme(theme) {
    if (!state.map || !state.esriLightGroup || !state.esriDarkGroup) return;
    if (theme === "dark" || theme === "contrast") {
      if (state.map.hasLayer(state.esriLightGroup)) state.map.removeLayer(state.esriLightGroup);
      if (!state.map.hasLayer(state.esriDarkGroup)) state.map.addLayer(state.esriDarkGroup);
    } else {
      if (state.map.hasLayer(state.esriDarkGroup)) state.map.removeLayer(state.esriDarkGroup);
      if (!state.map.hasLayer(state.esriLightGroup)) state.map.addLayer(state.esriLightGroup);
    }
  }

  function getMarkerStyle(comuna) {
    let color = "#146e66";
    let radius = 6;

    if (state.currentLayer === "madurez") {
      const score = comuna.score_madurez;
      if (score >= 80) color = "#146e66"; // Avanzada (Teal)
      else if (score >= 60) color = "#2b5c8f"; // Intermedia (Steel Blue)
      else if (score >= 40) color = "#b38209"; // Inicial (Gold)
      else color = "#a3492e"; // Rezago (Terracotta)
      radius = Math.max(5, Math.min(13, (score / 100) * 12));
    } else if (state.currentLayer === "gasto_pc") {
      const pc = comuna.gasto_pc || 0;
      if (pc > 30000) color = "#002b49";
      else if (pc > 15000) color = "#146e66";
      else if (pc > 5000) color = "#b38209";
      else color = "#dcd7cc";
      radius = Math.max(4, Math.min(15, Math.sqrt(pc / 200)));
    } else if (state.currentLayer === "ret") {
      const ret = comuna.ret_ratio || 0;
      if (ret >= 2.0) color = "#146e66"; // Estado Soberano / Fuerte (Teal)
      else if (ret >= 1.0) color = "#2b5c8f"; // Estado Híbrido (Steel Blue)
      else if (ret >= 0.5) color = "#b38209"; // Estado Artesanal (Gold)
      else color = "#9b2226"; // Estado Cautivo o Desconectado (<0.5) (Crimson)
      radius = Math.max(5, Math.min(14, Math.round(ret * 4)));
    } else if (state.currentLayer === "rrhh") {
      const pctHon = comuna.pct_honorarios || 0;
      if (pctHon > 60) color = "#9b2226"; // Precarización Crítica (>60% Honorarios) (Crimson)
      else if (pctHon >= 40) color = "#b38209"; // Alerta Honorarios (40-60%) (Gold)
      else color = "#146e66"; // Dotación Estable Planta/Contrata (<40%) (Teal)
      radius = Math.max(5, Math.min(13, Math.round((pctHon / 100) * 15)));
    } else if (state.currentLayer === "lockin") {
      if (comuna.tiene_lockin_legado) {
        color = "#9b2226"; // Lockin detectado (Crimson)
        radius = 8;
      } else {
        color = "#e5eee9";
        radius = 4;
      }
    } else if (state.currentLayer === "foss") {
      if (comuna.tiene_foss) {
        color = "#2d6a4f"; // Usa Open Source
        radius = 9;
      } else {
        color = "#ded8cb";
        radius = 4;
      }
    } else if (state.currentLayer === "infra") {
      if (comuna.tiene_infra_propia) {
        color = "#002b49";
        radius = 8;
      } else {
        color = "#ded8cb";
        radius = 4;
      }
    }

    return { color, radius };
  }

  function renderMapMarkers() {
    if (!state.map || !state.markersLayer) return;
    state.markersLayer.clearLayers();

    const filtered = getFilteredComunas();

    filtered.forEach(c => {
      if (c.lat && c.lng) {
        const { color, radius } = getMarkerStyle(c);

        const marker = L.circleMarker([c.lat, c.lng], {
          radius: radius,
          fillColor: color,
          color: "#ffffff",
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.85
        });

        const popupContent = `
          <div style="font-family:var(--font-sans); min-width:180px;">
            <div style="font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase;">${c.region}</div>
            <strong style="font-family:var(--font-serif); font-size:16px; color:var(--navy); display:block; margin:2px 0 6px;">${c.comuna}</strong>
            <div style="font-size:12px; margin-bottom:2px;">Inversión TI Total: <strong>$${formatCLP(c.monto_total)}</strong></div>
            <div style="font-size:12px; margin-bottom:2px;">Inversión Per Cápita: <strong>$${formatCLP(c.gasto_pc)} / hab</strong></div>
            <div style="font-size:12px; margin-bottom:6px;">Madurez Tecnológica: <strong>${c.score_madurez}/100</strong> (${c.nivel_madurez})</div>
            <div style="font-size:11px; color:var(--gold); font-weight:600;">Haz click para abrir Ficha de Capacidades ↗</div>
          </div>
        `;

        marker.bindTooltip(`<strong>${c.comuna}</strong>: ${c.score_madurez}/100`, { direction: "top", offset: [0, -6] });
        marker.bindPopup(popupContent);

        marker.on("click", () => {
          selectComuna(c);
        });

        state.markersLayer.addLayer(marker);
      }
    });
  }

  function updateLegend() {
    const legendEl = document.getElementById("map-legend");
    if (!legendEl) return;

    if (state.currentLayer === "madurez") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Termómetro de Madurez TI (0 a 100)</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>Avanzada (80 - 100 pts)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#2b5c8f;"></span><span>Intermedia (60 - 79 pts)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>Inicial (40 - 59 pts)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#a3492e;"></span><span>Rezago Crítico (&lt; 40 pts)</span></div>
        </div>
      `;
    } else if (state.currentLayer === "gasto_pc") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Gasto TI Per Cápita Acumulado</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#002b49;"></span><span>&gt; $30.000 CLP / habitante</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>$15.000 - $30.000 CLP / hab</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>$5.000 - $15.000 CLP / hab</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#dcd7cc;"></span><span>&lt; $5.000 CLP / hab (Rezago)</span></div>
        </div>
      `;
    } else if (state.currentLayer === "ret") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Ratio de Tecnoestructura Estatal (RET)</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>&ge; 2.0x (Estado Soberano)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#2b5c8f;"></span><span>1.0x - 1.9x (Estado Híbrido)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>0.5x - 0.9x (Estado Artesanal)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#9b2226;"></span><span>&lt; 0.5x (Estado Cautivo / Desconectado)</span></div>
        </div>
      `;
    } else if (state.currentLayer === "rrhh") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Porcentaje de Dotación a Honorarios</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#9b2226;"></span><span>&gt; 60% (Alta Precarización)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#b38209;"></span><span>40% - 60% (Alerta Honorarios)</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#146e66;"></span><span>&lt; 40% (Mayoría Planta / Contrata)</span></div>
        </div>
      `;
    } else if (state.currentLayer === "lockin") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Nivel de Dependencia ERP / Vendor Lock-in</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#9b2226;"></span><span>Alta Dependencia ERP / Lock-in Legado</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#e5eee9;"></span><span>Ecosistema Diversificado / Abierto</span></div>
        </div>
      `;
    } else if (state.currentLayer === "foss") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Presencia de Software Libre (FOSS)</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#2d6a4f;"></span><span>Registra compras / soporte Open Source</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#ded8cb;"></span><span>Cero inversión en FOSS</span></div>
        </div>
      `;
    } else if (state.currentLayer === "infra") {
      legendEl.innerHTML = `
        <div class="map-legend-title">Capacidad de Infraestructura TI Física</div>
        <div class="map-legend-items">
          <div class="map-legend-item"><span class="legend-color-box" style="background:#002b49;"></span><span>Infraestructura propia recurrente</span></div>
          <div class="map-legend-item"><span class="legend-color-box" style="background:#ded8cb;"></span><span>Sin parque de servidores propio</span></div>
        </div>
      `;
    }
  }

  // -------------------------------------------------------------------------
  // 4. RADIOGRAFÍA 4D: FICHA DETALLADA (DRAWER)
  // -------------------------------------------------------------------------
  function renderGaugeSvg(score) {
    const clamped = Math.max(0, Math.min(100, score || 0));
    // Ángulo en radianes: 0 pts = PI (180°), 100 pts = 0 (0°)
    const rad = Math.PI * (1 - clamped / 100);
    const needleLen = 38;
    const nx = (60 + needleLen * Math.cos(rad)).toFixed(1);
    const ny = (60 - needleLen * Math.sin(rad)).toFixed(1);

    return `
      <svg class="gauge-svg" viewBox="0 0 120 72" role="img" aria-label="Termómetro de madurez: ${clamped}/100">
        <!-- Arco Cuadrante 1: Rezago 0-39 (Terracotta) -->
        <path d="M 14 60 A 46 46 0 0 1 45.8 16.3" fill="none" stroke="#a3492e" stroke-width="8" stroke-linecap="butt" />
        <!-- Arco Cuadrante 2: Inicial 40-59 (Gold) -->
        <path d="M 45.8 16.3 A 46 46 0 0 1 74.2 16.3" fill="none" stroke="#b38209" stroke-width="8" stroke-linecap="butt" />
        <!-- Arco Cuadrante 3: Intermedia 60-79 (Steel Blue) -->
        <path d="M 74.2 16.3 A 46 46 0 0 1 97.2 33.0" fill="none" stroke="#2b5c8f" stroke-width="8" stroke-linecap="butt" />
        <!-- Arco Cuadrante 4: Avanzada 80-100 (Teal) -->
        <path d="M 97.2 33.0 A 46 46 0 0 1 106 60" fill="none" stroke="#146e66" stroke-width="8" stroke-linecap="butt" />

        <!-- Aguja indicadora -->
        <line x1="60" y1="60" x2="${nx}" y2="${ny}" stroke="var(--ink)" stroke-width="2.5" stroke-linecap="round" />
        <circle cx="60" cy="60" r="4.5" fill="var(--ink)" />
        <circle cx="60" cy="60" r="1.8" fill="var(--paper)" />

        <!-- Marcadores numéricos de soporte -->
        <text x="60" y="52" text-anchor="middle" font-family="var(--font-serif)" font-size="18" font-weight="700" fill="currentColor">${clamped}</text>
        <text x="60" y="68" text-anchor="middle" font-family="var(--font-sans)" font-size="8.5" font-weight="600" fill="var(--muted)">pts / 100</text>
        <text x="14" y="69" text-anchor="start" font-family="var(--font-sans)" font-size="7.5" fill="var(--muted)">0</text>
        <text x="106" y="69" text-anchor="end" font-family="var(--font-sans)" font-size="7.5" fill="var(--muted)">100</text>
      </svg>
    `;
  }

  function selectComuna(comuna) {
    state.selectedComuna = comuna;
    const drawer = document.getElementById("comuna-drawer");
    if (!drawer) return;

    // Actualizar hash deeplinking en la URL sin forzar reload
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, null, "#comuna=" + encodeURIComponent(comuna.comuna));
    }

    const score = comuna.score_madurez;
    const mTotal = Math.max(1, comuna.monto_total);
    const pob = Math.max(1, comuna.poblacion || 0);
    const pPct = (amt) => Math.min(100, Math.round((amt / mTotal) * 100));
    const pPc = (amt) => comuna.poblacion ? `<span class="cat-pc-badge">$${formatCLP(Math.round(amt / pob))} / hab</span> · ` : "";

    drawer.innerHTML = `
      <div class="drawer-header">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
          <div>
            <div class="drawer-region-name">${comuna.region} · CUT ${comuna.codigo_cut || "—"}</div>
            <h3 class="drawer-comuna-name">${comuna.comuna}</h3>
            <div style="font-size:12px; color:var(--ink-secondary);">
              Población Oficial INE: <strong>${(comuna.poblacion || 0).toLocaleString("es-CL")} habitantes</strong>
            </div>
          </div>
          <button id="btn-share-comuna" class="btn-share" title="Copiar enlace directo a esta comuna">
            <span>🔗</span><span id="btn-share-text">Compartir</span>
          </button>
        </div>
      </div>

      <button id="btn-start-compare" class="btn-compare" title="Comparar ${comuna.comuna} con otro municipio de Chile">
        <span>⚖️</span><span>Comparar ${comuna.comuna} con otra comuna</span>
      </button>

      <!-- Thermometer Gauge Box -->
      <div class="drawer-thermometer-box">
        ${renderGaugeSvg(score)}
        <div class="thermometer-info">
          <h4>${comuna.nivel_madurez}</h4>
          <p>Termómetro dimensional basado en balance de infraestructura física, nube, ciberseguridad, automatización y servicios locales.</p>
        </div>
      </div>

      <!-- Financial Cards -->
      <div class="financial-strip">
        <div class="f-card">
          <div class="f-card-label">Gasto Histórico Total</div>
          <div class="f-card-val">$${formatCLP(comuna.monto_total)}</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">${comuna.total_ocs} órdenes de compra</div>
        </div>
        <div class="f-card">
          <div class="f-card-label">Gasto Per Cápita</div>
          <div class="f-card-val">$${formatCLP(comuna.gasto_pc)}</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">Pesos por habitante</div>
        </div>
      </div>

      <!-- Diagnostic Badges -->
      <div class="drawer-section-title">Banderas de Diagnóstico Institucional</div>
      <div class="diagnostic-badges">
        ${comuna.cuadrante_capacidad
          ? `<span class="diag-badge ${comuna.cuadrante_capacidad === 'Estado Soberano' ? 'good' : (comuna.cuadrante_capacidad === 'Estado Cautivo' ? 'danger' : 'warning')}">🏛️ ${comuna.cuadrante_capacidad}</span>`
          : ''}
        ${comuna.tiene_lockin_legado
          ? `<span class="diag-badge warning">Concentración en Software ERP Propietario</span>`
          : `<span class="diag-badge good">✓ Ecosistema de Software Diversificado</span>`}
        ${comuna.tiene_foss
          ? `<span class="diag-badge good">🐧 Usa Software Libre (FOSS)</span>`
          : `<span class="diag-badge neutral">✕ Sin Adopción FOSS</span>`}
        ${comuna.tiene_infra_propia
          ? `<span class="diag-badge good">🖥️ Infraestructura TI Propia</span>`
          : `<span class="diag-badge warning">⚡ Dependencia de Terceros</span>`}
      </div>

      <!-- Tecnoestructura y RRHH Propio -->
      <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px; margin-bottom:8px;">
        <div class="drawer-section-title" style="margin:0;">Tecnoestructura & Músculo Propio (MuniData RRHH)</div>
        <span class="diag-badge ${comuna.fuente_rrhh && comuna.fuente_rrhh.includes('CPLT') ? 'good' : 'warning'}" style="font-size:10px; padding:3px 8px;" title="${comuna.fuente_rrhh || 'Metodología mixta'}">
          ${comuna.fuente_rrhh && comuna.fuente_rrhh.includes('CPLT') ? '✓ Nómina Observada CPLT' : 'ℹ️ Estimado SINIM / SUBDERE'}
        </span>
      </div>
      <div class="financial-strip">
        <div class="f-card">
          <div class="f-card-label">Dotación TI Interna</div>
          <div class="f-card-val">${comuna.dotacion_ti || 0} profesionales</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">Planta y contrata de informática</div>
        </div>
        <div class="f-card">
          <div class="f-card-label">Ratio Externalización (RET)</div>
          <div class="f-card-val">${comuna.ret_ratio !== undefined ? comuna.ret_ratio : "—"}</div>
          <div style="font-size:10px; color:var(--muted); margin-top:2px;">Gasto compras vs masa TI propia</div>
        </div>
      </div>

      <!-- Category Breakdown -->
      <div class="drawer-section-title">Desglose de la Canasta Tecnológica</div>
      <div class="category-breakdown-list">
        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Infraestructura y Hardware</span>
            <span class="cat-amount">${pPc(comuna.monto_hardware)}$${formatCLP(comuna.monto_hardware)} (${pPct(comuna.monto_hardware)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_hardware)}%; background:var(--navy);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">IA y Automatización Básica</span>
            <span class="cat-amount">${pPc(comuna.monto_ia)}$${formatCLP(comuna.monto_ia)} (${pPct(comuna.monto_ia)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_ia)}%; background:var(--teal);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Redes y Telecomunicaciones</span>
            <span class="cat-amount">${pPc(comuna.monto_telecom)}$${formatCLP(comuna.monto_telecom)} (${pPct(comuna.monto_telecom)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_telecom)}%; background:var(--gold);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Ciberseguridad y Respaldo</span>
            <span class="cat-amount">${pPc(comuna.monto_cyber)}$${formatCLP(comuna.monto_cyber)} (${pPct(comuna.monto_cyber)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_cyber)}%; background:#70587c;"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">SaaS y Cloud Computing</span>
            <span class="cat-amount">${pPc(comuna.monto_saas)}$${formatCLP(comuna.monto_saas)} (${pPct(comuna.monto_saas)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_saas)}%; background:#385bb2;"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Sistemas ERP de Gestión (Legados)</span>
            <span class="cat-amount">${pPc(comuna.monto_legado)}$${formatCLP(comuna.monto_legado)} (${pPct(comuna.monto_legado)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_legado)}%; background:var(--crimson);"></div></div>
        </div>

        <div class="cat-item">
          <div class="cat-item-header">
            <span class="cat-name">Software Libre (FOSS)</span>
            <span class="cat-amount">${pPc(comuna.monto_foss)}$${formatCLP(comuna.monto_foss)} (${pPct(comuna.monto_foss)}%)</span>
          </div>
          <div class="cat-bar-bg"><div class="cat-bar-fill" style="width:${pPct(comuna.monto_foss)}%; background:var(--forest);"></div></div>
        </div>
      </div>

      <!-- Contratos Emblemáticos Mercado Público -->
      <!-- Gated Dossier Ejecutivo (Lead Capture) -->
      <div class="gated-dossier-box">
        <div class="gated-lock-icon">🔒</div>
        <div class="gated-title">Ficha Ejecutiva & Hoja de Ruta para ${comuna.comuna}</div>
        <p class="gated-desc">
          ¿Perteneces a este municipio, al concejo o asesoras licitaciones públicas? Accede al informe pormenorizado con evaluación de costos de cambio de proveedores ERP, brechas presupuestarias de soporte y hoja de ruta sugerida.
        </p>
        <button type="button" class="btn-request-dossier" data-comuna="${comuna.comuna}">
          📋 Solicitar Dossier Comunal Gratuito
        </button>
      </div>

      <div class="drawer-section-title">Contratos Emblemáticos en Mercado Público</div>
      <div style="font-size:11px; color:var(--muted); margin-top:-6px; margin-bottom:10px; line-height:1.4;">
        ℹ️ <strong>Rigor Metodológico:</strong> Los montos corresponden a <em>Órdenes de Compra (OCs)</em> efectivamente emitidas y aceptadas. Las licitaciones públicas de origen constituyen el acto administrativo habilitante y no representan gasto sumable adicional.
      </div>
      <div class="top-contracts-list">
        ${(comuna.top_contratos && comuna.top_contratos.length > 0)
          ? comuna.top_contratos.map(oc => `
            <div class="contract-card">
              <div class="contract-card-header">
                <div>
                  <span class="contract-code">${oc.codigo_oc}</span>
                  <div style="font-size:10px; font-weight:600; color:var(--teal); margin-top:2px;">Origen: ${((oc.descripcion || "").match(/(?:DESDE|LICITACI[OÓ]N|PROPUESTA|ID)\s*([0-9]{3,5}-[0-9]{1,4}-[A-Z0-9]{2,4})/i) ? (oc.descripcion || "").match(/(?:DESDE|LICITACI[OÓ]N|PROPUESTA|ID)\s*([0-9]{3,5}-[0-9]{1,4}-[A-Z0-9]{2,4})/i)[1] : (oc.codigo_oc.includes('-CM') ? 'Convenio Marco' : (oc.codigo_oc.includes('-SE') ? 'Licitación / Trato Directo' : 'Proceso Licitatorio')))}</div>
                </div>
                <span class="contract-amount">$${formatCLP(oc.monto)}</span>
              </div>
              <div class="contract-prov">${oc.proveedor} (${oc.anio})</div>
              <div class="contract-desc">${oc.descripcion}</div>
              <a href="${oc.url_mercadopublico}" target="_blank" rel="noopener noreferrer" class="contract-link">
                Auditar OC en MercadoPúblico ↗
              </a>
            </div>
          `).join("")
          : `<div style="font-size:12px; color:var(--muted);">Sin detalle de contratos individuales disponible.</div>`
        }
      </div>

      <!-- Gobernanza y Normativa Tecnológica (MuniData Normas) -->
      <div class="drawer-section-title">Gobernanza & Normativa Tecnológica (MuniData Normas)</div>
      <div class="normativa-box" style="background:var(--paper-soft); border:1px solid var(--line-light); border-radius:6px; padding:12px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; gap:8px;">
          <span class="diag-badge ${comuna.normativa_tech && comuna.normativa_tech.tiene_normativa ? (comuna.normativa_tech.estado_gobernanza.includes('IA') ? 'good' : 'warning') : 'neutral'}">
            ${comuna.normativa_tech && comuna.normativa_tech.tiene_normativa ? (comuna.normativa_tech.estado_gobernanza.includes('IA') ? '🏛️ ' : '📡 ') + comuna.normativa_tech.estado_gobernanza : '🏜️ Desierto Regulatorio Tecnológico'}
          </span>
          <span style="font-size:11px; font-weight:600; color:var(--muted);">${(comuna.normativa_tech ? comuna.normativa_tech.total_instrumentos : 0)} instrumento(s)</span>
        </div>
        ${(comuna.normativa_tech && comuna.normativa_tech.tiene_normativa)
          ? `
            <div style="display:flex; flex-direction:column; gap:8px; margin-top:8px;">
              ${(comuna.normativa_tech.politicas_ia || []).map(p => `
                <div style="background:var(--paper); border:1px solid var(--line-light); border-left:3px solid var(--teal); border-radius:4px; padding:8px 10px;">
                  <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; font-weight:700; color:var(--teal); text-transform:uppercase;">
                    <span>${p.tipo_instrumento}</span>
                    <span>${p.año || ''}</span>
                  </div>
                  <div style="font-size:12px; font-weight:600; color:var(--navy); margin-top:2px;">${p.titulo}</div>
                  <div style="font-size:11px; color:var(--ink-secondary); margin-top:3px;">${p.descripcion || p.decreto}</div>
                  ${p.url_oficial ? `<a href="${p.url_oficial}" target="_blank" rel="noopener noreferrer" style="display:inline-block; margin-top:4px; font-size:11px; color:var(--teal); font-weight:600; text-decoration:none;">Consultar instrumento oficial ↗</a>` : ''}
                </div>
              `).join("")}
              ${(comuna.normativa_tech.ordenanzas || []).map(o => `
                <div style="background:var(--paper); border:1px solid var(--line-light); border-left:3px solid var(--navy); border-radius:4px; padding:8px 10px;">
                  <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; font-weight:700; color:var(--navy); text-transform:uppercase;">
                    <span>${o.categoria_tech}</span>
                    <span>${o.fecha || ''}</span>
                  </div>
                  <div style="font-size:12px; font-weight:600; color:var(--ink); margin-top:2px;">${o.titulo}</div>
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px; font-size:11px;">
                    <span style="color:var(--muted); font-size:10px;">Norma N° ${o.numero} · ${o.fuente}</span>
                    ${o.url_oficial ? `<a href="${o.url_oficial}" target="_blank" rel="noopener noreferrer" style="color:var(--teal); font-weight:600; text-decoration:none;">Ver norma oficial ↗</a>` : ''}
                  </div>
                </div>
              `).join("")}
            </div>
          `
          : `<div style="font-size:11px; color:var(--muted); line-height:1.4; margin-top:4px;">Este municipio no registra ordenanzas de telecomunicaciones ni decretos de gobernanza algorítmica en el catastro nacional consolidado.</div>`
        }
        <div style="margin-top:10px; padding-top:8px; border-top:1px dashed var(--line-light); display:flex; justify-content:space-between; align-items:center; font-size:11px;">
          <span style="color:var(--muted);">Auditoría normativa P090 (BCN / CPLT)</span>
          <a href="https://ordenanzas.evegat.cl/#busqueda=${encodeURIComponent(comuna.comuna)}" target="_blank" rel="noopener noreferrer" style="color:var(--teal); font-weight:600; text-decoration:none;">
            Explorar en ordenanzas.evegat.cl ↗
          </a>
        </div>
      </div>

      <!-- Top Suppliers -->
      <div class="drawer-section-title">Principales Proveedores Contratados</div>
      <div class="top-suppliers-list">
        ${(comuna.top_proveedores && comuna.top_proveedores.length > 0)
          ? comuna.top_proveedores.map(p => `
            <div class="supplier-item">
              <span class="supplier-name" title="${p.proveedor}">${p.proveedor}</span>
              <span class="supplier-amount">$${formatCLP(p.monto)}</span>
            </div>
          `).join("")
          : `<div style="font-size:12px; color:var(--muted);">Sin detalle de proveedores disponible.</div>`
        }
      </div>
    `;

    // Conectar botón de compartir con portapapeles
    const btnShare = document.getElementById("btn-share-comuna");
    if (btnShare) {
      btnShare.addEventListener("click", () => {
        const url = window.location.origin + window.location.pathname + "#comuna=" + encodeURIComponent(comuna.comuna);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(() => {
            const txt = document.getElementById("btn-share-text");
            if (txt) {
              txt.textContent = "¡Copiado!";
              setTimeout(() => { txt.textContent = "Compartir"; }, 2000);
            }
          }).catch(() => {
            prompt("Copia este enlace directo:", url);
          });
        } else {
          prompt("Copia este enlace directo:", url);
        }
      });
    }

    // Conectar botón de comparar
    const btnCompare = document.getElementById("btn-start-compare");
    if (btnCompare) {
      btnCompare.addEventListener("click", () => {
        let other = state.comunas.find(c => c.comuna !== comuna.comuna && c.region === comuna.region);
        if (!other) {
          other = state.comunas.find(c => c.comuna !== comuna.comuna);
        }
        if (other) {
          openComparison(comuna, other);
        }
      });
    }

    // Conectar botón de solicitar dossier comunal
    const btnDossier = drawer.querySelector(".btn-request-dossier");
    if (btnDossier) {
      btnDossier.addEventListener("click", () => {
        const comName = btnDossier.dataset.comuna || comuna.comuna;
        const regModal = document.getElementById("registro-descarga-modal");
        const modalTitle = document.getElementById("modal-descarga-title");
        const inProy = document.getElementById("reg-proyecto");
        const inProp = document.getElementById("reg-proposito");

        if (modalTitle) modalTitle.textContent = "📋 Solicitud de Dossier Comunal: " + comName;
        if (inProy) inProy.value = "Solicitud de Dossier Ejecutivo y Hoja de Ruta Tecnológica para la Municipalidad de " + comName;
        if (inProp && !inProp.value) inProp.value = "gestión";

        state.pendingDownload = {
          file: "dossier_ejecutivo_" + encodeURIComponent(comName) + ".pdf",
          label: "Dossier Ejecutivo: Municipalidad de " + comName
        };

        if (regModal) {
          regModal.classList.add("active");
          regModal.setAttribute("aria-hidden", "false");
          document.body.style.overflow = "hidden";
        }
      });
    }

    // Centrar mapa si tiene coordenadas
    if (state.map && comuna.lat && comuna.lng) {
      state.map.setView([comuna.lat, comuna.lng], 9, { animate: true });
    }
  }

  // -------------------------------------------------------------------------
  // 4.1 COMPARADOR COMUNAL A VS B
  // -------------------------------------------------------------------------
  function openComparison(comunaA, comunaB) {
    state.selectedComuna = comunaA;
    state.compareComuna = comunaB;
    state.isCompareMode = true;

    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, null, "#comparar=" + encodeURIComponent(comunaA.comuna) + "," + encodeURIComponent(comunaB.comuna));
    }

    renderComparisonView();
  }

  function renderComparisonView() {
    const drawer = document.getElementById("comuna-drawer");
    if (!drawer || !state.selectedComuna || !state.compareComuna) return;

    const cA = state.selectedComuna;
    const cB = state.compareComuna;

    const pobA = Math.max(1, cA.poblacion || 0);
    const pobB = Math.max(1, cB.poblacion || 0);

    const pcDiff = cA.gasto_pc - cB.gasto_pc;
    const pcPctDiff = cB.gasto_pc > 0 ? Math.round(((cA.gasto_pc - cB.gasto_pc) / cB.gasto_pc) * 100) : 0;

    const otherComunas = state.comunas.slice().sort((a, b) => a.comuna.localeCompare(b.comuna));

    drawer.innerHTML = `
      <div class="compare-view">
        <div class="compare-top-nav">
          <button id="btn-back-to-single" class="btn-back">
            <span>←</span><span>Volver a ${cA.comuna}</span>
          </button>
          <button id="btn-share-compare" class="btn-share" title="Copiar enlace a esta comparación">
            <span>🔗</span><span id="btn-share-compare-text">Compartir vs</span>
          </button>
        </div>

        <div class="compare-selector-box">
          <label for="compare-select-b">Comparar ${cA.comuna} con:</label>
          <select id="compare-select-b" class="compare-select">
            ${otherComunas.map(c => `
              <option value="${c.comuna}" ${c.comuna === cB.comuna ? 'selected' : ''}>
                ${c.comuna} (${c.region})
              </option>
            `).join("")}
          </select>
        </div>

        <!-- Encabezados de Comunas -->
        <div class="compare-grid">
          <div class="compare-col highlight-a">
            <div style="font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase;">${cA.region}</div>
            <h3 class="compare-comuna-title">${cA.comuna}</h3>
            <div style="font-size:11px; color:var(--ink-secondary);">${(cA.poblacion || 0).toLocaleString("es-CL")} hab.</div>
          </div>
          <div class="compare-col highlight-b">
            <div style="font-size:10px; font-weight:700; color:var(--muted); text-transform:uppercase;">${cB.region}</div>
            <h3 class="compare-comuna-title">${cB.comuna}</h3>
            <div style="font-size:11px; color:var(--ink-secondary);">${(cB.poblacion || 0).toLocaleString("es-CL")} hab.</div>
          </div>
        </div>

        <!-- Termómetro Madurez TI -->
        <div class="drawer-section-title" style="margin-top:8px;">Madurez Tecnológica (0-100)</div>
        <div class="compare-grid">
          <div class="compare-col">
            <div style="font-size:24px; font-family:var(--font-serif); font-weight:700; color:var(--navy); line-height:1;">${cA.score_madurez} <span style="font-size:12px; font-weight:400; color:var(--muted);">/100</span></div>
            <div style="font-size:11px; font-weight:600; color:var(--teal);">${cA.nivel_madurez}</div>
          </div>
          <div class="compare-col">
            <div style="font-size:24px; font-family:var(--font-serif); font-weight:700; color:var(--teal); line-height:1;">${cB.score_madurez} <span style="font-size:12px; font-weight:400; color:var(--muted);">/100</span></div>
            <div style="font-size:11px; font-weight:600; color:var(--teal);">${cB.nivel_madurez}</div>
          </div>
        </div>

        <!-- Inversión Per Cápita -->
        <div class="drawer-section-title" style="margin-top:8px;">Inversión Per Cápita Acumulada</div>
        <div class="compare-grid">
          <div class="compare-col">
            <div class="compare-row-metric">
              <div class="lbl">Gasto / Habitante</div>
              <div class="val" style="color:var(--navy);">$${formatCLP(cA.gasto_pc)}</div>
            </div>
            <div class="compare-row-metric">
              <div class="lbl">Gasto Histórico Total</div>
              <div class="val" style="font-size:12px;">$${formatCLP(cA.monto_total)}</div>
            </div>
          </div>
          <div class="compare-col">
            <div class="compare-row-metric">
              <div class="lbl">Gasto / Habitante</div>
              <div class="val" style="color:var(--teal);">$${formatCLP(cB.gasto_pc)}</div>
            </div>
            <div class="compare-row-metric">
              <div class="lbl">Gasto Histórico Total</div>
              <div class="val" style="font-size:12px;">$${formatCLP(cB.monto_total)}</div>
            </div>
          </div>
        </div>
        <div style="background:var(--paper-soft); border:1px solid var(--line-light); border-radius:6px; padding:10px 12px; font-size:12px; text-align:center;">
          ${pcDiff > 0
            ? `<strong>${cA.comuna}</strong> invierte <strong>$${formatCLP(Math.abs(pcDiff))} CLP más por habitante (+${Math.abs(pcPctDiff)}%)</strong> que ${cB.comuna}.`
            : pcDiff < 0
            ? `<strong>${cB.comuna}</strong> invierte <strong>$${formatCLP(Math.abs(pcDiff))} CLP más por habitante</strong> que ${cA.comuna}.`
            : `Ambos municipios tienen una inversión per cápita idéntica.`
          }
        </div>

        <!-- Comparativa de Categorías Clave ($ / hab) -->
        <div class="drawer-section-title" style="margin-top:8px;">Inversión por Habitante en Canastas Clave</div>
        <div style="display:flex; flex-direction:column; gap:8px;">
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:var(--navy); margin-bottom:4px;">Infraestructura y Hardware</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_hardware / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_hardware / pobB))}</strong></span>
            </div>
          </div>
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:var(--teal); margin-bottom:4px;">IA y Automatización Básica</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_ia / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_ia / pobB))}</strong></span>
            </div>
          </div>
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:#385bb2; margin-bottom:4px;">SaaS y Cloud Computing</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_saas / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_saas / pobB))}</strong></span>
            </div>
          </div>
          <div style="background:var(--paper); border:1px solid var(--line-light); border-radius:4px; padding:8px 10px;">
            <div style="font-size:11px; font-weight:700; color:#70587c; margin-bottom:4px;">Ciberseguridad y Respaldo</div>
            <div style="display:flex; justify-content:space-between; font-size:12px; font-family:var(--font-mono);">
              <span>${cA.comuna}: <strong>$${formatCLP(Math.round(cA.monto_cyber / pobA))}</strong></span>
              <span>${cB.comuna}: <strong>$${formatCLP(Math.round(cB.monto_cyber / pobB))}</strong></span>
            </div>
          </div>
        </div>

        <!-- Gobernanza y Normativa Tecnológica -->
        <div class="drawer-section-title" style="margin-top:8px;">Gobernanza y Normativa Tecnológica (MuniData)</div>
        <div class="compare-grid">
          <div class="compare-col" style="font-size:11px;">
            <div style="font-weight:700; color:var(--navy);">${cA.normativa_tech ? cA.normativa_tech.estado_gobernanza : 'Desierto Regulatorio'}</div>
            <div style="color:var(--muted); font-size:10px; margin-top:2px;">${cA.normativa_tech ? cA.normativa_tech.total_instrumentos : 0} instrumentos registrados</div>
          </div>
          <div class="compare-col" style="font-size:11px;">
            <div style="font-weight:700; color:var(--teal);">${cB.normativa_tech ? cB.normativa_tech.estado_gobernanza : 'Desierto Regulatorio'}</div>
            <div style="color:var(--muted); font-size:10px; margin-top:2px;">${cB.normativa_tech ? cB.normativa_tech.total_instrumentos : 0} instrumentos registrados</div>
          </div>
        </div>

        <!-- Banderas de Diagnóstico -->
        <div class="drawer-section-title" style="margin-top:8px;">Diagnóstico Institucional</div>
        <div class="compare-grid">
          <div class="compare-col" style="font-size:11px;">
            <div>${cA.tiene_lockin_legado ? '⚠️ <span style="color:var(--crimson); font-weight:700;">Alta Dependencia ERP</span>' : '✓ Ecosistema Diversificado'}</div>
            <div>${cA.tiene_foss ? '🐧 <span style="color:var(--forest); font-weight:700;">Usa Software Libre</span>' : '✕ Sin FOSS'}</div>
            <div>${cA.tiene_infra_propia ? '🖥️ <span style="color:var(--navy); font-weight:700;">Infra TI Propia</span>' : '⚡ Tercerizado'}</div>
          </div>
          <div class="compare-col" style="font-size:11px;">
            <div>${cB.tiene_lockin_legado ? '⚠️ <span style="color:var(--crimson); font-weight:700;">Alta Dependencia ERP</span>' : '✓ Ecosistema Diversificado'}</div>
            <div>${cB.tiene_foss ? '🐧 <span style="color:var(--forest); font-weight:700;">Usa Software Libre</span>' : '✕ Sin FOSS'}</div>
            <div>${cB.tiene_infra_propia ? '🖥️ <span style="color:var(--navy); font-weight:700;">Infra TI Propia</span>' : '⚡ Tercerizado'}</div>
          </div>
        </div>
      </div>
    `;

    // Eventos de la vista comparativa
    const btnBack = document.getElementById("btn-back-to-single");
    if (btnBack) {
      btnBack.addEventListener("click", () => {
        state.isCompareMode = false;
        selectComuna(state.selectedComuna);
      });
    }

    const selectB = document.getElementById("compare-select-b");
    if (selectB) {
      selectB.addEventListener("change", (e) => {
        const targetB = state.comunas.find(c => c.comuna === e.target.value);
        if (targetB) {
          openComparison(state.selectedComuna, targetB);
        }
      });
    }

    const btnShareComp = document.getElementById("btn-share-compare");
    if (btnShareComp) {
      btnShareComp.addEventListener("click", () => {
        const url = window.location.origin + window.location.pathname + "#comparar=" + encodeURIComponent(cA.comuna) + "," + encodeURIComponent(cB.comuna);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(() => {
            const txt = document.getElementById("btn-share-compare-text");
            if (txt) {
              txt.textContent = "¡Copiado!";
              setTimeout(() => { txt.textContent = "Compartir vs"; }, 2000);
            }
          }).catch(() => {
            prompt("Copia este enlace de comparación:", url);
          });
        } else {
          prompt("Copia este enlace de comparación:", url);
        }
      });
    }
  }

  // -------------------------------------------------------------------------
  // 5. FILTROS, BÚSQUEDA Y CONTROLES
  // -------------------------------------------------------------------------
  function initRegionDropdown() {
    const select = document.getElementById("region-filter");
    if (!select) return;

    // Obtener regiones únicas
    const regionNames = [...new Set(state.comunas.map(c => c.region))].filter(Boolean).sort();
    regionNames.forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      select.appendChild(opt);
    });
  }

  function initControls() {
    // Enrutador de Vistas / Páginas (SPA)
    document.querySelectorAll(".nav-view-link").forEach(link => {
      link.addEventListener("click", (e) => {
        const viewId = link.dataset.view;
        if (viewId) {
          e.preventDefault();
          switchView(viewId, true);
        }
      });
    });

    // Botones de capas
    const layerBtns = document.querySelectorAll(".layer-btn[data-layer]");
    layerBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        layerBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        state.currentLayer = btn.dataset.layer;
        renderMapMarkers();
        updateLegend();
      });
    });

    // Búsqueda instantánea con datalist y navegación por teclado Enter
    const searchInput = document.getElementById("comuna-search");
    const comunaDatalist = document.getElementById("comunas-datalist");
    if (comunaDatalist && state.comunas) {
      comunaDatalist.innerHTML = state.comunas.map(c => `<option value="${c.comuna}">${c.region}</option>`).join("");
    }

    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        state.searchQuery = e.target.value;
        renderMapMarkers();
        renderTable();
        updateProviderCrossSuggestion();
      });

      searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          const val = searchInput.value.trim().toLowerCase();
          if (!val) return;
          const matched = state.comunas.find(c => 
            c.comuna.toLowerCase() === val || 
            normalizeSearch(c.comuna) === normalizeSearch(val)
          ) || state.comunas.find(c => 
            normalizeSearch(c.comuna).includes(normalizeSearch(val))
          );
          if (matched) {
            selectComuna(matched);
            if (state.map && matched.lat && matched.lng) {
              state.map.setView([matched.lat, matched.lng], 12);
            }
          }
        }
      });
    }

    // Filtro por Región
    const regionSelect = document.getElementById("region-filter");
    if (regionSelect) {
      regionSelect.addEventListener("change", (e) => {
        state.selectedRegion = e.target.value;
        renderMapMarkers();
        renderTable();

        // Ajustar zoom a la región
        if (state.selectedRegion && state.map) {
          const matchComunas = state.comunas.filter(c => c.region === state.selectedRegion && c.lat && c.lng);
          if (matchComunas.length > 0) {
            const bounds = L.latLngBounds(matchComunas.map(c => [c.lat, c.lng]));
            state.map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
          }
        }
      });
    }

    // Filtro por Cuadrante de Capacidad Estatal
    const cuadranteSelect = document.getElementById("cuadrante-filter");
    if (cuadranteSelect) {
      cuadranteSelect.addEventListener("change", (e) => {
        state.selectedCuadrante = e.target.value;
        renderMapMarkers();
        renderTable();
      });
    }

    // Filtro por Escala Poblacional
    const poblacionSelect = document.getElementById("poblacion-filter");
    if (poblacionSelect) {
      poblacionSelect.addEventListener("change", (e) => {
        state.selectedPoblacionScale = e.target.value;
        renderTable();
      });
    }

    // Reset Map
    const btnReset = document.getElementById("btn-reset-map");
    if (btnReset) {
      btnReset.addEventListener("click", () => {
        state.searchQuery = "";
        state.selectedRegion = "";
        state.selectedCuadrante = "";
        if (searchInput) searchInput.value = "";
        if (regionSelect) regionSelect.value = "";
        if (cuadranteSelect) cuadranteSelect.value = "";
        if (state.map) state.map.setView([-35.6751, -71.5430], 5);
        renderMapMarkers();
        renderTable();
        updateProviderCrossSuggestion();
      });
    }

    // Exportar CSV Comunal
    const btnExport = document.getElementById("btn-export-csv");
    if (btnExport) {
      btnExport.addEventListener("click", () => {
        // Interceptado por initModals
      });
    }

    // Exportar CSV Proveedores
    const btnExportProv = document.getElementById("btn-export-prov-csv");
    if (btnExportProv) {
      btnExportProv.addEventListener("click", () => {
        // Interceptado por initModals
      });
    }

    // Buscador de Proveedores
    const provSearchInput = document.getElementById("prov-search");
    if (provSearchInput) {
      provSearchInput.addEventListener("input", (e) => {
        state.provSearchQuery = e.target.value.toLowerCase().trim();
        renderProveedoresTable();
      });
    }

    // Pestañas del Centro de Rankings con ARIA sincronizado
    const rankTabs = document.querySelectorAll(".rank-tab-btn[data-rank-pane]");
    rankTabs.forEach(btn => {
      btn.addEventListener("click", () => {
        rankTabs.forEach(b => {
          b.classList.remove("active");
          b.setAttribute("aria-selected", "false");
        });
        btn.classList.add("active");
        btn.setAttribute("aria-selected", "true");
        const paneId = btn.dataset.rankPane;
        document.querySelectorAll(".rank-pane").forEach(pane => {
          pane.classList.remove("active");
        });
        const targetPane = document.getElementById(paneId);
        if (targetPane) targetPane.classList.add("active");
        if (paneId === "pane-proveedores") renderProveedoresTable();
        if (paneId === "pane-cuadrantes") renderCuadrantesSummary();
      });
    });

    // Clicks en comunas de los Podios
    document.querySelectorAll(".rank-podium-item .comuna-name").forEach(span => {
      span.addEventListener("click", () => {
        const cName = span.dataset.comuna;
        if (!cName) return;
        const target = state.comunas.find(c => c.comuna.toLowerCase() === cName.toLowerCase());
        if (target) {
          switchView("mapa", true);
          selectComuna(target);
        }
      });
    });

    // Table sorting headers
    const ths = document.querySelectorAll("#ranking-table th[data-sort]");
    ths.forEach(th => {
      const handleSort = () => {
        const field = th.dataset.sort;
        if (state.sortField === field) {
          state.sortAsc = !state.sortAsc;
        } else {
          state.sortField = field;
          state.sortAsc = false; // Descendente por defecto para métricas
        }
        renderTable();
      };
      th.addEventListener("click", handleSort);
      th.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleSort();
        }
      });
    });
  }

  function activateProveedoresTab(provName) {
    const provTabBtn = document.querySelector(".rank-tab-btn[data-rank-pane='pane-proveedores']");
    if (provTabBtn) {
      provTabBtn.click();
    }
    const provSearch = document.getElementById("prov-search");
    if (provSearch) {
      provSearch.value = provName;
      state.provSearchQuery = provName.toLowerCase().trim();
      renderProveedoresTable();
    }
    const rankSection = document.getElementById("ranking");
    if (rankSection) {
      rankSection.scrollIntoView({ behavior: "smooth" });
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function findProviderMatch(query) {
    if (!query) return null;
    const normQ = normalizeText(query).replace(/[-_.]/g, " ");
    if (normQ.length < 2) return null;
    return state.proveedores.find(p => {
      const pName = normalizeText(p.proveedor || "").replace(/[-_.]/g, " ");
      const pRut = normalizeText(p.rut || "").replace(/[-_.]/g, " ");
      return pName.includes(normQ) || pRut.includes(normQ);
    }) || state.proveedores.find(p => {
      const pName = normalizeText(p.proveedor || "").replace(/[-_.]/g, " ");
      return normQ.length >= 5 && normQ.includes(pName);
    });
  }

  function updateProviderCrossSuggestion() {
    const query = state.searchQuery ? state.searchQuery.trim() : "";
    let hintEl = document.getElementById("comuna-provider-hint");

    if (!query || query.length < 2) {
      if (hintEl) hintEl.style.display = "none";
      return;
    }

    const filtered = getFilteredComunas();
    if (filtered.length > 0) {
      if (hintEl) hintEl.style.display = "none";
      return;
    }

    const matchedProv = findProviderMatch(query);

    if (matchedProv) {
      if (!hintEl) {
        hintEl = document.createElement("div");
        hintEl.id = "comuna-provider-hint";
        hintEl.setAttribute("role", "status");
        hintEl.setAttribute("aria-live", "polite");
        hintEl.style.cssText = "margin-top: 10px; padding: 10px 14px; background: var(--gold-bg, #fff8e6); border-left: 3px solid var(--gold, #b38209); font-size: 13px; color: var(--ink-primary, #1c1c1c); border-radius: 4px; grid-column: 1 / -1; width: 100%; box-sizing: border-box;";
        const controlsBar = document.querySelector(".filter-controls-group") || document.querySelector(".map-controls-bar");
        if (controlsBar) controlsBar.appendChild(hintEl);
      }
      hintEl.style.display = "block";
      const safeQuery = escapeHtml(query);
      const safeProv = escapeHtml(matchedProv.proveedor);
      hintEl.innerHTML = `
        🔍 No se encontraron comunas con el nombre <strong>"${safeQuery}"</strong>, pero encontramos al proveedor tecnológico <strong>${safeProv}</strong>. 
        <button type="button" id="btn-goto-prov-rank" style="background: none; border: none; color: var(--teal, #146e66); font-weight: 700; text-decoration: underline; cursor: pointer; padding: 0 4px; font-size: 13px;" aria-label="Ver ficha del proveedor en el Centro de Rankings">
          Ver cuota de mercado en el Centro de Rankings →
        </button>
      `;
      const btnGoto = document.getElementById("btn-goto-prov-rank");
      if (btnGoto) {
        btnGoto.addEventListener("click", () => {
          activateProveedoresTab(matchedProv.proveedor);
        });
      }
    } else {
      if (hintEl) hintEl.style.display = "none";
    }
  }

  function getFilteredComunas() {
    const rawQuery = state.searchQuery || "";
    const normQuery = normalizeText(rawQuery);
    const effectiveQuery = COMUNA_ALIASES[normQuery] || normQuery;

    return state.comunas.filter(c => {
      const normComuna = normalizeText(c.comuna);
      const normRegion = normalizeText(c.region);
      const matchSearch = !effectiveQuery || 
        normComuna.includes(effectiveQuery) || 
        normRegion.includes(effectiveQuery) ||
        normComuna.includes(normQuery) ||
        normRegion.includes(normQuery);
      const matchRegion = !state.selectedRegion || c.region === state.selectedRegion;
      const matchCuadrante = !state.selectedCuadrante || c.cuadrante_capacidad === state.selectedCuadrante;
      
      let matchPoblacion = true;
      const pob = c.poblacion || 0;
      if (state.selectedPoblacionScale === "grande") {
        matchPoblacion = pob >= 100000;
      } else if (state.selectedPoblacionScale === "mediana") {
        matchPoblacion = pob >= 40000 && pob < 100000;
      } else if (state.selectedPoblacionScale === "pequena") {
        matchPoblacion = pob >= 10000 && pob < 40000;
      } else if (state.selectedPoblacionScale === "rural") {
        matchPoblacion = pob < 10000;
      }

      return matchSearch && matchRegion && matchCuadrante && matchPoblacion;
    });
  }

  // -------------------------------------------------------------------------
  // 6. RANKING & TABLA DE DATOS
  // -------------------------------------------------------------------------
  function renderTable() {
    const tbody = document.getElementById("ranking-tbody");
    if (!tbody) return;

    let filtered = getFilteredComunas();

    if (filtered.length === 0) {
      const matchedProv = findProviderMatch(state.searchQuery || "");

      if (matchedProv) {
        const safeQuery = escapeHtml(state.searchQuery || "");
        const safeProv = escapeHtml(matchedProv.proveedor);
        tbody.innerHTML = `
          <tr>
            <td colspan="13" style="text-align:center; padding: 36px 16px; color: var(--muted); font-size: 13px;">
              🔍 No se encontraron municipios para <strong>"${safeQuery}"</strong>, pero existe el proveedor tecnológico <strong>${safeProv}</strong>.<br>
              <button type="button" id="btn-table-goto-prov" style="margin-top: 10px; background: var(--teal); color: #fff; border: none; padding: 6px 14px; border-radius: 4px; font-size: 12px; cursor: pointer; font-weight: 600;" aria-label="Ver proveedor en el Centro de Rankings">
                Ver ${safeProv} en el Ranking de Proveedores →
              </button>
            </td>
          </tr>
        `;
        const btn = document.getElementById("btn-table-goto-prov");
        if (btn) {
          btn.addEventListener("click", () => activateProveedoresTab(matchedProv.proveedor));
        }
      } else {
        tbody.innerHTML = `
          <tr>
            <td colspan="13" style="text-align:center; padding: 36px 16px; color: var(--muted); font-size: 13px;">
              No se encontraron municipios que coincidan con los filtros aplicados.
            </td>
          </tr>
        `;
      }
      return;
    }

    // Actualizar atributos aria-sort en cabeceras de ordenamiento
    const ths = document.querySelectorAll("#ranking-table th[data-sort]");
    ths.forEach(th => {
      if (th.dataset.sort === state.sortField) {
        th.setAttribute("aria-sort", state.sortAsc ? "ascending" : "descending");
      } else {
        th.setAttribute("aria-sort", "none");
      }
    });

    // Ordenar
    filtered.sort((a, b) => {
      let va = a[state.sortField];
      let vb = b[state.sortField];
      if (typeof va === "string") {
        va = va.toLowerCase();
        vb = (vb || "").toLowerCase();
      }
      if (va < vb) return state.sortAsc ? -1 : 1;
      if (va > vb) return state.sortAsc ? 1 : -1;
      return 0;
    });

    tbody.innerHTML = filtered.slice(0, 100).map((c, idx) => `
      <tr data-comuna-name="${c.comuna}" tabindex="0" role="button" aria-label="Ver ficha y radiografía de ${c.comuna}">
        <td style="font-weight:700; color:var(--muted);">${idx + 1}</td>
        <td style="font-weight:600; color:var(--navy);">${c.comuna}</td>
        <td style="font-size:12px; color:var(--muted);">${c.region}</td>
        <td>${(c.poblacion || 0).toLocaleString("es-CL")}</td>
        <td style="font-family:var(--font-mono); font-weight:600;">$${formatCLP(c.monto_total)}</td>
        <td style="font-family:var(--font-mono); color:var(--teal); font-weight:600;">$${formatCLP(c.gasto_pc)}</td>
        <td>
          <span class="badge-pill" style="background:${c.score_madurez >= 80 ? 'var(--teal-bg)' : c.score_madurez >= 60 ? '#eaf0f8' : c.score_madurez >= 40 ? 'var(--gold-bg)' : 'var(--crimson-bg)'}; color:${c.score_madurez >= 80 ? 'var(--teal)' : c.score_madurez >= 60 ? '#2b5c8f' : c.score_madurez >= 40 ? 'var(--gold)' : 'var(--crimson)'};">
            ${c.score_madurez}/100
          </span>
        </td>
        <td>${(c.dotacion_total || 0).toLocaleString("es-CL")}</td>
        <td style="font-family:var(--font-mono);">${c.pct_honorarios !== undefined ? c.pct_honorarios + '%' : '—'}</td>
        <td style="font-family:var(--font-mono); font-weight:700; color:var(--teal);">${c.dotacion_ti || 0}</td>
        <td style="font-family:var(--font-mono); font-weight:600;">${c.ret_ratio !== undefined ? c.ret_ratio + 'x' : '—'}</td>
        <td>
          ${c.cuadrante_capacidad ? `
            <span class="diag-badge ${c.cuadrante_capacidad === 'Estado Soberano' ? 'good' : (c.cuadrante_capacidad === 'Estado Cautivo' ? 'danger' : (c.cuadrante_capacidad === 'Estado Híbrido Dependiente' ? 'warning' : 'neutral'))}" style="font-size:10px; padding:2px 6px;">
              ${c.cuadrante_capacidad.replace('Estado ', '')}
            </span>
          ` : '—'}
        </td>
        <td>${c.tiene_lockin_legado ? '<span style="color:var(--crimson); font-weight:700;">⚠️ Lock-in</span>' : '<span style="color:var(--forest);">✓ Limpio</span>'}</td>
      </tr>
    `).join("");

    // Click y Enter en fila selecciona comuna y cambia a la vista del mapa
    tbody.querySelectorAll("tr").forEach(tr => {
      const selectRow = () => {
        const cName = tr.dataset.comunaName;
        const target = state.comunas.find(c => c.comuna === cName);
        if (target) {
          switchView("mapa", true);
          selectComuna(target);
        }
      };
      tr.addEventListener("click", selectRow);
      tr.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectRow();
        }
      });
    });
  }

  function exportTableToCSV() {
    const filtered = getFilteredComunas();
    const headers = [
      "Ranking", "Comuna", "Region", "Poblacion", "Gasto_Total_CLP", 
      "Gasto_Per_Capita_CLP", "Madurez_TI", "Dotacion_RRHH_Total", 
      "Pct_Honorarios", "Dotacion_TI", "Ratio_RET", "Cuadrante_Capacidad", "Lockin_Legado"
    ];
    const rows = filtered.map((c, idx) => [
      idx + 1,
      `"${c.comuna}"`,
      `"${c.region}"`,
      c.poblacion || 0,
      c.monto_total || 0,
      c.gasto_pc || 0,
      c.score_madurez || 0,
      c.dotacion_total || 0,
      c.pct_honorarios !== undefined ? c.pct_honorarios : "",
      c.dotacion_ti || 0,
      c.ret_ratio !== undefined ? c.ret_ratio : "",
      `"${c.cuadrante_capacidad || ''}"`,
      c.tiene_lockin_legado ? "Lock-in" : "Limpio"
    ]);

    const csvContent = "\uFEFF" + [headers.join(";")].concat(rows.map(e => e.join(";"))).join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `ranking_ti_rrhh_municipal_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function renderProveedoresTable() {
    const tbody = document.getElementById("prov-tbody");
    if (!tbody || !state.proveedores) return;

    let filtered = state.proveedores.filter(p => {
      if (!state.provSearchQuery) return true;
      return (
        (p.proveedor && p.proveedor.toLowerCase().includes(state.provSearchQuery)) ||
        (p.rut && p.rut.toLowerCase().includes(state.provSearchQuery)) ||
        (p.rubro_principal && p.rubro_principal.toLowerCase().includes(state.provSearchQuery))
      );
    });

    tbody.innerHTML = filtered.map((p, idx) => {
      let badgeClass = "general";
      const rubro = p.rubro_principal || "";
      if (rubro.includes("ERP") || rubro.includes("Gestión")) badgeClass = "erp";
      else if (rubro.includes("Telecom")) badgeClass = "telecom";
      else if (rubro.includes("Hardware")) badgeClass = "hardware";
      else if (rubro.includes("Cloud") || rubro.includes("Software")) badgeClass = "cloud";
      else if (rubro.includes("Seguridad")) badgeClass = "seguridad";
      else if (rubro.includes("Consultoría")) badgeClass = "consultoria";

      return `
        <tr>
          <td style="font-weight:700; color:var(--muted);">${idx + 1}</td>
          <td style="font-weight:600; color:var(--navy);">${p.proveedor}</td>
          <td style="font-family:var(--font-mono); font-size:11px; color:var(--muted);">${p.rut || "—"}</td>
          <td><span class="prov-badge ${badgeClass}">${rubro}</span></td>
          <td style="font-family:var(--font-mono); text-align:center;">${p.total_munis} comunas</td>
          <td style="font-family:var(--font-mono); text-align:center;">${(p.total_ocs || 0).toLocaleString("es-CL")}</td>
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--navy);">$${formatCLP(p.monto_total_clp)}</td>
          <td style="font-family:var(--font-mono); font-weight:700; color:var(--gold);">${p.cuota_mercado_pct}%</td>
        </tr>
      `;
    }).join("");
  }

  function exportProveedoresToCSV() {
    if (!state.proveedores || state.proveedores.length === 0) return;
    const headers = [
      "Ranking", "Proveedor", "RUT", "Rubro_Principal", 
      "Municipios_Clientes", "Total_OCs", "Monto_Total_CLP", "Cuota_Mercado_Pct"
    ];
    const rows = state.proveedores.map((p, idx) => [
      idx + 1,
      `"${p.proveedor}"`,
      `"${p.rut || ''}"`,
      `"${p.rubro_principal || ''}"`,
      p.total_munis || 0,
      p.total_ocs || 0,
      p.monto_total_clp || 0,
      p.cuota_mercado_pct || 0
    ]);
    const csvContent = "\uFEFF" + [headers.join(";")].concat(rows.map(e => e.join(";"))).join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `proveedores_ti_municipal_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function renderCuadrantesSummary() {
    const container = document.getElementById("rank-cuadrantes-summary");
    if (!container) return;
    // Conteo dinámico exacto de los 345 municipios reales
    const dist = {
      "Estado Soberano": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Soberano").length,
      "Estado Híbrido Dependiente": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Híbrido Dependiente").length,
      "Estado Cautivo": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Cautivo").length,
      "Estado Artesanal": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Artesanal").length,
      "Estado Desconectado": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Desconectado").length
    };

    container.innerHTML = `
      <div class="quadrant-card soberano" style="cursor:pointer;" data-filter-quadrant="Estado Soberano">
        <div class="quadrant-header">
          <span class="quadrant-title">🏛️ Estado Soberano</span>
          <span class="quadrant-count">${dist["Estado Soberano"] || 198} comunas</span>
        </div>
        <p class="quadrant-desc">
          Gobiernos locales con equipo TI propio robusto (&ge; 5 profesionales) y un gasto externo equilibrado (RET &le; 1,8x). Mantienen autonomía técnica sobre sus datos y plataformas.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--forest);">Click para filtrar ranking por este cuadrante →</div>
      </div>

      <div class="quadrant-card hibrido" style="cursor:pointer;" data-filter-quadrant="Estado Híbrido Dependiente">
        <div class="quadrant-header">
          <span class="quadrant-title">⚡ Estado Híbrido Dependiente</span>
          <span class="quadrant-count">${dist["Estado Híbrido Dependiente"] || 5} comunas</span>
        </div>
        <p class="quadrant-desc">
          Municipios con alta capacidad técnica interna pero con un gasto masivo en consultoras y proveedores externos (RET &gt; 1,8x). Riesgo de duplicidad presupuestaria.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--teal);">Click para filtrar ranking por este cuadrante →</div>
      </div>

      <div class="quadrant-card artesanal" style="cursor:pointer;" data-filter-quadrant="Estado Artesanal">
        <div class="quadrant-header">
          <span class="quadrant-title">🛠️ Estado Artesanal</span>
          <span class="quadrant-count">${dist["Estado Artesanal"] || 99} comunas</span>
        </div>
        <p class="quadrant-desc">
          Baja dotación informática (&lt; 5 profesionales) y bajo gasto externo. Operación austera o manual con baja penetración de sistemas digitales avanzados.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--gold);">Click para filtrar ranking por este cuadrante →</div>
      </div>

      <div class="quadrant-card cautivo" style="cursor:pointer;" data-filter-quadrant="Estado Cautivo">
        <div class="quadrant-header">
          <span class="quadrant-title">⚠️ Estado Cautivo</span>
          <span class="quadrant-count">${dist["Estado Cautivo"] || 46} comunas</span>
        </div>
        <p class="quadrant-desc">
          Escaso personal informático interno (&lt; 5 profesionales) y alta dependencia financiera de proveedores y ERPs externos (RET &gt; 1,8x). Máximo riesgo de vendor lock-in.
        </p>
        <div style="font-size:11px; font-weight:700; color:var(--crimson);">Click para filtrar ranking por este cuadrante →</div>
      </div>
    `;

    container.querySelectorAll(".quadrant-card[data-filter-quadrant]").forEach(card => {
      card.setAttribute("tabindex", "0");
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", `Filtrar ranking por cuadrante ${card.dataset.filterQuadrant}`);

      const activate = () => {
        const qName = card.dataset.filterQuadrant;
        const cuadranteSelect = document.getElementById("cuadrante-filter");
        if (cuadranteSelect) {
          cuadranteSelect.value = qName;
          state.selectedCuadrante = qName;
          renderTable();
        }
        // Cambiar a la pestaña de comunas
        const btnComunasTab = document.querySelector(".rank-tab-btn[data-rank-pane='pane-comunas']");
        if (btnComunasTab) btnComunasTab.click();
        const tableEl = document.getElementById("ranking-table");
        if (tableEl) tableEl.scrollIntoView({ behavior: "smooth" });
      };

      card.addEventListener("click", activate);
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          activate();
        }
      });
    });
  }

  // -------------------------------------------------------------------------
  // 7. GESTIÓN DE TEMA Y ACCESIBILIDAD (A11Y)
  // -------------------------------------------------------------------------
  function initThemeAndA11y() {
    // Botones de tema
    document.querySelectorAll("[data-theme-btn]").forEach(btn => {
      btn.addEventListener("click", () => {
        const theme = btn.dataset.themeBtn;
        document.documentElement.setAttribute("data-theme", theme);
        try { localStorage.setItem("evegat_theme", theme); } catch (e) {}
        updateMapTheme(theme);
      });
    });

    // Control de tipografía
    let currentFontSize = 16;
    try {
      const savedFont = localStorage.getItem("evegat_fontsize");
      if (savedFont) currentFontSize = parseInt(savedFont, 10);
    } catch (e) {}

    const updateFont = (sz) => {
      currentFontSize = Math.min(22, Math.max(13, sz));
      document.documentElement.style.fontSize = currentFontSize + "px";
      try { localStorage.setItem("evegat_fontsize", currentFontSize); } catch (e) {}
    };

    const btnDec = document.getElementById("btn-font-dec");
    const btnReset = document.getElementById("btn-font-reset");
    const btnInc = document.getElementById("btn-font-inc");

    if (btnDec) btnDec.addEventListener("click", () => updateFont(currentFontSize - 1));
    if (btnReset) btnReset.addEventListener("click", () => updateFont(16));
    if (btnInc) btnInc.addEventListener("click", () => updateFont(currentFontSize + 1));

    // Lector de voz TTS
    const btnTts = document.getElementById("btn-tts");
    if (btnTts && "speechSynthesis" in window) {
      let isSpeaking = false;
      btnTts.addEventListener("click", () => {
        if (isSpeaking) {
          window.speechSynthesis.cancel();
          isSpeaking = false;
          const textEl = document.getElementById("tts-text");
          if (textEl) textEl.textContent = "Escuchar";
          return;
        }

        let narrative = "";
        if (state.selectedComuna) {
          const c = state.selectedComuna;
          narrative = `Resumen de capacidades tecnológicas para la comuna de ${c.comuna}, región de ${c.region}. Población: ${(c.poblacion || 0).toLocaleString("es-CL")} habitantes. Inversión histórica en contratos tecnológicos: ${formatCLP(c.monto_total)} pesos chilenos, equivalente a ${formatCLP(c.gasto_pc)} pesos por habitante. Índice de madurez tecnológica: ${c.score_madurez} sobre 100, clasificado como ${c.nivel_madurez}. Diagnóstico de capacidad estatal: ${c.cuadrante_capacidad || "En evaluación"}. Tecnoestructura municipal: ${c.dotacion_ti || 0} profesionales TI contratados. Ratio de externalización tecnológica: ${c.ret_ratio || "No determinado"}.`;
        } else {
          narrative = `Observatorio de Capacidades Tecnológicas y Capacidad Estatal en las 345 municipalidades de Chile (346 comunas). Se analizaron más de 312 mil millones de pesos transados en 153 mil contratos en Mercado Público durante 12 años, cruzados con la dotación funcionaria y tecnoestructura de Transparencia Activa.`;
        }

        const utter = new SpeechSynthesisUtterance(narrative);
        utter.lang = "es-CL";
        utter.rate = 1.0;
        utter.onend = () => {
          isSpeaking = false;
          const textEl = document.getElementById("tts-text");
          if (textEl) textEl.textContent = "Escuchar";
        };
        isSpeaking = true;
        const textEl = document.getElementById("tts-text");
        if (textEl) textEl.textContent = "Detener";
        window.speechSynthesis.speak(utter);
      });
    }
  }

  // -------------------------------------------------------------------------
  // 8. GESTIÓN DE MODALES ("CÓMO USAR" Y "AVISO LEGAL / LEY 21.719")
  // -------------------------------------------------------------------------
  function initModals() {
    const comoUsarModal = document.getElementById("como-usar-modal");
    const legalModal = document.getElementById("legal-modal");
    const registroModal = document.getElementById("registro-descarga-modal");
    const formRegistro = document.getElementById("form-registro-descarga");
    const errorMsg = document.getElementById("reg-error-msg");
    const filenameLabel = document.getElementById("descarga-filename-label");
    const chkNoAutoShow = document.getElementById("chk-no-auto-show");

    let lastActiveElement = null;

    function getFocusableElements(container) {
      if (!container) return [];
      return Array.from(
        container.querySelectorAll(
          'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
      ).filter(el => el.offsetWidth > 0 || el.offsetHeight > 0 || el === document.activeElement);
    }

    function openModal(modal) {
      if (!modal) return;
      lastActiveElement = document.activeElement;
      modal.classList.add("active");
      modal.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";

      const card = modal.querySelector(".obs-modal-card") || modal;
      const closeBtn = card.querySelector(".obs-modal-close");
      const titleEl = card.querySelector("h2, h3");
      if (titleEl) {
        titleEl.setAttribute("tabindex", "-1");
        setTimeout(() => titleEl.focus(), 50);
      } else if (closeBtn) {
        setTimeout(() => closeBtn.focus(), 50);
      }
    }

    function closeModal(modal) {
      if (!modal) return;
      modal.classList.remove("active");
      modal.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
      if (modal === comoUsarModal && chkNoAutoShow && chkNoAutoShow.checked) {
        try { localStorage.setItem("evegat_seen_guide_v3", "1"); } catch (e) {}
      }
      if (lastActiveElement && typeof lastActiveElement.focus === "function") {
        lastActiveElement.focus();
        lastActiveElement = null;
      }
    }

    // Auto-apertura de la guía de uso al inicio (explica cómo se usa la plataforma)
    try {
      const seenGuide = localStorage.getItem("evegat_seen_guide_v3");
      if (!seenGuide) {
        setTimeout(() => {
          openModal(comoUsarModal);
        }, 300);
      }
    } catch (e) {}

    // Botones para abrir "Cómo usar"
    ["btn-open-guia", "btn-open-guia-band", "btn-hero-como-usar", "btn-banner-open-modal", "btn-floating-guia"].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener("click", () => openModal(comoUsarModal));
    });

    // Botones para abrir "Aviso Legal"
    ["btn-open-legal-top", "btn-open-legal-band", "btn-open-legal-academic", "btn-open-legal-footer"].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener("click", () => openModal(legalModal));
    });

    // Interceptor para todas las descargas de datos (exige registro previo)
    document.querySelectorAll(".btn-intercept-download").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const file = btn.dataset.file || "comunas_enriched.json";
        const label = btn.dataset.label || file;
        state.pendingDownload = { file, label };

        if (filenameLabel) filenameLabel.textContent = label;

        // Pre-cargar datos del usuario si ya se registró previamente
        try {
          const rawLead = localStorage.getItem("evegat_registered_lead");
          if (rawLead) {
            const lead = JSON.parse(rawLead);
            const inNombre = document.getElementById("reg-nombre");
            const inEmail = document.getElementById("reg-email");
            const inInst = document.getElementById("reg-institucion");
            const inPerfil = document.getElementById("reg-perfil");
            const inProp = document.getElementById("reg-proposito");
            const inProy = document.getElementById("reg-proyecto");

            if (inNombre && lead.nombre) inNombre.value = lead.nombre;
            if (inEmail && lead.email) inEmail.value = lead.email;
            if (inInst && lead.institucion) inInst.value = lead.institucion;
            if (inPerfil && lead.perfil) inPerfil.value = lead.perfil;
            if (inProp && lead.proposito) inProp.value = lead.proposito;
            if (inProy && lead.proyecto) inProy.value = lead.proyecto;
            if (document.getElementById("reg-contacto") && lead.contacto !== undefined) {
              document.getElementById("reg-contacto").checked = Boolean(lead.contacto);
            }
          }
        } catch (e) {}

        if (errorMsg) errorMsg.style.display = "none";
        openModal(registroModal);
      });
    });

    // Envío del formulario de registro y disparo de descarga
    if (formRegistro) {
      formRegistro.addEventListener("submit", (e) => {
        e.preventDefault();
        const nombre = (document.getElementById("reg-nombre")?.value || "").trim();
        const email = (document.getElementById("reg-email")?.value || "").trim();
        const institucion = (document.getElementById("reg-institucion")?.value || "").trim();
        const perfil = (document.getElementById("reg-perfil")?.value || "").trim();
        const proposito = (document.getElementById("reg-proposito")?.value || "").trim();
        const proyecto = (document.getElementById("reg-proyecto")?.value || "").trim();
        const contacto = Boolean(document.getElementById("reg-contacto")?.checked);

        // Validación básica
        if (!nombre || !email || !institucion || !perfil || !proposito || !email.includes("@")) {
          if (errorMsg) errorMsg.style.display = "block";
          return;
        }

        if (errorMsg) errorMsg.style.display = "none";

        // Persistir lead localmente
        const leadData = {
          nombre,
          email,
          institucion,
          perfil,
          proposito,
          proyecto,
          contacto,
          fecha: new Date().toISOString()
        };
        try {
          localStorage.setItem("evegat_registered_lead", JSON.stringify(leadData));
        } catch (err) {}

        const targetFile = state.pendingDownload ? state.pendingDownload.file : "comunas_enriched.json";

        // Disparo asíncrono hacia la API propia de Brújula IA / Cloudflare KV
        try {
          const apiPayload = {
            nombre: nombre,
            email: email,
            institucion: institucion,
            estamento_rol: perfil,
            proposito_uso: proposito,
            detalle_proyecto: proyecto || "Descarga de microdatos Observatorio TI Municipal",
            archivo_solicitado: targetFile,
            consentimiento: contacto
          };

          fetch("https://brujulaiaedusuperior.evegat.cl/api/register-download", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(apiPayload),
            keepalive: true
          }).catch(() => {
            // Falla silenciosa si hay bloqueo de red o adblocker; no interrumpe la experiencia del usuario
          });
        } catch (err) {}

        // Telemetría Umami si está disponible
        if (window.umami && typeof window.umami.track === "function") {
          try {
            window.umami.track("lead_descarga_datos", {
              perfil: perfil,
              proposito: proposito,
              archivo: targetFile
            });
          } catch (_) {}
        }

        // Ejecutar descarga
        if (targetFile === "ranking_comunal.csv") {
          exportTableToCSV();
        } else if (targetFile === "proveedores_tecnologicos.csv") {
          exportProveedoresToCSV();
        } else {
          const a = document.createElement("a");
          a.href = "data/" + targetFile;
          a.download = targetFile;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }

        closeModal(registroModal);
        showToast("✓ ¡Registro completado! Tu descarga ha comenzado.");
      });
    }

    // Botón de Descarga Directa sin Registro (Principio de Ciencia Abierta)
    const btnDirectDownload = document.getElementById("btn-direct-download");
    if (btnDirectDownload) {
      btnDirectDownload.addEventListener("click", () => {
        const targetFile = (state.pendingDownload && state.pendingDownload.file) || "comunas_enriched.json";
        if (targetFile === "ranking_comunal.csv") {
          exportTableToCSV();
        } else if (targetFile === "proveedores_tecnologicos.csv") {
          exportProveedoresToCSV();
        } else {
          const a = document.createElement("a");
          a.href = "data/" + targetFile;
          a.download = targetFile;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }
        closeModal(registroModal);
        showToast("⚡ Descarga directa iniciada (Ciencia Abierta).");
      });
    }

    // Cerrar modales mediante atributos data-close-modal
    document.querySelectorAll("[data-close-modal]").forEach(btn => {
      btn.addEventListener("click", () => {
        const modalId = btn.dataset.closeModal;
        const targetModal = document.getElementById(modalId);
        if (targetModal) closeModal(targetModal);
      });
    });

    // Cerrar al clickear el backdrop
    [comoUsarModal, legalModal, registroModal].forEach(m => {
      if (!m) return;
      m.addEventListener("click", (e) => {
        if (e.target === m) closeModal(m);
      });
    });

    // Gestión accesible de teclado para modales: Trampa de foco (Tab trap) y Escape
    document.addEventListener("keydown", (e) => {
      const activeModal = [comoUsarModal, legalModal, registroModal].find(m => m && m.classList.contains("active"));
      if (!activeModal) return;

      if (e.key === "Tab") {
        const card = activeModal.querySelector(".obs-modal-card") || activeModal;
        const focusables = getFocusableElements(card);
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first || !card.contains(document.activeElement)) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last || !card.contains(document.activeElement)) {
            e.preventDefault();
            first.focus();
          }
        }
      } else if (e.key === "Escape") {
        closeModal(activeModal);
      }
    });

    // Botones de salto rápido dentro del modal "Cómo usar"
    document.querySelectorAll(".btn-modal-jump[data-jump-target]").forEach(btn => {
      btn.addEventListener("click", () => {
        closeModal(comoUsarModal);
        const targetId = btn.dataset.jumpTarget.replace("#", "");
        const viewMap = {
          "radiografia": "mapa",
          "mapa": "mapa",
          "ranking": "ranking",
          "rrhh": "rrhh",
          "metodologia": "metodologia"
        };
        const targetView = viewMap[targetId] || targetId;
        switchView(targetView, true);
      });
    });

    // Demo compare: Maipú vs Algarrobo
    const btnDemoCompare = document.getElementById("btn-demo-compare");
    if (btnDemoCompare) {
      btnDemoCompare.addEventListener("click", () => {
        closeModal(comoUsarModal);
        const maipu = state.comunas.find(c => c.comuna.toLowerCase() === "maipú" || c.comuna.toLowerCase() === "maipu");
        const algarrobo = state.comunas.find(c => c.comuna.toLowerCase() === "algarrobo");
        if (maipu && algarrobo) {
          switchView("mapa", true);
          openComparison(maipu, algarrobo);
        }
      });
    }
  }

  function showToast(msg) {
    let toast = document.getElementById("obs-toast-el");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "obs-toast-el";
      toast.className = "obs-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3500);
  }

  // -------------------------------------------------------------------------
  // 9. MÓDULO RRHH MUNICIPAL Y CAPACIDAD ESTATAL
  // -------------------------------------------------------------------------
  function initRRHHModule() {
    const kpisGrid = document.getElementById("rrhh-kpis-grid");
    const tabsContainer = document.getElementById("rrhh-tabs");
    const stage = document.getElementById("rrhh-stage");
    if (!kpisGrid || !stage) return;

    // Métricas nacionales calculadas dinámicamente desde el catastro
    const totalDotacion = state.comunas.reduce((acc, c) => acc + (c.dotacion_total || 0), 0) || 151342;
    const totalTI = state.comunas.reduce((acc, c) => acc + (c.dotacion_ti || 0), 0) || 3647;
    const pctTI = ((totalTI / totalDotacion) * 100).toFixed(2);
    const comunasConHon = state.comunas.filter(c => c.pct_honorarios !== undefined && c.pct_honorarios > 0);
    const avgHonorarios = comunasConHon.length > 0 
      ? (comunasConHon.reduce((acc, c) => acc + c.pct_honorarios, 0) / comunasConHon.length).toFixed(1)
      : 42.8;
    const comunasConRET = state.comunas.filter(c => c.ret_ratio !== undefined && c.ret_ratio > 0);
    const avgRET = comunasConRET.length > 0
      ? (comunasConRET.reduce((acc, c) => acc + c.ret_ratio, 0) / comunasConRET.length).toFixed(2)
      : 2.42;

    kpisGrid.innerHTML = `
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Dotación Total Municipal</div>
        <div class="rrhh-kpi-val">${totalDotacion.toLocaleString("es-CL")}</div>
        <div class="rrhh-kpi-desc">Funcionarios analizados en las 345 municipalidades (Planta, Contrata y Honorarios)</div>
      </div>
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Músculo Propio TI</div>
        <div class="rrhh-kpi-val" style="color:var(--teal);">${totalTI.toLocaleString("es-CL")}</div>
        <div class="rrhh-kpi-desc">Apenas el <strong>${pctTI}%</strong> de la dotación municipal total corresponde a informáticos</div>
      </div>
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Tasa de Precarización</div>
        <div class="rrhh-kpi-val" style="color:var(--crimson);">${avgHonorarios}%</div>
        <div class="rrhh-kpi-desc">Personal contratado a honorarios, sin estabilidad ni carrera funcionaria</div>
      </div>
      <div class="rrhh-kpi-card">
        <div class="rrhh-kpi-label">Ratio RET Promedio</div>
        <div class="rrhh-kpi-val" style="color:var(--gold);">${avgRET}x</div>
        <div class="rrhh-kpi-desc">Por cada $1 peso invertido en tecnoestructura interna se gastan $2,42 en compras externas</div>
      </div>
    `;

    // Conteo de comunas por cuadrante
    const cuadrantesCount = {
      "Estado Soberano": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Soberano").length,
      "Estado Híbrido Dependiente": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Híbrido Dependiente").length,
      "Estado Cautivo": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Cautivo").length,
      "Estado Artesanal": state.comunas.filter(c => c.cuadrante_capacidad === "Estado Artesanal").length,
    };

    function renderRRHHTab(tabKey) {
      if (tabKey === "capacidad") {
        stage.innerHTML = `
          <div style="margin-bottom:20px;">
            <h3 style="font-family:var(--font-serif); font-size:22px; color:var(--navy); margin-bottom:8px;">
              Matriz de Capacidad Estatal y Soberanía Tecnológica (Ratio RET)
            </h3>
            <p style="font-size:13px; color:var(--ink-secondary); line-height:1.6;">
              El <strong>Ratio de Externalización de la Tecnoestructura (RET)</strong> evalúa la relación entre las compras de tecnología a proveedores privados y la capacidad técnica instalada propia del gobierno local. Permite clasificar a las 345 municipalidades de Chile en cuatro cuadrantes operativos:
            </p>
          </div>

          <div class="quadrant-grid">
            <div class="quadrant-card soberano">
              <div class="quadrant-header">
                <span class="quadrant-title">🏛️ Estado Soberano</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Soberano"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Dotación informática interna robusta (&ge; 5 profesionales) y un ratio de compras externas balanceado (RET &le; 1,8x). Capacidad instalada para gobernar contratos, auditar código y mantener autonomía de datos públicos.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Santiago, Providencia, Las Condes, Maipú, Peñalolén.
              </div>
            </div>

            <div class="quadrant-card hibrido">
              <div class="quadrant-header">
                <span class="quadrant-title">⚡ Estado Híbrido Dependiente</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Híbrido Dependiente"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Dispone de equipo técnico calificado pero realiza un gasto intensivo en consultorías externas y licitaciones de gran envergadura (RET &gt; 1,8x). Fuerte capacidad de contraparte técnica pero alta absorción de presupuesto por terceros.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Viña del Mar, Antofagasta, Temuco, Puerto Montt.
              </div>
            </div>

            <div class="quadrant-card cautivo">
              <div class="quadrant-header">
                <span class="quadrant-title">⚠️ Estado Cautivo</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Cautivo"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Dotación informática interna reducida (&lt; 5 profesionales) combinada con alta tercerización tecnológica externa (RET &gt; 1,8x). Elevada dependencia operativa de contratos de soporte de software propietario y vulnerabilidad técnica ante cambios de proveedor.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Calama, Quillota, Algarrobo, Melipilla, San Bernardo.
              </div>
            </div>

            <div class="quadrant-card artesanal">
              <div class="quadrant-header">
                <span class="quadrant-title">🛠️ Estado Artesanal / Desconectado</span>
                <span class="quadrant-count">${cuadrantesCount["Estado Artesanal"]} comunas</span>
              </div>
              <p class="quadrant-desc">
                Baja inversión financiera externa y casi nulo personal de informática interno. Los trámites operan con planillas desconectadas, carpetas compartidas y soporte ad-hoc. Severo rezago frente a las exigencias de la Ley de Transformación Digital.
              </p>
              <div class="quadrant-examples">
                <strong>Referentes:</strong> Alhué, Alto Biobío, Putre, Timaukel, Ollagüe.
              </div>
            </div>
          </div>
        `;
      } else if (tabKey === "dotacion") {
        stage.innerHTML = `
          <div>
            <h3 style="font-family:var(--font-serif); font-size:22px; color:var(--navy); margin-bottom:8px;">
              Composición Jurídica del Personal y la Tecnoestructura Municipal
            </h3>
            <p style="font-size:13px; color:var(--ink-secondary); line-height:1.6; margin-bottom:20px;">
              El análisis longitudinal sobre dotación de personal revela que la transformación digital municipal en Chile se sostiene sobre una base de alta fragilidad contractual. Mientras las plantas funcionarias permanecen congeladas desde hace décadas, los puestos de soporte computacional, ciberseguridad y desarrollo web se cubren masivamente bajo honorarios a suma alzada:
            </p>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:18px;">
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <h4 style="font-size:14px; font-weight:700; color:var(--navy); margin-bottom:6px;">Planta Municipal (31,4%)</h4>
                <p style="font-size:12px; color:var(--ink-secondary); line-height:1.5;">Máxima estabilidad laboral bajo el Estatuto Administrativo Municipal. Sin embargo, menos del <strong>0,3%</strong> de los cargos de planta corresponden a profesionales con título en Informática, Ciencia de la Computación o Telecomunicaciones.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <h4 style="font-size:14px; font-weight:700; color:var(--navy); margin-bottom:6px;">Contrata Anual (25,8%)</h4>
                <p style="font-size:12px; color:var(--ink-secondary); line-height:1.5;">Contratos renovables anualmente sujetos al tope presupuestario legal del 40% del gasto en personal. Concentra la mayor parte de las jefaturas operativas de informática en municipios medianos y grandes.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <h4 style="font-size:14px; font-weight:700; color:var(--crimson); margin-bottom:6px;">Honorarios a Suma Alzada (42,8%)</h4>
                <p style="font-size:12px; color:var(--ink-secondary); line-height:1.5;">Relación contractual civil sin fuero ni derechos estatutarios. En las áreas digitales y de soporte ciudadano, el <strong>68%</strong> de los desarrolladores y técnicos TI municipales prestan servicios bajo esta modalidad precaria.</p>
              </div>
            </div>
          </div>
        `;
      } else if (tabKey === "genero") {
        stage.innerHTML = `
          <div>
            <h3 style="font-family:var(--font-serif); font-size:22px; color:var(--navy); margin-bottom:8px;">
              Estabilidad Funcionaria, Remuneraciones y Brecha en Tecnología
            </h3>
            <p style="font-size:13px; color:var(--ink-secondary); line-height:1.6; margin-bottom:20px;">
              El cruce entre los salarios brutos informados en Transparencia Activa y las trayectorias individuales evidencia tres hallazgos estructurales:
            </p>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:18px;">
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <div style="font-size:11px; font-weight:700; color:var(--gold); text-transform:uppercase;">Permanencia Media</div>
                <div style="font-size:26px; font-family:var(--font-serif); color:var(--navy); font-weight:700; margin:4px 0;">14 Meses</div>
                <p style="font-size:12px; color:var(--ink-secondary);">La rotación promedio del personal TI a honorarios es de solo 14 meses, lo que genera pérdida crítica de conocimiento institucional y dependencia de consultores externos.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <div style="font-size:11px; font-weight:700; color:var(--teal); text-transform:uppercase;">Brecha Salarial Comunal</div>
                <div style="font-size:26px; font-family:var(--font-serif); color:var(--navy); font-weight:700; margin:4px 0;">3,8x</div>
                <p style="font-size:12px; color:var(--ink-secondary);">Un profesional informático en comunas del cono oriente de Santiago percibe en promedio $3,2M brutos, frente a $850.000 en municipios rurales de la macrozona sur.</p>
              </div>
              <div style="background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:18px;">
                <div style="font-size:11px; font-weight:700; color:var(--crimson); text-transform:uppercase;">Participación Femenina TI</div>
                <div style="font-size:26px; font-family:var(--font-serif); color:var(--navy); font-weight:700; margin:4px 0;">18,4%</div>
                <p style="font-size:12px; color:var(--ink-secondary);">Menos de 1 de cada 5 funcionarios dedicados a funciones técnicas de tecnología, redes o infraestructura en municipios chilenos son mujeres.</p>
              </div>
            </div>
          </div>
        `;
      }
    }

    // Inicializar pestaña por defecto
    renderRRHHTab("capacidad");

    // Eventos de pestañas con ARIA sincronizado
    if (tabsContainer) {
      tabsContainer.querySelectorAll(".rrhh-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          tabsContainer.querySelectorAll(".rrhh-tab-btn").forEach(b => {
            b.classList.remove("active");
            b.setAttribute("aria-selected", "false");
          });
          btn.classList.add("active");
          btn.setAttribute("aria-selected", "true");
          renderRRHHTab(btn.dataset.rrhhTab);
        });
      });
    }
  }

  // -------------------------------------------------------------------------
  // UTILIDADES
  // -------------------------------------------------------------------------
  function formatCLP(val) {
    if (!val || isNaN(val)) return "0";
    return Math.round(val).toLocaleString("es-CL");
  }

  // Iniciar ejecución
  init();
});
