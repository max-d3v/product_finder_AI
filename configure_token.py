#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getpass

def save_token_to_env_file(token):
    """Salva o token no arquivo .env"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Verifica se o arquivo já existe
    env_content = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    try:
                        key, value = line.strip().split('=', 1)
                        env_content[key] = value
                    except ValueError:
                        pass
    
    # Adiciona ou atualiza o token
    env_content['WS_TOKEN'] = token
    
    # Escreve o arquivo
    with open(env_file, 'w') as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    print(f"Token salvo com sucesso no arquivo {env_file}")
    return True

def save_token_to_file(token):
    """Salva o token em um arquivo separado"""
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.txt')
    
    with open(token_file, 'w') as f:
        f.write(token)
    
    # Tenta definir permissões restritas no arquivo (apenas no Unix)
    try:
        os.chmod(token_file, 0o600)  # Apenas o proprietário pode ler/escrever
    except:
        pass
    
    print(f"Token salvo com sucesso no arquivo {token_file}")
    return True

def main():
    print("Configuração do Token de Autenticação")
    print("=====================================")
    print("Este script irá configurar o token de autenticação para a atualização automática de produtos.")
    print("O token será armazenado localmente e usado nas atualizações automáticas.")
    print()
    
    # Solicita o token
    token = None
    while not token:
        token = getpass.getpass("Digite o token de autenticação: ").strip()
        if not token:
            print("O token não pode estar vazio. Tente novamente.")
    
    # Salva o token
    save_token_to_env_file(token)
    save_token_to_file(token)
    
    print("\nConfiguração concluída com sucesso!")
    print("O token foi configurado e será usado nas atualizações automáticas.")
    print("Para alterar o token no futuro, execute este script novamente.")

if __name__ == "__main__":
    main() 