#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# Adiciona o diretório atual ao path para importar a função load_token
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from update_products import load_token
except ImportError:
    print("Erro: Não foi possível importar a função load_token do arquivo update_products.py")
    sys.exit(1)

def test_token_config():
    """Testa se o token está configurado corretamente."""
    print("Testando configuração do token...")
    
    # Tenta carregar o token
    token = load_token()
    
    if token:
        print("✅ Token configurado com sucesso!")
        print(f"Token encontrado: {token[:5]}{'*' * (len(token) - 10)}{token[-5:]}")
        
        # Verifica onde o token foi encontrado
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.txt')
        
        if os.environ.get('WS_TOKEN'):
            print("O token foi carregado da variável de ambiente WS_TOKEN.")
        
        if os.path.exists(env_file):
            print(f"Arquivo .env encontrado em: {env_file}")
            with open(env_file, 'r') as f:
                if 'WS_TOKEN' in f.read():
                    print("O token está configurado no arquivo .env.")
        
        if os.path.exists(token_file):
            print(f"Arquivo token.txt encontrado em: {token_file}")
            print("O token está configurado no arquivo token.txt.")
        
        return True
    else:
        print("❌ Token não configurado!")
        print("Por favor, configure o token usando um dos métodos a seguir:")
        print("1. Execute o script configure_token.py")
        print("2. Crie um arquivo .env com WS_TOKEN=seu_token")
        print("3. Crie um arquivo token.txt contendo apenas o token")
        print("4. Configure a variável de ambiente WS_TOKEN")
        return False

if __name__ == "__main__":
    test_token_config() 