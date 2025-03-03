@echo off
echo Agendando tarefa para atualizar products.json diariamente a meia-noite (GMT -03:00)...

REM Obtém o caminho absoluto do diretório atual
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%update_products.py"
set "CONFIG_SCRIPT=%SCRIPT_DIR%configure_token.py"

REM Verifica se o Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Erro: Python não encontrado. Por favor, instale o Python e tente novamente.
    exit /b 1
)

REM Verifica se os scripts Python existem
if not exist "%PYTHON_SCRIPT%" (
    echo Erro: O script update_products.py não foi encontrado em %SCRIPT_DIR%
    exit /b 1
)

if not exist "%CONFIG_SCRIPT%" (
    echo Erro: O script configure_token.py não foi encontrado em %SCRIPT_DIR%
    exit /b 1
)

REM Instala as dependências necessárias
echo Instalando dependências...
pip install requests

REM Verifica se o token já está configurado
set "TOKEN_FILE=%SCRIPT_DIR%token.txt"
set "ENV_FILE=%SCRIPT_DIR%.env"

if not exist "%TOKEN_FILE%" (
    if not exist "%ENV_FILE%" (
        echo Token de autenticação não configurado.
        echo Executando script de configuração...
        python "%CONFIG_SCRIPT%"
        
        if %ERRORLEVEL% NEQ 0 (
            echo Erro ao configurar o token. Por favor, tente novamente.
            exit /b 1
        )
    )
)

REM Cria a tarefa agendada
echo Criando tarefa agendada...
schtasks /create /tn "AtualizarProdutos" /tr "python \"%PYTHON_SCRIPT%\"" /sc DAILY /st 00:00 /ru SYSTEM /f

if %ERRORLEVEL% EQU 0 (
    echo Tarefa agendada com sucesso! O arquivo products.json será atualizado diariamente à meia-noite.
) else (
    echo Erro ao agendar a tarefa. Tente executar este script como administrador.
)

echo.
echo Para executar o script manualmente, use: python "%PYTHON_SCRIPT%"
echo Para alterar o token de autenticação, use: python "%CONFIG_SCRIPT%"
echo.

pause 