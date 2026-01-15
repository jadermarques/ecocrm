# Regras do Projeto (AI Rules)

Este arquivo define as diretrizes obrigatórias para o projeto ECOCRM.

## 1. Integridade do Chatwoot
- **NÃO alterar o código-fonte do Chatwoot.** O core do Chatwoot deve permanecer intocado para garantir atualizações futuras.
- Toda customização deve ser feita externamente.

## 2. Integrações
- Utilize **API** (REST) para comunicação.
- Utilize **Webhooks** para ouvir eventos.
- Utilize **iFrames** se for necessário embutir telas no painel do Chatwoot.

## 3. Organização do Monorepo
O projeto segue uma estrutura modular na raiz:
- `platform_api/`: Backend principal.
- `streamlit_portal/`: Frontend/Dashboard.
- `bot_runner/`: Workers de automação.
- `shared/`: Código compartilhado.
- `infra/`: Scripts e configurações de deploy.

## 4. Padrões
- Código limpo e modular.
- Logs estruturados.
- Separação clara de responsabilidades.
