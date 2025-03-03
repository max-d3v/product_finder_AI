#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import shutil
from datetime import datetime

# Verifica se o arquivo products.json existe
if not os.path.exists('products.json'):
    print("Arquivo products.json não encontrado. Criando um arquivo de exemplo...")
    
    # Cria um arquivo de exemplo
    example_data = {
        "products": [
            {"ItemName": "Produto de Teste 1"},
            {"ItemName": "Produto de Teste 2"},
            {"ItemName": "Produto de Teste 3"}
        ]
    }
    
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(example_data, f, ensure_ascii=False, indent=2)
    
    print("Arquivo products.json de exemplo criado com sucesso.")

# Faz backup do arquivo atual
backup_file = f"products_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
shutil.copy('products.json', backup_file)
print(f"Backup criado: {backup_file}")

# Simula novos dados do endpoint
new_data = {
    "products": [
        {"ItemName": "Adesivo Higindoor 203 p/ produto diluído 10cm x 08cm"},
        {"ItemName": "Adesivo Higindoor 207 p/ diluidor 04cm x 04cm"},
        {"ItemName": "Adesivo Higindoor 207 p/ produto concentrado 10cm x 08cm"},
        {"ItemName": "Adesivo Higindoor 207 p/ produto diluído 10cm x 08cm"},
        {"ItemName": "Adesivo Higindoor 213 p/ produto concentrado 10cm x 08cm"},
        {"ItemName": "Adesivo Higindoor 213 p/ produto diluído 10cm x 08cm"},
        {"ItemName": "Produto Novo 1 - Teste de Atualização"},
        {"ItemName": "Produto Novo 2 - Teste de Atualização"}
    ]
}

# Atualiza o arquivo products.json
with open('products.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print(f"Arquivo products.json atualizado com sucesso. Total de produtos: {len(new_data['products'])}")

# Verifica se é necessário recriar o banco de vetores
vector_db_dir = "vector_db_products"
if os.path.exists(vector_db_dir):
    try:
        shutil.rmtree(vector_db_dir)
        print(f"Diretório {vector_db_dir} removido para recriação do banco de vetores.")
    except Exception as e:
        print(f"Erro ao remover diretório {vector_db_dir}: {str(e)}")

print("\nTeste de atualização concluído com sucesso!")
print("Na próxima execução do aplicativo, o banco de vetores será recriado com os novos dados.")
print("Para reverter para a versão anterior, renomeie o arquivo de backup para products.json.") 