# ECOCRM

Monorepo para o ecossistema CRM integrado ao Chatwoot.

## Estrutura do Projeto

```text
ECOCRM/
├── platform_api/       # API Principal (FastAPI)
├── streamlit_portal/   # Portal Administrativo (Streamlit)
├── bot_runner/         # Workers da automação
├── shared/             # Bibliotecas compartilhadas
├── infra/              # Infraestrutura e scripts
├── docs/               # Documentação
├── ai_rules.md         # Regras do projeto
└── README.md           # Este arquivo
```

## Entrypoints

### Platform API
- Diretório: `platform_api/`
- Execução: `uvicorn main:app --reload` (Verificar arquivo main.py)

### Streamlit Portal
- Diretório: `streamlit_portal/`
- Execução: `streamlit run app.py`

### Bot Runner
- Diretório: `bot_runner/`
- Execução: `python main.py`

## Infraestrutura
Scripts de suporte estão em `infra/`.
Execute `make help` (se disponível) ou cheque `docs/` para mais detalhes.
