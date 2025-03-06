# Configurando HTTPS para sua API FastAPI na VPS

## Opção 1: Usando Certbot e Let's Encrypt (Recomendado se você tiver um domínio)

Se você decidir usar um domínio no futuro, esta é a melhor opção:

```bash
# Instalar Certbot
sudo apt update
sudo apt install certbot

# Obter certificado (substitua seu-dominio.com pelo seu domínio)
sudo certbot certonly --standalone -d seu-dominio.com

# Os certificados serão salvos em /etc/letsencrypt/live/seu-dominio.com/
```

## Opção 2: Usando certificado autoassinado (Solução temporária)

```bash
# Gerar chave privada e certificado
openssl req -x509 -newkey rsa:4096 -keyout chave.pem -out certificado.pem -days 365 -nodes
```

Coloque os arquivos `chave.pem` e `certificado.pem` no mesmo diretório do seu app.py e descomente a seção SSL no código.

## Opção 3: Usando Nginx como proxy reverso (Recomendado para produção)

Esta é a melhor solução para produção:

1. Instale o Nginx:

```bash
sudo apt update
sudo apt install nginx
```

2. Configure o Nginx como proxy reverso com SSL:

```bash
sudo nano /etc/nginx/sites-available/fastapi
```

3. Adicione a configuração:

```
server {
    listen 443 ssl;
    server_name 189.126.105.186;  # Seu IP ou domínio

    ssl_certificate /caminho/para/certificado.pem;
    ssl_certificate_key /caminho/para/chave.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. Ative o site e reinicie o Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Opção 4: Configurar um proxy CORS (Solução alternativa)

Se você não quiser configurar HTTPS na sua VPS, pode criar um proxy CORS no seu frontend:

1. Crie um arquivo `proxy.js` no seu servidor frontend:

```javascript
// Exemplo usando Express.js
const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
const app = express();

app.use(
  "/api",
  createProxyMiddleware({
    target: "http://189.126.105.186:8080",
    changeOrigin: true,
    pathRewrite: {
      "^/api": "/",
    },
  })
);

app.listen(3000);
```

2. Atualize suas chamadas de API para usar este proxy:

```javascript
fetch("/api/products/stream"); // em vez de http://189.126.105.186:8080/products/stream
```

## Opção 5: Usar um serviço de proxy CORS (Solução rápida)

Você pode usar serviços como CORS Anywhere ou criar seu próprio proxy CORS.

Exemplo de uso:

```javascript
fetch(
  "https://cors-anywhere.herokuapp.com/http://189.126.105.186:8080/products/stream"
);
```

## Recomendação final

Para um ambiente de produção, a melhor opção é a 3 (Nginx como proxy reverso com SSL). É a solução mais robusta e segura.
