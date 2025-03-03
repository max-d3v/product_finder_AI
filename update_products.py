#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import os
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_products.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("update_products")

# Função para carregar o token de autenticação
def load_token():
    # Tenta carregar do arquivo .env
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key == 'WS_TOKEN':
                        return value.strip('"\'')
    
    # Tenta carregar da variável de ambiente
    token = os.getenv("WS_TOKEN")
    if token:
        return token
    
    # Tenta carregar do arquivo de token
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.txt')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    
    return None

# URL e token para a consulta
URL = "http://192.168.1.23:9060/consultaSQL"
TOKEN = load_token()
QUERY = """SELECT "ItemName" FROM "SBO_COPAPEL_PRD"."OITM" WHERE "validFor" = 'Y' AND "ItemType" = 'I' ORDER BY "ItemCode";"""

# Caminho para o arquivo products.json
PRODUCTS_FILE = "products.json"

def fetch_products():
    """
    Consulta o endpoint para obter a lista de produtos.
    Retorna a lista de produtos ou None em caso de erro.
    """
    if not TOKEN:
        logger.error("Token de autenticação não configurado. Configure a variável de ambiente WS_TOKEN, o arquivo .env ou token.txt.")
        return None
        
    try:
        params = {
            "token": TOKEN,
            "query": QUERY
        }
        
        logger.info("Iniciando consulta ao endpoint...")
        response = requests.get(URL, params=params)
        
        if response.status_code == 200:
            logger.info(f"Consulta realizada com sucesso. Recebidos {len(response.json())} produtos.")
            return response.json()
        else:
            logger.error(f"Erro ao consultar endpoint. Status code: {response.status_code}")
            logger.error(f"Resposta: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exceção ao consultar endpoint: {str(e)}")
        return None

def format_products(products_data):
    """
    Formata os dados dos produtos no formato esperado pelo arquivo products.json.
    """
    if not products_data:
        return None
    
    # Verifica se os dados já estão no formato esperado
    if isinstance(products_data, list) and all(isinstance(item, dict) and "ItemName" in item for item in products_data):
        formatted_data = {
            "products": products_data
        }
        return formatted_data
    
    # Se os dados estiverem em outro formato, tenta converter
    try:
        if isinstance(products_data, dict) and "products" in products_data:
            return products_data
        
        logger.warning("Formato de dados inesperado. Tentando converter...")
        formatted_data = {
            "products": []
        }
        
        for item in products_data:
            if isinstance(item, dict) and "ItemName" in item:
                formatted_data["products"].append({"ItemName": item["ItemName"]})
            elif isinstance(item, str):
                formatted_data["products"].append({"ItemName": item})
        
        return formatted_data
    except Exception as e:
        logger.error(f"Erro ao formatar dados: {str(e)}")
        return None

def save_products(formatted_data):

    if not formatted_data:
        logger.error("Nenhum dado para salvar.")
        return False
    
    try:
        if os.path.exists(PRODUCTS_FILE):
            backup_file = f"products_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Backup criado: {backup_file}")
        
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Arquivo {PRODUCTS_FILE} atualizado com sucesso. Total de produtos: {len(formatted_data['products'])}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo: {str(e)}")
        return False

def update_products():

    logger.info("Iniciando atualização de produtos...")
    
    products_data = fetch_products()
    if not products_data:
        logger.error("Falha ao obter dados dos produtos. Abortando atualização.")
        return False
    
    formatted_data = format_products(products_data)
    if not formatted_data:
        logger.error("Falha ao formatar dados dos produtos. Abortando atualização.")
        return False
    
    success = save_products(formatted_data)
    
    if success:
        logger.info("Atualização de produtos concluída com sucesso.")
        
        # Verifica se é necessário recriar o banco de vetores
        vector_db_dir = "vector_db_products"
        if os.path.exists(vector_db_dir):
            import shutil
            try:
                shutil.rmtree(vector_db_dir)
                logger.info(f"Diretório {vector_db_dir} removido para recriação do banco de vetores.")
            except Exception as e:
                logger.error(f"Erro ao remover diretório {vector_db_dir}: {str(e)}")
    else:
        logger.error("Falha na atualização de produtos.")
    
    return success

if __name__ == "__main__":
    update_products() 