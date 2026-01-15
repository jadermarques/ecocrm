# Integração Contínua (CI)

O projeto utiliza **GitHub Actions** para automação de testes básicos e build da Imagem Unificada.

## Workflow `ci.yml`

### Triggers
- **Push na main**: Executa testes e, se passar, faz build e push da imagem unificada para o GHCR.
- **Push de tags (v*)**: Geras tags versionadas (ex: v1.0.0).
- **Pull Request**: Executa apenas testes e build (dry-run) para validar a PR.

### Jobs

1. **smoke-check**:
   - Instala Python 3.12.
   - Roda `python -m compileall .` para garantir zero erros de sintaxe.
   - Executa um teste básico com `pytest`.

2. **build-and-push**:
   - Só roda se o `smoke-check` passar.
   - Constrói a **Imagem Docker Unificada** (usando o `Dockerfile` da raiz).
   - Faz push para o `ghcr.io/seu-usuario/ecocrm`.

## Como habilitar no GitHub

1. Vá em **Settings > Actions > General** e garanta que as Actions estão permitidas.
2. O workflow usa o `GITHUB_TOKEN` padrão para autenticar no GHCR.
3. As imagens estarão disponíveis na aba **Packages** do perfil/organização do GitHub.

### Deploy usando a Imagem (Alternativa ao Build Git)
No Easypanel, você também pode implantar usando a aba **Docker Image** em vez de Git:
- **Image**: `ghcr.io/seu-usuario/ecocrm:main`
- **Username/Password**: Seu usuário e um Personal Access Token (se o pacote for privado).
