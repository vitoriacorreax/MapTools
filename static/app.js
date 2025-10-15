async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Erro HTTP ${res.status}`);
  return res.json();
}

function setGridSize(mapEl, width, height) {
  mapEl.style.setProperty('--cols', String(width));
  mapEl.style.setProperty('--rows', String(height));
}

function createCell() {
  const div = document.createElement('div');
  div.className = 'cell';
  return div;
}

function createMarker(item) {
  const marker = document.createElement('div');
  marker.className = 'marker';
  marker.dataset.sku = item.sku;

  // Estilos por nível de estoque
  if (item.qty <= 5) marker.classList.add('critical');
  else if (item.qty <= 20) marker.classList.add('low');

  marker.textContent = item.qty;

  // Tooltip simples
  const tip = document.createElement('div');
  tip.className = 'tooltip';
  tip.textContent = `${item.name} • ${item.category} • SKU ${item.sku}`;
  marker.appendChild(tip);

  return marker;
}

function renderGrid(mapEl, mapCfg, items) {
  const { width, height } = mapCfg;
  setGridSize(mapEl, width, height);
  mapEl.innerHTML = '';

  const grid = [];
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const cell = createCell();
      grid.push(cell);
      mapEl.appendChild(cell);
    }
  }

  for (const item of items) {
    const index = item.y * width + item.x; // origem (0,0) canto superior esquerdo
    if (index < 0 || index >= grid.length) continue;
    const cell = grid[index];
    const marker = createMarker(item);
    cell.appendChild(marker);
  }
}

function renderResults(listEl, items, onFocus) {
  listEl.innerHTML = '';
  for (const item of items) {
    const li = document.createElement('li');
    const block = document.createElement('div');
    const meta = document.createElement('small');
    const btn = document.createElement('button');

    block.innerHTML = `<strong>${item.name}</strong><br/>SKU ${item.sku} • ${item.category}`;
    meta.textContent = `Qtd: ${item.qty} | Posição: (${item.x}, ${item.y})`;
    btn.textContent = 'Localizar no mapa';

    btn.addEventListener('click', () => onFocus(item));

    li.appendChild(block);
    li.appendChild(btn);
    li.appendChild(meta);
    listEl.appendChild(li);
  }
}

function focusItemOnMap(mapEl, item) {
  const selector = `.marker[data-sku="${CSS.escape(item.sku)}"]`;
  const marker = mapEl.querySelector(selector);
  if (!marker) return;

  // Remover seleção anterior
  mapEl.querySelectorAll('.marker.selected').forEach(el => el.classList.remove('selected'));
  marker.classList.add('selected');
  marker.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
}

async function main() {
  const mapEl = document.getElementById('map');
  const resultsEl = document.getElementById('results');
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const clearBtn = document.getElementById('clearBtn');

  const [mapCfg, initialItems] = await Promise.all([
    fetchJSON('/api/map'),
    fetchJSON('/api/items')
  ]);

  renderGrid(mapEl, mapCfg, initialItems);
  renderResults(resultsEl, initialItems, (item) => focusItemOnMap(mapEl, item));

  async function doSearch() {
    const q = searchInput.value.trim();
    const data = await fetchJSON(`/api/search?q=${encodeURIComponent(q)}`);
    renderResults(resultsEl, data, (item) => focusItemOnMap(mapEl, item));
  }

  searchBtn.addEventListener('click', doSearch);
  searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });
  clearBtn.addEventListener('click', async () => {
    searchInput.value = '';
    const data = await fetchJSON('/api/items');
    renderResults(resultsEl, data, (item) => focusItemOnMap(mapEl, item));
  });
}

window.addEventListener('DOMContentLoaded', () => {
  main().catch(err => console.error(err));
});


