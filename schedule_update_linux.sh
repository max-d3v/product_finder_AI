#!/bin/bash

echo "Agendando tarefa para atualizar products.json diariamente a meia-noite (GMT -03:00)..."

# Obtém o caminho absoluto do diretório atual
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="${SCRIPT_DIR}/update_products.py"
CONFIG_SCRIPT="${SCRIPT_DIR}/configure_token.py"

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não encontrado. Por favor, instale o Python 3 e tente novamente."
    exit 1
fi

# Verifica se os scripts Python existem
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Erro: O script update_products.py não foi encontrado em $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$CONFIG_SCRIPT" ]; then
    echo "Erro: O script configure_token.py não foi encontrado em $SCRIPT_DIR"
    exit 1
fi

# Torna os scripts Python executáveis
chmod +x "$PYTHON_SCRIPT"
chmod +x "$CONFIG_SCRIPT"

# Instala as dependências necessárias
echo "Instalando dependências..."
pip3 install requests

# Verifica se o token já está configurado
TOKEN_FILE="${SCRIPT_DIR}/token.txt"
ENV_FILE="${SCRIPT_DIR}/.env"

if [ ! -f "$TOKEN_FILE" ] && [ ! -f "$ENV_FILE" ]; then
    echo "Token de autenticação não configurado."
    echo "Executando script de configuração..."
    python3 "$CONFIG_SCRIPT"
    
    if [ $? -ne 0 ]; then
        echo "Erro ao configurar o token. Por favor, tente novamente."
        exit 1
    fi
fi

# Cria a entrada cron para executar à meia-noite (GMT -03:00)
CRON_JOB="0 0 * * * cd $SCRIPT_DIR && python3 $PYTHON_SCRIPT >> $SCRIPT_DIR/update_products_cron.log 2>&1"

# Adiciona a tarefa ao crontab
(crontab -l 2>/dev/null | grep -v "$PYTHON_SCRIPT"; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo "Tarefa agendada com sucesso! O arquivo products.json será atualizado diariamente à meia-noite."
    echo "A saída do script será registrada em $SCRIPT_DIR/update_products_cron.log"
else
    echo "Erro ao agendar a tarefa. Verifique suas permissões."
fi

echo ""
echo "Para executar o script manualmente, use: python3 $PYTHON_SCRIPT"
echo "Para alterar o token de autenticação, use: python3 $CONFIG_SCRIPT"
echo "" 