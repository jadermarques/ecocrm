# Troubleshooting

Guia de resolução de problemas comuns no ambiente de desenvolvimento do ECOCRM.

## Comandos de Emergência

### 🚨 Reset Completo (CUIDADO: Apaga dados)
Se o banco de dados estiver corrompido ou você precisar limpar tudo (incluindo volumes):

```bash
# Apaga containers, redes e volumes
docker compose down -v --remove-orphans
# Sobe tudo novamente com rebuild
docker compose up -d --build
```

### Remover volume específico
Para resetar apenas o Redis ou Postgres sem afetar o outro:

```bash
# Listar volumes
docker volume ls

# Remover (o container deve estar parado)
docker volume rm ecocrm_postgres_data
docker volume rm ecocrm_redis_data
```

## Problemas Comuns

### Inspecionar Volumes
Para ver onde os arquivos estão realmente sendo salvos no host:

```bash
docker volume inspect ecocrm_postgres_data
```

### Permission Denied em `./var`
Como usamos bind mounts em desenvolvimento, pode haver problemas de permissão se os arquivos forem criados pelo root dentro do container.

**Solução:**
```bash
sudo chown -R $USER:$USER var/
```

### Portas em uso (Address already in use)
Se você não consegue subir o stack porque a porta 5432, 6379 ou 8000 está ocupada:

**Verifique quem está usando a porta:**
```bash
sudo lsof -i :8000
```
**Mate o processo (se for seguro):**
```bash
kill -9 <PID>
```

### Rebuild Forçado
Às vezes o Docker cacheia uma versão antiga do código ou das dependências (pip install). Para forçar a atualização:

```bash
docker compose up -d --build --force-recreate
```
