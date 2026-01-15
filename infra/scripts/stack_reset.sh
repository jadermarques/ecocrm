#!/bin/bash
echo "⚠️  ATENÇÃO: Isso irá apagar TODOS os containers e volumes (dados) do projeto."
read -p "Tem certeza? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "♻️  Resetando ambiente..."
    sudo docker compose down -v --remove-orphans
    echo "✅ Ambiente limpo. Use ./stack_up.sh para iniciar novamente."
else
    echo "❌ Cancelado."
fi
