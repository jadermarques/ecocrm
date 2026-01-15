# Integração Contínua (CI)

O projeto utiliza **GitHub Actions** para automação de testes básicos e build de imagens Docker.

## Workflow `ci.yml`

### Triggers
- **Push na main**: Executa testes e, se passar, faz build e push das imagens para o GHCR (GitHub Container Registry).
- **Push de tags (v*)**: Gera imagens com a tag correspondente (ex: v1.0.0).
- **Pull Request**: Executa apenas testes e build (sem push) para validar a PR.

### Jobs

1. **smoke-check**:
   - Instala Python 3.12.
   - Roda `python -m compileall` nas pastas do projeto para garantir que não há erros de sintaxe (syntax errors) no código.

2. **build-and-push**:
   - Só roda se o `smoke-check` passar.
   - Constrói as imagens Docker para:
     - `services/platform_api`
     - `apps/streamlit_portal`
     - `workers/bot_runner`
   - Faz push para o `ghcr.io` (apenas em push na main ou tags).

## Como habilitar no GitHub

1. Vá em **Settings > Actions > General** e garanta que as Actions estão permitidas.
2. O workflow usa o `GITHUB_TOKEN` padrão para autenticar no GHCR, então certifique-se que o workflow tem permissão de escrita em pacotes (normalmente padrão ou configurável em Settings > Actions).
3. As imagens estarão disponíveis na aba **Packages** do perfil/organização do GitHub.
