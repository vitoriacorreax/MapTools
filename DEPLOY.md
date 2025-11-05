# 🚀 Guia de Deploy para Render

## Pré-requisitos
- Conta no [Render.com](https://render.com)
- Repositório Git (GitHub, GitLab ou Bitbucket)

## Passos para Deploy

### 1. Preparar o Repositório
Certifique-se de que todos os arquivos estão commitados:
```bash
git add .
git commit -m "Preparando para deploy no Render"
git push
```

### 2. Criar Novo Serviço no Render

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte seu repositório Git
4. Configure o serviço:
   - **Name**: `mapa-ferragem` (ou o nome que preferir)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120 app:app`
   - **Plan**: Escolha o plano (Free tier disponível)

### 3. Configurações Adicionais (Opcional)

Se preferir usar o arquivo `render.yaml`, o Render detectará automaticamente.

### 4. Variáveis de Ambiente

Não são necessárias variáveis de ambiente para este projeto, mas você pode adicionar:
- `PYTHON_VERSION=3.9.18` (se necessário)

### 5. Deploy Automático

O Render fará deploy automaticamente sempre que você fizer push para o repositório.

## 📝 Arquivos de Configuração

- ✅ `requirements.txt` - Dependências Python
- ✅ `runtime.txt` - Versão do Python
- ✅ `Procfile` - Comando de inicialização
- ✅ `render.yaml` - Configuração alternativa do Render

## 🔧 Troubleshooting

Se o deploy falhar:
1. Verifique os logs no dashboard do Render
2. Certifique-se de que o `requirements.txt` está correto
3. Verifique se o `app:app` está correto (módulo:variável)

## 📱 Acesso

Após o deploy, você receberá uma URL como:
`https://mapa-ferragem.onrender.com`

**Nota**: No plano gratuito, o serviço pode "adormecer" após 15 minutos de inatividade. A primeira requisição pode demorar alguns segundos para "acordar" o serviço.

