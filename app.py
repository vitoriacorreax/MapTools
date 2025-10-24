from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "inventory.json"


def load_inventory() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return {"map": {"width": 10, "height": 6}, "items": []}
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = 'ferragem_fenix_2024'  # Para mensagens flash

    inventory: Dict[str, Any] = load_inventory()

    @app.get("/")
    def index():
        # Recarrega inventário a cada requisição para refletir mudanças no JSON
        inventory: Dict[str, Any] = load_inventory()
        # Logo opcional em static/logo.png
        static_logo = BASE_DIR / "static" / "logo.png"
        logo_url = "/static/logo.png" if static_logo.exists() else None
        # Parâmetros (sem JS)
        query: str = request.args.get("q", "").strip().lower()
        active_category: str = request.args.get("cat", "").strip()
        view_mode: str = request.args.get("view", "map").strip() or "map"  # "map" ou "list"
        try:
            cell_px = max(32, min(128, int(request.args.get("cell", "80"))))
        except ValueError:
            cell_px = 80
        # Coluna selecionada (para filtrar por coluna ao clicar no mapa)
        selected_col_raw = request.args.get("col")
        try:
            selected_col = int(selected_col_raw) if selected_col_raw is not None else None
        except ValueError:
            selected_col = None

        map_cfg: Dict[str, Any] = inventory.get("map", {"width": 10, "height": 6})
        all_items: List[Dict[str, Any]] = inventory.get("items", [])
        zones: List[Dict[str, Any]] = inventory.get("zones", [])
        aisles: List[str] = inventory.get("aisles", [])

        # Lista de categorias únicas (ordenadas)
        categories = sorted({str(it.get("category", "")).strip() for it in all_items if it.get("category")})

        def matches(item: Dict[str, Any]) -> bool:
            if active_category and str(item.get("category", "")).strip() != active_category:
                return False
            if not query:
                return True
            haystack = " ".join(
                [
                    str(item.get("name", "")),
                    str(item.get("category", "")),
                    str(item.get("sku", "")),
                    str(item.get("description", "")),
                ]
            ).lower()
            return query in haystack

        filtered_items = [it for it in all_items if matches(it)]
        if selected_col is not None:
            filtered_items = [it for it in filtered_items if int(it.get("x", -1)) == selected_col]

        # Descobrir o corredor de um item: usa item["aisle"] se existir;
        # caso contrário, tenta inferir pela zona (se x,y estiverem dentro de uma zona)
        def infer_aisle(it: Dict[str, Any]) -> str:
            if it.get("aisle"):
                return str(it.get("aisle"))
            ix = int(it.get("x", -1))
            iy = int(it.get("y", -1))
            for z in zones:
                zx, zy = int(z.get("x", 0)), int(z.get("y", 0))
                zw, zh = int(z.get("w", 1)), int(z.get("h", 1))
                if zx <= ix < zx + zw and zy <= iy < zy + zh:
                    return str(z.get("label", "Corredor"))
            return "Corredor"

        for it in filtered_items:
            it["aisle_display"] = infer_aisle(it)

        # Mapa de células -> itens (para facilitar o template Jinja)
        width = int(map_cfg.get("width", 10))
        height = int(map_cfg.get("height", 6))
        cells: List[List[List[Dict[str, Any]]]] = [
            [ [] for _ in range(width) ] for _ in range(height)
        ]
        for it in all_items:
            x = int(it.get("x", -1))
            y = int(it.get("y", -1))
            if 0 <= x < width and 0 <= y < height:
                cells[y][x].append(it)

        # Layout SVG (tamanho em pixels e elementos prontos)
        spacing = 8  # espaço entre células
        margin = 16
        svg_width = margin * 2 + width * cell_px + (width - 1) * spacing
        svg_height = margin * 2 + height * cell_px + (height - 1) * spacing

        def cell_to_px(coord: int) -> int:
            return margin + coord * (cell_px + spacing)

        svg_zones: List[Dict[str, Any]] = []
        for z in zones:
            zx = int(z.get("x", 0))
            zy = int(z.get("y", 0))
            zw = int(z.get("w", 1))
            zh = int(z.get("h", 1))
            px_w = zw * cell_px + (zw - 1) * spacing
            px_h = zh * cell_px + (zh - 1) * spacing
            base_fs = max(10, min(18, cell_px // 3 + 6))
            # estimativa de caracteres que cabem na largura do retângulo
            max_chars = max(4, int((px_w - 24) / (base_fs * 0.6)))
            raw_label = str(z.get("label", ""))
            label_display = raw_label if len(raw_label) <= max_chars else raw_label[: max(0, max_chars - 1) ] + "…"
            svg_zones.append(
                {
                    "x": cell_to_px(zx),
                    "y": cell_to_px(zy),
                    "w": px_w,
                    "h": px_h,
                    "label": raw_label,
                    "label_display": label_display,
                    "fs": base_fs,
                    "emoji": z.get("emoji", ""),
                    "fill": z.get("fill", "#cbd5e1"),
                    "col": zx,
                }
            )

        def qty_color(qty: int) -> str:
            if qty <= 10:
                return "#ef4444"  # vermelho
            if qty <= 30:
                return "#f59e0b"  # amarelo
            return "#22c55e"      # verde

        svg_items: List[Dict[str, Any]] = []
        for it in filtered_items:
            gx = int(it.get("x", 0))
            gy = int(it.get("y", 0))
            cx = cell_to_px(gx) + cell_px // 2
            cy = cell_to_px(gy) + cell_px // 2
            svg_items.append(
                {
                    "cx": cx,
                    "cy": cy,
                    "r": max(8, min(14, cell_px // 3)),
                    "qty": int(it.get("qty", 0)),
                    "fill": qty_color(int(it.get("qty", 0))),
                    "label": it.get("name", ""),
                    "gx": gx,
                    "gy": gy,
                }
            )

        # não usamos mais svg_cols; os próprios retângulos das zonas serão clicáveis

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

    @app.get("/api/map")
    def api_map():
        inv = load_inventory()
        return jsonify(inv.get("map", {"width": 10, "height": 6}))

    @app.get("/api/items")
    def api_items():
        inv = load_inventory()
        return jsonify(inv.get("items", []))

    @app.get("/api/search")
    def api_search():
        inv = load_inventory()
        query: str = request.args.get("q", "").strip().lower()
        items: List[Dict[str, Any]] = inv.get("items", [])
        if not query:
            return jsonify(items)

        def matches(item: Dict[str, Any]) -> bool:
            haystack = " ".join(
                [
                    str(item.get("name", "")),
                    str(item.get("category", "")),
                    str(item.get("sku", "")),
                    str(item.get("description", "")),
                ]
            ).lower()
            return query in haystack

        return jsonify([it for it in items if matches(it)])

@app.route("/upload-logo", methods=["GET", "POST"])
def upload_logo():
    """Página para upload do logo"""
    if request.method == "POST":
        if 'logo' not in request.files:
            flash('Nenhum arquivo selecionado!', 'error')
            return redirect(url_for('upload_logo'))
        
        file = request.files['logo']
        if file.filename == '':
            flash('Nenhum arquivo selecionado!', 'error')
            return redirect(url_for('upload_logo'))
        
        if file:
            # Verificar se é imagem
            if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                # Salvar como logo.png
                filename = 'logo.png'
                filepath = BASE_DIR / "static" / filename
                file.save(str(filepath))
                flash('Logo atualizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Formato não suportado! Use PNG, JPG, GIF ou SVG.', 'error')
                return redirect(url_for('upload_logo'))
    
    # Verificar se existe logo
    logo_path = BASE_DIR / "static" / "logo.png"
    logo_url = f"/static/logo.png" if logo_path.exists() else None
    
    return render_template("upload_logo.html", logo_url=logo_url)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """Página de administração do mapa"""
    if request.method == "POST":
        # Salvar mudanças no mapa
        try:
            new_data = request.get_json()
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            return jsonify({"success": True, "message": "Mapa atualizado com sucesso!"})
        except Exception as e:
            return jsonify({"success": False, "message": f"Erro ao salvar: {str(e)}"}), 500
    
    # Carregar dados atuais
    data = load_inventory()
    logo_path = BASE_DIR / "static" / "logo.png"
    logo_url = f"/static/logo.png" if logo_path.exists() else None
    
    return render_template("admin.html", data=data, logo_url=logo_url)
    
    return app


if __name__ == "__main__":
    print("Iniciando servidor...")
    print("Pasta atual:", BASE_DIR)
    print("Arquivo de dados:", DATA_FILE)

    app = create_app()

    print("Servidor configurado!")
    print("Acesse: http://localhost:8080")
    print("Celular: http://192.168.26.92:8080")
    print("Para parar: Ctrl+C")
    print("-" * 50)
    
    try:
        app.run(host="0.0.0.0", port=8080, debug=True)
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        print("Tentando porta alternativa...")
        app.run(host="0.0.0.0", port=8081, debug=True)


