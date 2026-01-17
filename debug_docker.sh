#!/bin/bash
echo "=== Containers Rodando ==="
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ecocrm

echo -e "\n=== Logs Recentes da API ==="
sudo docker logs ecocrm-platform_api-1 --tail 50 2>&1

echo -e "\n=== Teste de Rede (Streamlit -> API) ==="
sudo docker exec ecocrm-streamlit_portal-1 ping -c 1 platform_api
