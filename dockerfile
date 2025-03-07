FROM python:3.11-slim

# Instala as dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    cron \
    python3-dev \
    sqlite3 \
    net-tools \
    iproute2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Adiciona host.docker.internal ao /etc/hosts no Windows/macOS
RUN mkdir -p /etc/docker && \
    echo '#!/bin/sh\n\
    if [ -n "$DOCKER_INTERNAL_HOST" ]; then\n\
        echo "$DOCKER_INTERNAL_HOST host.docker.internal" >> /etc/hosts\n\
    fi\n\
    exec "$@"' > /etc/docker/entrypoint.sh && \
    chmod +x /etc/docker/entrypoint.sh

# Define o diretório de trabalho
WORKDIR /app

# Cria diretório de dados
RUN mkdir -p /app/data

# Copia todos os arquivos necessários
COPY . /app/

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Configura o cron job
RUN echo "0 0 * * * /usr/local/bin/python /app/update_products.py >> /var/log/cron.log 2>&1" > /etc/cron.d/update_products
RUN chmod 0644 /etc/cron.d/update_products
RUN crontab /etc/cron.d/update_products

# Cria o arquivo de log
RUN touch /var/log/cron.log

# Dá permissão de execução ao script de inicialização
RUN chmod +x entrypoint.sh

# Expõe a porta da API
EXPOSE 1515

# Define o entrypoint para configurar o host.docker.internal
ENTRYPOINT ["/etc/docker/entrypoint.sh"]

# Executa o script de inicialização da aplicação
CMD ["python", "app.py"]