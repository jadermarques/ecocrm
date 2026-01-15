# Deploy no Easypanel (Unified Dockerfile)

Guia atualizado para o uso do Dockerfile unificado na raiz.

## Passo 1: Configuração Comum (Aba Source/Git)

Para **TODOS** os serviços abaixo, use exatamente a mesma configuração na aba **Source (Git)**:

- **Root Directory / Context**: `./` (ou deixe em branco se for o padrão)
- **Build Path**: `/` (apenas a barra, pois o arquivo `Dockerfile` agora está na raiz)

## Passo 2: Configuração Específica (Aba General/Deploy)

Para cada serviço, você deve configurar o **Comando de Inicialização (Command)** na aba 'General' ou 'Deploy' do Easypanel.

### Service 1: `platform_api`
- **Command**: `uvicorn platform_api.main:app --host 0.0.0.0 --port 8000`
- **Port**: 8000
- **Environment**: (Copie de `env/platform_api.env`)

### Service 2: `streamlit_portal`
- **Command**: `streamlit run streamlit_portal/app.py --server.port=8501 --server.address=0.0.0.0`
- **Port**: 8501
- **Environment**: (Copie de `env/streamlit_portal.env`)

### Service 3: `bot_runner`
- **Command**: `python bot_runner/main.py`
- **Environment**: (Copie de `env/bot_runner.env`)

## Passo 3: Limpeza
Se houver arquivos antigos como `Dockerfile.bot_runner`, você pode ignorá-los. O Easypanel usará apenas o `Dockerfile` da raiz.
