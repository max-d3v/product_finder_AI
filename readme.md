# Sistema de Busca de Produtos Similares com Streaming

Este sistema permite buscar produtos similares a um produto alvo, utilizando técnicas de RAG (Retrieval Augmented Generation) e LLMs. A implementação inclui suporte para streaming de resultados, permitindo que o cliente receba atualizações em tempo real sobre o progresso da busca.

## Características

- Busca de produtos similares usando embeddings e LLMs
- Streaming de resultados em tempo real
- Suporte para busca de um único produto ou múltiplos produtos
- Interface de cliente HTML para demonstração
- API RESTful com FastAPI

## Requisitos

- Python 3.8+
- FastAPI
- LangChain
- OpenAI API Key
- Google Gemini API Key (opcional)

## Instalação

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione suas chaves de API:
     ```
     OPENAI_API_KEY_NEW=sua_chave_openai
     GOOGLE_API_KEY=sua_chave_google
     ```

## Executando o servidor

```bash
python app.py
```

O servidor será iniciado em `http://127.0.0.1:1313`.

## Endpoints da API

### Endpoints Síncronos (sem streaming)

- `GET /product/{target_product}` - Busca produtos similares a um produto alvo
- `POST /products` - Busca produtos similares para múltiplos produtos alvo

### Endpoints com Streaming

- `GET /product/stream/{target_product}` - Busca produtos similares a um produto alvo com streaming de resultados
- `POST /products/stream` - Busca produtos similares para múltiplos produtos alvo com streaming de resultados

## Cliente de Demonstração

Um cliente HTML de demonstração está disponível em `client_example.html`. Para usá-lo:

1. Inicie o servidor conforme descrito acima
2. Abra o arquivo `client_example.html` em um navegador
3. Digite o nome do produto que deseja buscar
4. Clique em "Buscar"

O cliente mostrará o progresso da busca em tempo real e exibirá os resultados à medida que forem encontrados.

## Formato dos Dados de Streaming

Os endpoints de streaming retornam dados no formato NDJSON (Newline Delimited JSON). Cada linha é um objeto JSON válido seguido por uma quebra de linha. Os objetos têm os seguintes campos:

- `status`: Estado atual do processamento (iniciando, produtos_encontrados, iniciando_llm, concluido, etc.)
- `message`: Mensagem descritiva sobre o estado atual
- `result`: Resultado final (apenas quando status é "concluido" ou "produto_concluido")
- Outros campos específicos dependendo do status

## Exemplo de Uso com cURL

### Busca de produto único com streaming:

```bash
curl -N "http://127.0.0.1:1313/product/stream/Caneta%20Azul"
```

### Busca de múltiplos produtos com streaming:

```bash
curl -N -X POST "http://127.0.0.1:1313/products/stream" \
  -H "Content-Type: application/json" \
  -d '{"target_products": ["Caneta Azul", "Lápis Preto"]}'
```

## Implementação do Streaming no Cliente

Para implementar o streaming no seu próprio cliente, você pode seguir o exemplo em JavaScript:

```javascript
async function fetchWithStreaming(url, options = {}) {
  const response = await fetch(url, options);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop(); // Manter a última linha incompleta no buffer

    for (const line of lines) {
      if (line.trim()) {
        const data = JSON.parse(line);
        // Processar os dados aqui
        console.log(data);
      }
    }
  }
}
```
