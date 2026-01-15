.PHONY: up down logs ps reset help

help:
	@echo "Comandos disponíveis:"
	@echo "  make up      - Sobe o ambiente (docker compose up -d --build)"
	@echo "  make down    - Para o ambiente (docker compose down)"
	@echo "  make logs    - Mostra logs de todos os serviços"
	@echo "  make ps      - Mostra status dos containers"
	@echo "  make reset   - CUIDADO: Derruba tudo e APAGA volumes de dados!"

up:
	sudo docker compose up -d --build

down:
	sudo docker compose down

logs:
	sudo docker compose logs -f

ps:
	sudo docker compose ps

reset:
	@echo "⚠️  ATENÇÃO: Você está prestes a apagar TODOS os volumes e dados do banco/redis."
	@echo "Pressione Ctrl+C para cancelar ou Enter para continuar em 5 segundos..."
	@sleep 5
	sudo docker compose down -v --remove-orphans
	@echo "♻️  Ambiente resetado com sucesso."
