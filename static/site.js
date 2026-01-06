async function tnZipLookup(zip) {
  const res = await fetch(`/api/zip/${encodeURIComponent(zip)}`);
  if (!res.ok) {
    return null;
  }
  return await res.json();
}

function tnBindZipAutofill() {
  const zipEl = document.getElementById('zipInput');
  const cityEl = document.getElementById('cityInput');
  const stateEl = document.getElementById('stateInput');
  if (!zipEl || !cityEl || !stateEl) {
    return;
  }

  let last = '';
  zipEl.addEventListener('input', async () => {
    const zip = (zipEl.value || '').replace(/\D/g, '').slice(0, 5);
    zipEl.value = zip;

    if (zip.length !== 5 || zip === last) {
      return;
    }
    last = zip;

    const data = await tnZipLookup(zip);
    if (!data || !Array.isArray(data.results)) {
      return;
    }

    if (data.results.length >= 1) {
      stateEl.value = data.results[0].state || '';
    }

    const cities = [...new Set(data.results.map(r => r.city).filter(Boolean))];
    if (cities.length === 1) {
      cityEl.value = cities[0];
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  tnBindZipAutofill();
});
