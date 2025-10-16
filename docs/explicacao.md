Explicação do Projeto (somente Python no servidor)

Este projeto usa Python (Flask) para renderizar tudo no servidor, sem arquivos JavaScript ou CSS externos. O navegador recebe apenas HTML já pronto.

Estrutura
- `app.py`: servidor Flask e regras de busca/organização do mapa.
- `templates/index.html`: template Jinja2 que gera o HTML do mapa e da lista de resultados.
- `data/inventory.json`: dados com dimensões do mapa e itens (x, y, qty, etc.).

Principais comandos em Python
- `from flask import Flask, jsonify, render_template, request)`: importa Flask e utilitários.
- `app = Flask(__name__, template_folder="templates", static_folder="static")`: cria o app e define pastas.
- `@app.get("/")`: rota da página inicial. Lê `q` de `request.args` para a busca.
- `render_template("index.html", ...)`: envia variáveis para o template.
- Montagem de `cells` (lista 2D): `cells[linha][coluna]` contém uma lista de itens naquela posição `(x, y)`. Facilita o template a mostrar a quantidade total por célula.

Template Jinja (HTML gerado no servidor)
- Recebe `map_cfg` (width/height), `cells` (itens por célula) e `items` (resultados da busca).
- Usa loops `{% for ... %}` para gerar a tabela do mapa e a lista de resultados.
- Links "Ir no mapa" apontam para âncoras `#pos-x-y`, permitindo navegar até a célula correspondente.

Como rodar
1) Criar ambiente e instalar dependências:
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2) Iniciar o servidor:
```
python app.py
```
3) Abrir `http://localhost:5000` no navegador.

Como buscar
- Use o campo de busca e clique em "Buscar". O servidor filtra em Python e recarrega a página com os resultados.

Como adicionar itens
- Edite `data/inventory.json`. Garanta que `x` esteja entre `0..width-1` e `y` entre `0..height-1`.

Se quiser, depois podemos evoluir para uma versão 3D no futuro, mantendo o foco no Python.







