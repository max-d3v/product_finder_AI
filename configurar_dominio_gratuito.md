# Configurando um domínio gratuito com HTTPS para sua API

## Passo 1: Obter um domínio gratuito no DuckDNS

1. Acesse [duckdns.org](https://www.duckdns.org)
2. Faça login usando uma conta Google, Twitter, Reddit ou GitHub
3. Escolha um subdomínio (por exemplo: `minha-api.duckdns.org`)
4. Adicione o IP da sua VPS (189.126.105.186)
5. Clique em "update ip"

## Passo 2: Instalar Certbot e obter certificado SSL

```bash
# Instalar Certbot e plugin para DuckDNS
sudo apt update
sudo apt install certbot python3-certbot-dns-duckdns

# Criar arquivo de configuração para o DuckDNS
mkdir -p ~/.secrets/certbot
echo "dns_duckdns_token = SEU_TOKEN_DUCKDNS" > ~/.secrets/certbot/duckdns.ini
chmod 600 ~/.secrets/certbot/duckdns.ini

# Obter certificado SSL
sudo certbot certonly \
  --dns-duckdns \
  --dns-duckdns-credentials ~/.secrets/certbot/duckdns.ini \
  -d seudominio.duckdns.org
```

## Passo 3: Configurar Nginx como proxy reverso com SSL

1. Instale o Nginx:

```bash
sudo apt update
sudo apt install nginx
```

2. Crie um arquivo de configuração:

```bash
sudo nano /etc/nginx/sites-available/fastapi
```

3. Adicione a seguinte configuração (substitua seudominio.duckdns.org pelo seu domínio):

```
server {
    listen 80;
    server_name seudominio.duckdns.org;

    # Redirecionar HTTP para HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name seudominio.duckdns.org;

    # Certificados SSL do Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/seudominio.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seudominio.duckdns.org/privkey.pem;

    # Configurações de segurança recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Proxy para sua API FastAPI
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. Ative a configuração e reinicie o Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Passo 4: Configurar renovação automática do certificado

```bash
# Testar a renovação
sudo certbot renew --dry-run

# A renovação automática já é configurada pelo Certbot
# Você pode verificar em /etc/cron.d/certbot
```

## Passo 5: Atualizar o CORS na sua API FastAPI

Edite seu arquivo app.py para permitir o novo domínio:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://proposta.copapel.com.br",
        "https://seudominio.duckdns.org"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Passo 6: Atualizar seu código frontend

Agora você pode atualizar seu código frontend para usar o novo domínio HTTPS:

```javascript
// Antes
fetch('http://189.126.105.186:8080/products/stream', {...})

// Depois
fetch('https://seudominio.duckdns.org/products/stream', {...})
```

## Solução alternativa: Certificado autoassinado com IP

Se preferir não usar um domínio, você ainda pode configurar HTTPS diretamente com seu IP usando um certificado autoassinado:

```bash
# Gerar certificado autoassinado
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt

# Configurar Nginx (similar ao passo 3, mas usando o IP em vez do domínio)
```

Nota: Com certificados autoassinados, os navegadores mostrarão um aviso de segurança que o usuário precisará aceitar.
