from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from typing import List, AsyncGenerator
import asyncio
from product_rag import get_similar_products, initialize_db, recreate_db
import time
import json
import google.generativeai as genai

app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://proposta.copapel.com.br",
        "https://avprojects.duckdns.org:8443"  # Note a adição da porta
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Nota: Para resolver o problema de Mixed Content, você precisa:
# 1. Configurar HTTPS na sua API usando certificados SSL
# 2. Ou usar um proxy reverso como Nginx com SSL
# ... existing code ...

class FoundObject(BaseModel):
    ItemName: str = Field(description="Name of the item found")
    Similarity: float = Field(description="Similarity of the item found")
    
class FoundObjects(BaseModel):
    TargetProduct: str = Field(description="Target product to compare with")
    found_objects: list[FoundObject] = Field(description="List of found objects of high similarity")

pydantic_parser = PydanticOutputParser(pydantic_object=FoundObjects)

def load_env():
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada. Configure a variável de ambiente.")
    
    genai.configure(api_key=google_api_key)

def get_model():
    google_llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        temperature=0.2,
    )
    return google_llm

def get_prompt():
    format_instructions = pydantic_parser.get_format_instructions()

    instructions = """
    Dada uma lista de produtos e um produto alvo, encontre o produto mais similar.
    IMPORTANTE: considerando os aspectos mais relevantes para um cliente querendo achar o produto similar.
    Se houver mais de um produto igualmente relevante e de alta qualidade, retorne NO MÁXIMO OS 3 MELHORES.
    Se nenhum produto for suficientemente relevante, retorne None.

    {format_instructions}

    Items:
    {query}
    """

    prompt = PromptTemplate(
        template=instructions,
        input_variables=["query"],
        partial_variables = {
            "format_instructions": format_instructions
        }
    )

    return prompt

# Inicialização da aplicação
load_env()
llm = get_model()
prompt = get_prompt()
chain = prompt | llm | pydantic_parser

# Inicializa o banco de dados vetorial
print("Inicializando banco de dados vetorial...")
try:
    # Verifica se estamos em ambiente Docker
    is_docker = os.path.exists('/.dockerenv')
    
    # Se estiver em ambiente Docker, força a recriação do banco de dados
    # para evitar problemas de incompatibilidade
    if is_docker:
        print("Ambiente Docker detectado. Forçando recriação do banco de dados...")
        recreate_db()
    else:
        initialize_db()
    print("Banco de dados vetorial inicializado com sucesso!")
except Exception as e:
    print(f"Erro ao inicializar banco de dados: {str(e)}")
    print("Tentando recriar o banco de dados...")
    try:
        recreate_db()
        print("Banco de dados recriado com sucesso!")
    except Exception as e2:
        print(f"Falha ao recriar banco de dados: {str(e2)}")
        raise e2

query_template = """
    <product-list>
    {product_list}
    </product-list>

    <target-product>
    {target_product}
    </target-product>
    """

def get_products(target_product: str):
    print("Initiating similar product search...")
    start_time = time.time()
    product_list = get_similar_products(target_product)
    end_time = time.time()
    print(f"Product list obtained in {end_time - start_time} seconds.")

    query = query_template.format(product_list=product_list, target_product=target_product)
    print("Initiating llm reasoning")
    start_time_2 = time.time()
    result = chain.invoke({"query": query})
    end_time_2 = time.time()
    print(f"LLM reasoning completed in {end_time_2 - start_time_2} seconds.")
    return result

async def get_products_streaming(target_product: str) -> AsyncGenerator[str, None]:
    print("Iniciando busca de produtos similares (streaming)...")
    
    yield json.dumps({"status": "iniciando", "message": "Iniciando busca de produtos similares..."}) + "\n"
    await asyncio.sleep(0.1)
    
    start_time = time.time()
    product_list = get_similar_products(target_product)
    end_time = time.time()
    search_time = end_time - start_time
    
    yield json.dumps({
        "status": "produtos_encontrados", 
        "message": f"Produtos similares encontrados em {search_time:.2f} segundos",
        "count": len(product_list)
    }) + "\n"
    await asyncio.sleep(0.1)
    
    query = query_template.format(product_list=product_list, target_product=target_product)
    
    yield json.dumps({"status": "iniciando_llm", "message": "Iniciando análise de similaridade..."}) + "\n"
    await asyncio.sleep(0.1)
    
    start_time_2 = time.time()
    result = chain.invoke({"query": query})
    end_time_2 = time.time()
    llm_time = end_time_2 - start_time_2
    
    yield json.dumps({
        "status": "concluido",
        "message": f"Análise concluída em {llm_time:.2f} segundos",
        "result": result.dict()
    }) + "\n"

async def process_products_streaming(target_products: List[str]) -> AsyncGenerator[str, None]:
    yield json.dumps({
        "status": "iniciando", 
        "message": f"Iniciando processamento de {len(target_products)} produtos"
    }) + "\n"
    await asyncio.sleep(0.1)
    
    for i, target_product in enumerate(target_products):
        if target_product is None or target_product == "":
            yield json.dumps({
                "status": "erro",
                "produto_idx": i,
                "produto": target_product,
                "message": "Produto não especificado"
            }) + "\n"
            await asyncio.sleep(0.1)
            continue
        
        try:
            yield json.dumps({
                "status": "processando_produto",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Iniciando processamento do produto {i+1}/{len(target_products)}: {target_product}"
            }) + "\n"
            await asyncio.sleep(0.1)
            
            start_time = time.time()
            product_list = get_similar_products(target_product)
            end_time = time.time()
            search_time = end_time - start_time
            
            yield json.dumps({
                "status": "produtos_encontrados",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Produtos similares encontrados em {search_time:.2f} segundos",
                "count": len(product_list)
            }) + "\n"
            await asyncio.sleep(0.1)
            
            query = query_template.format(product_list=product_list, target_product=target_product)
            
            yield json.dumps({
                "status": "iniciando_llm",
                "produto_idx": i,
                "produto": target_product,
                "message": "Iniciando análise de similaridade..."
            }) + "\n"
            await asyncio.sleep(0.1)
            
            start_time_2 = time.time()
            result = chain.invoke({"query": query})
            end_time_2 = time.time()
            llm_time = end_time_2 - start_time_2
            
            yield json.dumps({
                "status": "produto_concluido",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Análise concluída em {llm_time:.2f} segundos",
                "result": result.dict()
            }) + "\n"
            await asyncio.sleep(0.1)
            
        except Exception as e:
            yield json.dumps({
                "status": "erro",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Erro ao processar produto: {str(e)}"
            }) + "\n"
            await asyncio.sleep(0.1)
    
    yield json.dumps({
        "status": "todos_concluidos",
        "message": f"Processamento de todos os {len(target_products)} produtos concluído"
    }) + "\n"

@app.get("/product/{target_product}")
def get_product(target_product: str):
    if (target_product is None or target_product == ""):
        return {"error": "No target product provided."}
    result = get_products(target_product)
    return result

@app.get("/product/stream/{target_product}")
async def get_product_streaming(target_product: str):
    if target_product is None or target_product == "":
        return {"error": "No target product provided."}
    
    return StreamingResponse(
        get_products_streaming(target_product),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/products")
def get_products_post(target_products: List[str]):
    results = []
    for target_product in target_products:
        if target_product is None or target_product == "":
            results.append({"error": "No target product provided."})
            continue
        try:
            result = get_product(target_product)
            print(type(result))
        except Exception as e:
            result = {"error": str(e)}
        results.append(result)
    return results

@app.post("/products/stream")
async def get_products_post_streaming(request: Request):
    data = await request.json()
    
    if isinstance(data, list):
        target_products = data
    else:
        target_products = data.get("target_products", [])
    
    if not target_products:
        return {"error": "No target products provided."}
    
    return StreamingResponse(
        process_products_streaming(target_products),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}

@app.post("/admin/recreate-db")
def admin_recreate_db():
    try:
        recreate_db()
        return {"status": "success", "message": "Banco de dados recriado com sucesso"}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao recriar banco de dados: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    
    # Para desenvolvimento local sem SSL:
    uvicorn.run(
        app, 
        host="0.0.0.0",
        port=8080,  # Certifique-se que esta porta corresponde à que você está usando na VPS
        timeout_keep_alive=120,
        log_level="info"
    )
    
    # Para produção com SSL (descomente e configure):
    # import ssl
    # ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # ssl_context.load_cert_chain('certificado.pem', keyfile='chave.pem')
    # uvicorn.run(
    #     app, 
    #     host="0.0.0.0",
    #     port=8080,
    #     ssl=ssl_context,
    #     timeout_keep_alive=120,
    #     log_level="info"
    # )