#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import os
import logging
from datetime import datetime
from urllib.parse import quote

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

# URL e token para a consulta
BASE_URL = "http://sl.copapel.com.br:9060/consultaSQL"
TOKEN = "ZJBIm0ML8zf9xML5d4fjnRzZGToe538UDAep0q2yfYxSk9OE3togCd5IyjmsdlEh"
QUERY = """SELECT "ItemName" FROM "SBO_COPAPEL_PRD"."OITM" WHERE "validFor" = 'Y' AND "ItemType" = 'I' ORDER BY "ItemCode";"""

# Caminho para o arquivo products.json
PRODUCTS_FILE = "data/products.json"

# Caminho para o diretório vector_db
VECTOR_DB_DIR = "data/vector_db_products"

# Caminho para o arquivo .env
ENV_FILE = "data/.env"

def fetch_products():
    """
    Consulta o endpoint para obter a lista de produtos.
    Retorna a lista de produtos ou None em caso de erro.
    """
    try:
        # Constrói a URL completa
        url = f"{BASE_URL}?token={TOKEN}&query={quote(QUERY)}"
        
        logger.info("Iniciando consulta ao endpoint...")
        logger.info(f"Query SQL sendo executada: {QUERY}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Se recebeu uma resposta de erro do servidor
            if isinstance(data, dict) and "STATUS" in data and data["STATUS"] == "-1":
                logger.error(f"Erro retornado pelo servidor: {data.get('MENSAGEM', 'Sem mensagem de erro')}")
                return None
            
            logger.info(f"Consulta realizada com sucesso. Recebidos {len(data)} produtos.")
            logger.debug(f"Primeiros 5 produtos: {json.dumps(data[:5], ensure_ascii=False, indent=2)}")
            return data
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
    
    try:
        formatted_data = {
            "products": []
        }
        
        # Trata a resposta da API
        if isinstance(products_data, list):
            for item in products_data:
                if isinstance(item, dict):
                    # Se o item já estiver no formato correto
                    if "ItemName" in item:
                        formatted_data["products"].append({"ItemName": item["ItemName"]})
                    # Se o item estiver em outro formato, tenta extrair o nome
                    else:
                        for key, value in item.items():
                            if isinstance(value, str):
                                formatted_data["products"].append({"ItemName": value})
                                break
                elif isinstance(item, str):
                    formatted_data["products"].append({"ItemName": item})
        
        # Verifica se há produtos após a formatação
        if not formatted_data["products"]:
            logger.warning("Nenhum produto encontrado após formatação dos dados")
            return None
            
        logger.info(f"Dados formatados com sucesso. Total de produtos: {len(formatted_data['products'])}")
        return formatted_data
    except Exception as e:
        logger.error(f"Erro ao formatar dados: {str(e)}")
        return None

def save_products(formatted_data):
    """
    Salva os dados formatados no arquivo products.json
    """
    if not formatted_data or not formatted_data.get("products"):
        logger.error("Nenhum dado válido para salvar.")
        return False
    
    try:
        # Cria backup do arquivo atual se existir
        if os.path.exists(PRODUCTS_FILE):
            backup_file = f"products_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Backup criado: {backup_file}")
        
        # Salva o novo arquivo
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Arquivo {PRODUCTS_FILE} atualizado com sucesso. Total de produtos: {len(formatted_data['products'])}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo: {str(e)}")
        return False

def update_products():
    """
    Função principal que coordena a atualização dos produtos
    """
    logger.info("Iniciando atualização de produtos...")
    
    # Busca os produtos
    products_data = fetch_products()
    if not products_data:
        logger.error("Falha ao obter dados dos produtos. Abortando atualização.")
        return False
    
    # Formata os dados
    formatted_data = format_products(products_data)
    if not formatted_data:
        logger.error("Falha ao formatar dados dos produtos. Abortando atualização.")
        return False
    
    # Salva os dados
    success = save_products(formatted_data)
    
    if success:
        logger.info("Atualização de produtos concluída com sucesso.")
        
        # Limpa o banco de vetores se existir
        if os.path.exists(VECTOR_DB_DIR):
            import shutil
            try:
                shutil.rmtree(VECTOR_DB_DIR)
                logger.info(f"Diretório {VECTOR_DB_DIR} removido para recriação do banco de vetores.")
            except Exception as e:
                logger.error(f"Erro ao remover diretório {VECTOR_DB_DIR}: {str(e)}")
    else:
        logger.error("Falha na atualização de produtos.")
    
    return success

if __name__ == "__main__":
    update_products() 