# Atualização Automática de Produtos

Este diretório contém scripts para atualizar automaticamente o arquivo `products.json` com dados obtidos de um endpoint SQL.

## Arquivos

- `update_products.py`: Script Python principal que consulta o endpoint e atualiza o arquivo `products.json`.
- `configure_token.py`: Script para configurar o token de autenticação.
- `schedule_update_windows.bat`: Script para agendar a execução diária no Windows.
- `schedule_update_linux.sh`: Script para agendar a execução diária no Linux.
- `run_update_products.bat` ou `run_update_products.sh`: Scripts gerados automaticamente para executar a atualização com o token configurado.

## Requisitos

- Python 3.6 ou superior
- Biblioteca `requests` (instalada automaticamente pelos scripts de agendamento)
- Token de autenticação para o endpoint SQL

## Configuração do Token

Antes de agendar a atualização automática, você precisa configurar o token de autenticação. Há duas maneiras de fazer isso:

### Opção 1: Usando o script de configuração

Execute o script `configure_token.py`:

```bash
python configure_token.py
```

Este script solicitará o token de autenticação e o armazenará de forma segura para uso futuro.

### Opção 2: Configuração manual

Você pode configurar o token manualmente de uma das seguintes formas:

1. Criar um arquivo `.env` no diretório do script com o seguinte conteúdo:

   ```
   WS_TOKEN=seu_token_aqui
   ```

2. Criar um arquivo `token.txt` no diretório do script contendo apenas o token.

3. Definir a variável de ambiente `WS_TOKEN` no seu sistema.

## Agendamento da Atualização

### No Windows

1. Abra o Prompt de Comando como Administrador
2. Navegue até o diretório onde estão os scripts
3. Execute o script de agendamento:
   ```
   schedule_update_windows.bat
   ```
4. O script verificará se o token está configurado. Se não estiver, executará o script de configuração.
5. Em seguida, agendará a tarefa para ser executada diariamente à meia-noite (GMT -03:00).

### No Linux

1. Abra o Terminal
2. Navegue até o diretório onde estão os scripts
3. Torne o script de agendamento executável:
   ```
   chmod +x schedule_update_linux.sh
   ```
4. Execute o script de agendamento:
   ```
   ./schedule_update_linux.sh
   ```
5. O script verificará se o token está configurado. Se não estiver, executará o script de configuração.
6. Em seguida, agendará a tarefa para ser executada diariamente à meia-noite (GMT -03:00) usando cron.

## Execução Manual

Para executar o script manualmente e atualizar o arquivo `products.json` imediatamente:

### No Windows

```
run_update_products.bat
```

### No Linux

```
./run_update_products.sh
```

## Alteração do Token

Para alterar o token de autenticação a qualquer momento, execute:

```bash
python configure_token.py
```

## Logs

O script gera logs detalhados em:

- `update_products.log`: Log principal do script Python
- `update_products_cron.log`: Log da execução agendada via cron (apenas no Linux)

## Funcionamento

1. O script consulta o endpoint SQL especificado com o token de autenticação.
2. Os dados recebidos são formatados no formato esperado pelo arquivo `products.json`.
3. Um backup do arquivo `products.json` atual é criado antes da atualização.
4. O arquivo `products.json` é atualizado com os novos dados.
5. O diretório `vector_db_products` é removido para forçar a recriação do banco de vetores na próxima execução do aplicativo.

## Configuração

Se necessário, você pode editar o arquivo `update_products.py` para modificar:

- URL do endpoint
- Consulta SQL
- Caminho do arquivo de produtos

## Segurança do Token

O token de autenticação é armazenado localmente em um dos seguintes locais:

- Arquivo `.env`
- Arquivo `token.txt`

Certifique-se de proteger adequadamente esses arquivos, limitando o acesso apenas a usuários autorizados.

## Solução de Problemas

### Windows

- Se a tarefa não for agendada corretamente, verifique se você está executando o script como Administrador.
- Você pode verificar o status da tarefa agendada no Agendador de Tarefas do Windows.

### Linux

- Se a tarefa não for agendada corretamente, verifique se o cron está em execução: `systemctl status cron`.
- Verifique se o usuário atual tem permissão para usar o crontab: `crontab -l`.
- Verifique os logs do cron para erros: `grep CRON /var/log/syslog`.
