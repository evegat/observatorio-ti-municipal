const fs = require('fs');
const appCode = fs.readFileSync('app.js', 'utf8');

// We verify the lines in app.js where apiPayload is constructed
const payloadBlock = appCode.slice(
  appCode.indexOf('const contacto = Boolean(document.getElementById("reg-contacto")?.checked);'),
  appCode.indexOf('fetch("https://brujulaiaedusuperior.evegat.cl/api/register-download"')
);

console.log('Payload extraction block:');
console.log(payloadBlock);

// Check that apiPayload.consentimiento uses 'contacto'
if (!payloadBlock.includes('consentimiento: contacto')) {
  throw new Error('apiPayload.consentimiento does not use contacto variable!');
}

// Test with simulated DOM element
function simulatePayload(checkedState) {
  const document = {
    getElementById: (id) => {
      if (id === 'reg-nombre') return { value: 'Juan Pérez' };
      if (id === 'reg-email') return { value: 'juan@muni.cl' };
      if (id === 'reg-institucion') return { value: 'Municipalidad' };
      if (id === 'reg-perfil') return { value: 'Funcionario' };
      if (id === 'reg-proposito') return { value: 'Investigación' };
      if (id === 'reg-proyecto') return { value: 'Plan TI' };
      if (id === 'reg-contacto') return { checked: checkedState };
      return null;
    }
  };

  const nombre = (document.getElementById("reg-nombre")?.value || "").trim();
  const email = (document.getElementById("reg-email")?.value || "").trim();
  const institucion = (document.getElementById("reg-institucion")?.value || "").trim();
  const perfil = (document.getElementById("reg-perfil")?.value || "").trim();
  const proposito = (document.getElementById("reg-proposito")?.value || "").trim();
  const proyecto = (document.getElementById("reg-proyecto")?.value || "").trim();
  const contacto = Boolean(document.getElementById("reg-contacto")?.checked);

  const targetFile = "comunas_enriched.json";

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

  return apiPayload;
}

const payloadChecked = simulatePayload(true);
console.log('Checked payload consentimiento:', payloadChecked.consentimiento);
if (payloadChecked.consentimiento !== true) throw new Error('Expected true when checked');

const payloadUnchecked = simulatePayload(false);
console.log('Unchecked payload consentimiento:', payloadUnchecked.consentimiento);
if (payloadUnchecked.consentimiento !== false) throw new Error('Expected false when unchecked');

// Also test when element is missing (null/undefined)
const documentMissing = { getElementById: () => null };
const contactoMissing = Boolean(documentMissing.getElementById("reg-contacto")?.checked);
console.log('Missing element fallback:', contactoMissing);
if (contactoMissing !== false) throw new Error('Expected false when element is missing');

console.log('>>> CONSENT PAYLOAD TEST PASSED <<<');
