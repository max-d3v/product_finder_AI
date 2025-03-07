#!/bin/bash

# Exibe informações de rede
echo "Informações de rede:"
ip addr show
echo "Portas em uso:"
netstat -tulpn

# Inicia o serviço cron
service cron start
echo "Serviço cron iniciado"

# Executa a atualização imediatamente na primeira vez
echo "Iniciando atualização de produtos..."
python /app/update_products.py
echo "Atualização de produtos concluída"

# Inicia a aplicação FastAPI em background
echo "Iniciando servidor FastAPI na porta 1515..."
uvicorn app:app --host 0.0.0.0 --port 1515 &
echo "Servidor FastAPI iniciado"

# Mantém o container rodando e exibe os logs
echo "Container em execução. Exibindo logs..."
tail -f /var/log/cron.log 