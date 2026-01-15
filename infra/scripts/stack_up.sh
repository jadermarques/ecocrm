#!/bin/bash
echo "🚀 Subindo a stack ECOCRM..."
sudo docker compose up -d --build
echo "✅ Stack online! Execute 'make logs' para acompanhar."
