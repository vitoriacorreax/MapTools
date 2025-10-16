# 🏪 PROJETO MAPA DO ESTOQUE - FERRAGEM FÊNIX
## Projeto de Faculdade - Python + Flask

---

## 📋 ÍNDICE
1. [Visão Geral do Projeto](#visão-geral)
2. [Estrutura de Arquivos](#estrutura)
3. [Explicação Detalhada do Código](#explicação-código)
4. [Como Executar](#como-executar)
5. [Funcionalidades](#funcionalidades)
6. [Personalização](#personalização)

---

## 🎯 VISÃO GERAL DO PROJETO {#visão-geral}

Este projeto cria um **mapa virtual do estoque** de uma ferragem usando Python e Flask. Os clientes podem:
- 🔍 Buscar produtos por nome, categoria ou SKU
- 🗺️ Visualizar o mapa do estoque com corredores coloridos
- 📱 Usar no celular ou computador
- 🎯 Clicar em corredores para ver produtos específicos

---

## 📁 ESTRUTURA DE ARQUIVOS {#estrutura}

```
ferragem-mapa/
├── app.py                 # Servidor principal (Flask)
├── requirements.txt       # Dependências Python
├── data/
│   └── inventory.json     # Dados do estoque
├── templates/
│   └── index.html         # Página web
├── static/
│   └── logo.png          # Logo da empresa (opcional)
└── docs/
    └── explicacao.md     # Documentação
```

---

## 🔧 EXPLICAÇÃO DETALHADA DO CÓDIGO {#explicação-código}

### **1. ARQUIVO: app.py (Servidor Principal)**

```python
# ========================================
# IMPORTAÇÕES - O que cada uma faz:
# ========================================

from __future__ import annotations  # Compatibilidade com versões futuras do Python
import json                         # Para ler/escrever arquivos JSON
from pathlib import Path           # Para trabalhar com caminhos de arquivos
from typing import Any, Dict, List # Para tipagem (melhor organização do código)
from flask import Flask, jsonify, render_template, request  # Framework web

# ========================================
# CONFIGURAÇÕES GLOBAIS
# ========================================

BASE_DIR = Path(__file__).parent  # Pasta onde está o app.py
DATA_FILE = BASE_DIR / "data" / "inventory.json"  # Caminho para o arquivo de dados

# ========================================
# FUNÇÃO: load_inventory()
# ========================================
def load_inventory() -> Dict[str, Any]:
    """
    FUNÇÃO QUE CARREGA OS DADOS DO ESTOQUE
    
    O que faz:
    1. Verifica se o arquivo inventory.json existe
    2. Se existir, lê o conteúdo e converte para dicionário Python
    3. Se não existir, cria um estoque padrão
    
    Retorna: Dicionário com dados do mapa e itens
    """
    if not DATA_FILE.exists():  # Se arquivo não existe
        return {"map": {"width": 10, "height": 6}, "items": []}  # Estoque padrão
    
    with DATA_FILE.open("r", encoding="utf-8") as f:  # Abre arquivo para leitura
        return json.load(f)  # Converte JSON para dicionário Python

# ========================================
# FUNÇÃO: create_app()
# ========================================
def create_app() -> Flask:
    """
    FUNÇÃO QUE CRIA E CONFIGURA O APLICATIVO FLASK
    
    O que faz:
    1. Cria o aplicativo Flask
    2. Define onde estão os templates e arquivos estáticos
    3. Cria as rotas (URLs) do site
    4. Retorna o aplicativo configurado
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # ========================================
    # ROTA PRINCIPAL: "/" (Página inicial)
    # ========================================
    @app.get("/")
    def index():
        """
        FUNÇÃO QUE RENDERIZA A PÁGINA PRINCIPAL
        
        O que faz:
        1. Lê parâmetros da URL (busca, categoria, coluna selecionada)
        2. Carrega dados do estoque
        3. Filtra itens conforme busca/categoria
        4. Prepara dados para o template HTML
        5. Retorna página renderizada
        """
        
        # ========================================
        # LENDO PARÂMETROS DA URL
        # ========================================
        query = request.args.get("q", "").strip().lower()  # Texto de busca
        active_category = request.args.get("cat", "").strip()  # Categoria selecionada
        view_mode = request.args.get("view", "map").strip() or "map"  # Modo: mapa ou lista
        
        # Tamanho das células do mapa (zoom)
        try:
            cell_px = max(32, min(128, int(request.args.get("cell", "80"))))
        except ValueError:
            cell_px = 80
            
        # Coluna selecionada (para filtrar por corredor)
        selected_col_raw = request.args.get("col")
        try:
            selected_col = int(selected_col_raw) if selected_col_raw is not None else None
        except ValueError:
            selected_col = None
        
        # ========================================
        # CARREGANDO DADOS DO ESTOQUE
        # ========================================
        inventory = load_inventory()  # Recarrega dados a cada requisição
        map_cfg = inventory.get("map", {"width": 10, "height": 6})  # Dimensões do mapa
        all_items = inventory.get("items", [])  # Lista de todos os itens
        zones = inventory.get("zones", [])  # Corredores coloridos
        aisles = inventory.get("aisles", [])  # Lista de corredores
        
        # ========================================
        # FILTRANDO ITENS
        # ========================================
        def matches(item):
            """
            FUNÇÃO QUE VERIFICA SE UM ITEM CORRESPONDE AOS FILTROS
            
            Verifica:
            1. Se categoria está selecionada
            2. Se texto de busca está no nome/categoria/SKU/descrição
            """
            if active_category and str(item.get("category", "")).strip() != active_category:
                return False
            if not query:
                return True
            haystack = " ".join([
                str(item.get("name", "")),
                str(item.get("category", "")),
                str(item.get("sku", "")),
                str(item.get("description", "")),
            ]).lower()
            return query in haystack
        
        filtered_items = [it for it in all_items if matches(it)]
        
        # Filtro por coluna selecionada
        if selected_col is not None:
            filtered_items = [it for it in filtered_items if int(it.get("x", -1)) == selected_col]
        
        # ========================================
        # DETERMINANDO CORREDOR DE CADA ITEM
        # ========================================
        def infer_aisle(item):
            """
            FUNÇÃO QUE DESCOBRE EM QUAL CORREDOR ESTÁ O ITEM
            
            Lógica:
            1. Se item tem campo "aisle", usa ele
            2. Senão, verifica se posição (x,y) está dentro de alguma zona
            3. Retorna nome do corredor
            """
            if item.get("aisle"):
                return str(item.get("aisle"))
            ix = int(item.get("x", -1))
            iy = int(item.get("y", -1))
            for z in zones:
                zx, zy = int(z.get("x", 0)), int(z.get("y", 0))
                zw, zh = int(z.get("w", 1)), int(z.get("h", 1))
                if zx <= ix < zx + zw and zy <= iy < zy + zh:
                    return str(z.get("label", "Corredor"))
            return "Corredor"
        
        # Adiciona informação do corredor para cada item
        for item in filtered_items:
            item["aisle_display"] = infer_aisle(item)
        
        # ========================================
        # PREPARANDO DADOS PARA O TEMPLATE
        # ========================================
        
        # Lista de categorias únicas
        categories = sorted({str(it.get("category", "")).strip() for it in all_items if it.get("category")})
        
        # Mapa de células (para template antigo)
        width = int(map_cfg.get("width", 10))
        height = int(map_cfg.get("height", 6))
        cells = [[[] for _ in range(width)] for _ in range(height)]
        for item in all_items:
            x = int(item.get("x", -1))
            y = int(item.get("y", -1))
            if 0 <= x < width and 0 <= y < height:
                cells[y][x].append(item)
        
        # ========================================
        # PREPARANDO SVG (MAPA VISUAL)
        # ========================================
        spacing = 8  # Espaço entre células
        margin = 16  # Margem do mapa
        svg_width = margin * 2 + width * cell_px + (width - 1) * spacing
        svg_height = margin * 2 + height * cell_px + (height - 1) * spacing
        
        def cell_to_px(coord):
            """Converte coordenada da grade para pixel no SVG"""
            return margin + coord * (cell_px + spacing)
        
        # Preparando zonas (corredores coloridos)
        svg_zones = []
        for zone in zones:
            zx = int(zone.get("x", 0))
            zy = int(zone.get("y", 0))
            zw = int(zone.get("w", 1))
            zh = int(zone.get("h", 1))
            px_w = zw * cell_px + (zw - 1) * spacing
            px_h = zh * cell_px + (zh - 1) * spacing
            
            svg_zones.append({
                "x": cell_to_px(zx),
                "y": cell_to_px(zy),
                "w": px_w,
                "h": px_h,
                "label": zone.get("label", ""),
                "fill": zone.get("fill", "#cbd5e1"),
                "col": zx,  # Coluna para clique
            })
        
        # Preparando itens (pontos no mapa)
        def qty_color(qty):
            """Define cor baseada na quantidade em estoque"""
            if qty <= 10:
                return "#ef4444"  # Vermelho (crítico)
            if qty <= 30:
                return "#f59e0b"  # Amarelo (baixo)
            return "#22c55e"  # Verde (normal)
        
        svg_items = []
        for item in filtered_items:
            gx = int(item.get("x", 0))
            gy = int(item.get("y", 0))
            cx = cell_to_px(gx) + cell_px // 2
            cy = cell_to_px(gy) + cell_px // 2
            svg_items.append({
                "cx": cx,
                "cy": cy,
                "r": max(8, min(14, cell_px // 3)),
                "qty": int(item.get("qty", 0)),
                "fill": qty_color(int(item.get("qty", 0))),
                "label": item.get("name", ""),
                "gx": gx,
                "gy": gy,
            })
        
        # Logo opcional
        static_logo = BASE_DIR / "static" / "logo.png"
        logo_url = "/static/logo.png" if static_logo.exists() else None
        
        # ========================================
        # RENDERIZANDO TEMPLATE
        # ========================================
        return render_template(
            "index.html",
            query=query,
            map_cfg=map_cfg,
            cells=cells,
            items=filtered_items,
            categories=categories,
            active_category=active_category,
            view_mode=view_mode,
            cell_px=cell_px,
            svg_width=svg_width,
            svg_height=svg_height,
            svg_zones=svg_zones,
            svg_items=svg_items,
            aisles=aisles,
            selected_col=selected_col,
            logo_url=logo_url,
        )
    
    # ========================================
    # ROTAS API (Para uso futuro)
    # ========================================
    @app.get("/api/map")
    def api_map():
        """API que retorna configurações do mapa"""
        inv = load_inventory()
        return jsonify(inv.get("map", {"width": 10, "height": 6}))
    
    @app.get("/api/items")
    def api_items():
        """API que retorna todos os itens"""
        inv = load_inventory()
        return jsonify(inv.get("items", []))
    
    @app.get("/api/search")
    def api_search():
        """API que retorna itens filtrados por busca"""
        inv = load_inventory()
        query = request.args.get("q", "").strip().lower()
        items = inv.get("items", [])
        if not query:
            return jsonify(items)
        
        def matches(item):
            haystack = " ".join([
                str(item.get("name", "")),
                str(item.get("category", "")),
                str(item.get("sku", "")),
                str(item.get("description", "")),
            ]).lower()
            return query in haystack
        
        return jsonify([it for it in items if matches(it)])
    
    return app

# ========================================
# EXECUÇÃO DO SERVIDOR
# ========================================
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
    # host="0.0.0.0" = Acessível de outros dispositivos na rede
    # port=5000 = Porta do servidor
    # debug=True = Modo desenvolvimento (recarrega automaticamente)
```

### **2. ARQUIVO: data/inventory.json (Dados do Estoque)**

```json
{
  "map": { "width": 10, "height": 8 },
  "aisles": ["C1","C2","C3","C4","C5","C6","C7","C8","C9","C10"],
  "zones": [
    { "x": 0, "y": 1, "w": 1, "h": 6, "label": "C1",  "emoji": "", "fill": "#facc15" },
    { "x": 1, "y": 1, "w": 1, "h": 6, "label": "C2",  "emoji": "", "fill": "#d1d5db" },
    { "x": 2, "y": 1, "w": 1, "h": 6, "label": "C3",  "emoji": "", "fill": "#60a5fa" },
    { "x": 3, "y": 1, "w": 1, "h": 6, "label": "C4",  "emoji": "", "fill": "#fb923c" },
    { "x": 4, "y": 1, "w": 1, "h": 6, "label": "C5",  "emoji": "", "fill": "#facc15" },
    { "x": 5, "y": 1, "w": 1, "h": 6, "label": "C6",  "emoji": "", "fill": "#d1d5db" },
    { "x": 6, "y": 1, "w": 1, "h": 6, "label": "C7",  "emoji": "", "fill": "#60a5fa" },
    { "x": 7, "y": 1, "w": 1, "h": 6, "label": "C8",  "emoji": "", "fill": "#fb923c" },
    { "x": 8, "y": 1, "w": 1, "h": 6, "label": "C9",  "emoji": "", "fill": "#facc15" },
    { "x": 9, "y": 1, "w": 1, "h": 6, "label": "C10", "emoji": "", "fill": "#d1d5db" }
  ],
  "items": [
    { "sku": "TEST-01", "name": "Item 1",  "category": "Teste", "description": "Demo", "x": 0, "y": 1, "qty": 10, "aisle": "C1" },
    { "sku": "TEST-02", "name": "Item 2",  "category": "Teste", "description": "Demo", "x": 1, "y": 2, "qty": 12, "aisle": "C2" },
    { "sku": "TEST-03", "name": "Item 3",  "category": "Teste", "description": "Demo", "x": 2, "y": 3, "qty": 14, "aisle": "C3" },
    { "sku": "TEST-04", "name": "Item 4",  "category": "Teste", "description": "Demo", "x": 3, "y": 4, "qty": 8,  "aisle": "C4" },
    { "sku": "TEST-05", "name": "Item 5",  "category": "Teste", "description": "Demo", "x": 4, "y": 5, "qty": 20, "aisle": "C5" },
    { "sku": "TEST-06", "name": "Item 6",  "category": "Teste", "description": "Demo", "x": 5, "y": 1, "qty": 5,  "aisle": "C6" },
    { "sku": "TEST-07", "name": "Item 7",  "category": "Teste", "description": "Demo", "x": 6, "y": 2, "qty": 16, "aisle": "C7" },
    { "sku": "TEST-08", "name": "Item 8",  "category": "Teste", "description": "Demo", "x": 7, "y": 3, "qty": 30, "aisle": "C8" },
    { "sku": "TEST-09", "name": "Item 9",  "category": "Teste", "description": "Demo", "x": 8, "y": 4, "qty": 9,  "aisle": "C9" },
    { "sku": "TEST-10", "name": "Item 10", "category": "Teste", "description": "Demo", "x": 9, "y": 5, "qty": 18, "aisle": "C10" }
  ]
}
```

**EXPLICAÇÃO DO JSON:**
- `map`: Dimensões do mapa (10 colunas x 8 linhas)
- `aisles`: Lista de nomes dos corredores
- `zones`: Corredores coloridos (x, y, w, h, cor)
- `items`: Produtos (sku, nome, categoria, posição, quantidade)

### **3. ARQUIVO: templates/index.html (Página Web)**

```html
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Mapa do Estoque - Ferragem</title>
    <style>
        /* CSS interno para responsividade */
        #layout { display:grid; grid-template-columns: 1fr 360px; gap:16px; padding:16px; }
        .panel { border:1px solid #ddd; border-radius:8px; padding:12px; background:#fff; }
        .result-item { display:grid; grid-template-columns:1fr auto; gap:8px; align-items:center; }
        .chips { padding:12px 16px; display:flex; flex-wrap:wrap; gap:8px; }
        .topbar { padding:16px; border-bottom:1px solid #eab308; display:flex; gap:12px; align-items:center; justify-content:space-between; background:linear-gradient(135deg,#111827,#1f2937); color:#facc15; }
        h2 { margin:4px 0 12px; font-size:18px; }
        body { font-size:16px; line-height:1.35; }
        @media (max-width: 768px) {
            #layout { grid-template-columns: 1fr; padding:8px; gap:12px; }
            .panel { padding:10px; border-radius:10px; }
            .result-item { grid-template-columns: 1fr; }
            .chips { gap:6px; padding:8px; overflow-x:auto; white-space:nowrap; }
            .chips a { display:inline-block; }
            .topbar { flex-direction: column; align-items: stretch; }
            .topbar form { width:100%; display:flex; gap:8px; }
            .topbar form input { width:100%; flex:1; }
            .topbar form input, .topbar form button, .topbar form a { font-size:16px; padding:10px 12px !important; }
            svg { max-height: 360px; }
        }
    </style>
</head>
<body>
    <!-- CABEÇALHO COM LOGO E BUSCA -->
    <div class="topbar">
        <div style="display:flex;align-items:center;gap:12px;">
            {% if logo_url %}
                <img src="{{ logo_url }}" alt="Ferragem Fênix" style="width:44px;height:44px;border-radius:9999px;object-fit:cover;border:2px solid #facc15;background:#111;" />
            {% else %}
                <div style="width:44px;height:44px;border-radius:9999px;background:#facc15;color:#111;display:flex;align-items:center;justify-content:center;font-weight:800;">FF</div>
            {% endif %}
            <div>
                <div style="font-weight:800;letter-spacing:.4px;">Ferragem Fênix</div>
                <div style="font-size:12px;color:#fde68a;">Aberta todos os dias • Sempre aberta ao meio‑dia</div>
            </div>
        </div>
        <form method="get" action="/" style="display:flex;gap:8px;">
            <input name="q" value="{{ query }}" placeholder="Buscar produtos..." style="padding:8px;border-radius:8px;border:1px solid #eab308;color:#111;" />
            <button type="submit" style="padding:8px 12px;border-radius:8px;background:#facc15;color:#111;border:1px solid #eab308;">Buscar</button>
            <a href="/" style="padding:8px 12px;border:1px solid #eab308;border-radius:8px;text-decoration:none;color:#fde68a;">Limpar</a>
        </form>
    </div>

    <!-- CHIPS DE CATEGORIAS -->
    <div id="chips" class="chips">
        <a href="/?q={{ query }}" style="padding:6px 10px;border:1px solid #ddd;border-radius:20px;text-decoration:none;{% if not active_category %}background:#eef;{% endif %}">Todas</a>
        {% for cat in categories %}
        <a href="/?q={{ query }}&cat={{ cat }}&view={{ view_mode }}&cell={{ cell_px }}" style="padding:6px 10px;border:1px solid #ddd;border-radius:20px;text-decoration:none;{% if active_category==cat %}background:#eef;{% endif %}">{{ cat }}</a>
        {% endfor %}
    </div>

    <!-- LAYOUT PRINCIPAL -->
    <div id="layout">
        <!-- MAPA -->
        <section class="panel" id="map-top">
            <div style="margin-bottom:12px;font-weight:700;">Mapa</div>
            <svg viewBox="0 0 {{ svg_width }} {{ svg_height }}" width="100%" xmlns="http://www.w3.org/2000/svg" style="border:1px solid #ddd;border-radius:8px;background:#f8fafc;">
                <defs>
                    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#00000055" />
                    </filter>
                </defs>
                <!-- CORREDORES COLORIDOS (CLICÁVEIS) -->
                {% for z in svg_zones %}
                {% set is_sel = (selected_col is not none and selected_col==z.col) %}
                <a xlink:href="/?q={{ query }}&cat={{ active_category }}&view={{ view_mode }}&cell={{ cell_px }}&col={{ z.col }}">
                    <rect x="{{ z.x }}" y="{{ z.y }}" rx="10" ry="10" width="{{ z.w }}" height="{{ z.h }}" fill="{{ z.fill }}" filter="url(#shadow)" stroke="{% if is_sel %}#0ea5e9{% else %}transparent{% endif %}" stroke-width="{% if is_sel %}4{% else %}0{% endif %}" />
                </a>
                {% endfor %}

                <!-- PONTOS DOS PRODUTOS -->
                {% for it in svg_items %}
                <a id="pos-{{ it.gx }}-{{ it.gy }}" href="#pos-{{ it.gx }}-{{ it.gy }}">
                    <circle cx="{{ it.cx }}" cy="{{ it.cy }}" r="{{ it.r }}" fill="{{ it.fill }}" />
                </a>
                {% endfor %}
            </svg>
        </section>

        <!-- LISTA DE RESULTADOS -->
        <aside class="panel">
            <h2 style="margin:4px 0 12px;">Resultados</h2>
            {% if items|length == 0 %}
                <p>Nenhum item encontrado.</p>
            {% else %}
                <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;">
                    {% for it in items %}
                    <li class="result-item" style="border:1px solid #ddd;border-radius:8px;padding:8px 10px;">
                        <div>
                            <div><strong>{{ it.name }}</strong></div>
                            <div style="font-size:12px;color:#555;">SKU {{ it.sku }} • {{ it.category }}</div>
                            <div style="font-size:12px;color:#555;">Corredor: <strong>{{ it.aisle_display }}</strong></div>
                        </div>
                        <div>
                            <a href="/?q={{ query }}&cat={{ active_category }}&view={{ view_mode }}&cell={{ cell_px }}&col={{ it.x }}#map-top" style="display:inline-block;margin-top:6px;padding:6px 10px;border:1px solid #aaa;border-radius:6px;text-decoration:none;color:inherit;">Ir no mapa</a>
                        </div>
                    </li>
                    {% endfor %}
                </ul>
            {% endif %}
        </aside>
    </div>

    <!-- RODAPÉ -->
    <div style="padding:12px 16px;border-top:1px solid #ddd;color:#666;">
        <small>Exemplo educacional - Universidade</small>
    </div>
</body>
</html>
```

**EXPLICAÇÃO DO HTML:**
- **Jinja2**: Sistema de templates do Flask (`{% %}` e `{{ }}`)
- **Responsivo**: CSS que se adapta ao celular
- **SVG**: Mapa vetorial com corredores e pontos
- **Formulário**: Busca que envia dados via GET

### **4. ARQUIVO: requirements.txt (Dependências)**

```
Flask==3.0.3
```

**EXPLICAÇÃO:**
- `Flask`: Framework web para Python
- `==3.0.3`: Versão específica (evita problemas de compatibilidade)

---

## 🚀 COMO EXECUTAR {#como-executar}

### **1. Instalar Python:**
- Baixe em: https://python.org/downloads
- Marque "Add Python to PATH" durante instalação

### **2. Instalar dependências:**
```bash
pip install -r requirements.txt
```

### **3. Executar o servidor:**
```bash
python app.py
```

### **4. Acessar no navegador:**
- **PC:** http://localhost:5000
- **Celular:** http://SEU_IP:5000

---

## ⚙️ FUNCIONALIDADES {#funcionalidades}

### **🔍 Busca:**
- Por nome do produto
- Por categoria
- Por SKU
- Por descrição

### **🗺️ Mapa Interativo:**
- Corredores coloridos
- Clique para filtrar por corredor
- Pontos coloridos por nível de estoque
- Zoom ajustável

### **📱 Responsivo:**
- Funciona no celular
- Layout adaptativo
- Botões grandes para toque

### **🎨 Personalização:**
- Logo da empresa
- Cores dos corredores
- Tamanho do mapa
- Dados do estoque

---

## 🛠️ PERSONALIZAÇÃO {#personalização}

### **Adicionar Produtos:**
Edite `data/inventory.json`:
```json
{
  "sku": "NOVO-001",
  "name": "Produto Novo",
  "category": "Categoria",
  "description": "Descrição",
  "x": 5,
  "y": 3,
  "qty": 50,
  "aisle": "C6"
}
```

### **Mudar Cores dos Corredores:**
```json
{
  "x": 0, "y": 1, "w": 1, "h": 6,
  "label": "C1",
  "fill": "#facc15"  // Código da cor
}
```

### **Adicionar Logo:**
- Salve como `static/logo.png`
- Aparece automaticamente

### **Hospedar Online:**
- **Railway:** https://railway.app
- **Vercel:** https://vercel.com
- Conecta com GitHub para deploy automático

---

## 📚 CONCEITOS APRENDIDOS

### **Python:**
- **Flask**: Framework web
- **JSON**: Formato de dados
- **Funções**: Organização de código
- **Dicionários**: Estrutura de dados
- **Listas**: Coleções de itens

### **Web:**
- **HTML**: Estrutura da página
- **CSS**: Estilos visuais
- **SVG**: Gráficos vetoriais
- **Responsivo**: Adaptação a telas

### **Desenvolvimento:**
- **Git**: Controle de versão
- **GitHub**: Hospedagem de código
- **Deploy**: Publicação online

---

## 🎓 CONCLUSÃO

Este projeto demonstra:
- ✅ **Programação Python** prática
- ✅ **Desenvolvimento Web** completo
- ✅ **Interface responsiva** para mobile
- ✅ **Sistema de busca** funcional
- ✅ **Mapa interativo** com SVG
- ✅ **Controle de versão** com Git
- ✅ **Deploy** para produção

**Perfeito para apresentar na faculdade e usar em projetos reais!** 🚀
