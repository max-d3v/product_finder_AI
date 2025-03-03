from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from typing import List, AsyncGenerator
import asyncio
from product_rag import get_similar_products
#from test_optimized import get_similar_products_test
import time
import json

app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

class FoundObject(BaseModel):
    ItemName: str = Field(description="Name of the item found")
    Similarity: float = Field(description="Similarity of the item found")
    
class FoundObjects(BaseModel):
    TargetProduct: str = Field(description="Target product to compare with")
    found_objects: list[FoundObject] = Field(description="List of found objects of high similarity")

pydantic_parser = PydanticOutputParser(pydantic_object=FoundObjects)


def load_env():
    load_dotenv()
    googleKey=os.getenv("GOOGLE_API_KEY")
    key = os.getenv("OPENAI_API_KEY_NEW")
    
    os.environ["GOOGLE_API_KEY"] = googleKey
    os.environ["OPENAI_API_KEY"] = key



def get_model():
    openai_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2
    )

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


load_env()
llm = get_model()
prompt = get_prompt()
chain = prompt | llm | pydantic_parser


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

# Função assíncrona para obter produtos com streaming
async def get_products_streaming(target_product: str) -> AsyncGenerator[str, None]:
    print("Iniciando busca de produtos similares (streaming)...")
    
    # Primeiro, enviamos uma mensagem de início
    yield json.dumps({"status": "iniciando", "message": "Iniciando busca de produtos similares..."}) + "\n"
    # Pequeno atraso para garantir que o cliente receba esta mensagem
    await asyncio.sleep(0.1)
    
    # Obtendo a lista de produtos similares
    start_time = time.time()
    product_list = get_similar_products(target_product)
    end_time = time.time()
    search_time = end_time - start_time
    
    # Enviamos a mensagem de que encontramos produtos similares
    yield json.dumps({
        "status": "produtos_encontrados", 
        "message": f"Produtos similares encontrados em {search_time:.2f} segundos",
        "count": len(product_list)
    }) + "\n"
    # Pequeno atraso para garantir que o cliente receba esta mensagem
    await asyncio.sleep(0.1)
    
    # Preparamos a consulta para o LLM
    query = query_template.format(product_list=product_list, target_product=target_product)
    
    # Enviamos mensagem de que estamos iniciando o raciocínio do LLM
    yield json.dumps({"status": "iniciando_llm", "message": "Iniciando análise de similaridade..."}) + "\n"
    # Pequeno atraso para garantir que o cliente receba esta mensagem
    await asyncio.sleep(0.1)
    
    # Executamos o LLM
    start_time_2 = time.time()
    result = chain.invoke({"query": query})
    end_time_2 = time.time()
    llm_time = end_time_2 - start_time_2
    
    # Enviamos o resultado final
    yield json.dumps({
        "status": "concluido",
        "message": f"Análise concluída em {llm_time:.2f} segundos",
        "result": result.dict()
    }) + "\n"


# Função para processar múltiplos produtos em paralelo com streaming
async def process_products_streaming(target_products: List[str]) -> AsyncGenerator[str, None]:
    # Enviamos uma mensagem de início
    yield json.dumps({
        "status": "iniciando", 
        "message": f"Iniciando processamento de {len(target_products)} produtos"
    }) + "\n"
    # Pequeno atraso para garantir que o cliente receba esta mensagem
    await asyncio.sleep(0.1)
    
    # Processamos cada produto sequencialmente, mas com streaming de resultados
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
            # Notificamos que estamos iniciando o processamento deste produto
            yield json.dumps({
                "status": "processando_produto",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Iniciando processamento do produto {i+1}/{len(target_products)}: {target_product}"
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Obtendo produtos similares
            start_time = time.time()
            product_list = get_similar_products(target_product)
            end_time = time.time()
            search_time = end_time - start_time
            
            # Notificamos que encontramos produtos similares
            yield json.dumps({
                "status": "produtos_encontrados",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Produtos similares encontrados em {search_time:.2f} segundos",
                "count": len(product_list)
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Preparamos a consulta para o LLM
            query = query_template.format(product_list=product_list, target_product=target_product)
            
            # Notificamos que estamos iniciando o raciocínio do LLM
            yield json.dumps({
                "status": "iniciando_llm",
                "produto_idx": i,
                "produto": target_product,
                "message": "Iniciando análise de similaridade..."
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Executamos o LLM
            start_time_2 = time.time()
            result = chain.invoke({"query": query})
            end_time_2 = time.time()
            llm_time = end_time_2 - start_time_2
            
            # Enviamos o resultado para este produto
            yield json.dumps({
                "status": "produto_concluido",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Análise concluída em {llm_time:.2f} segundos",
                "result": result.dict()
            }) + "\n"
            await asyncio.sleep(0.1)
            
        except Exception as e:
            # Em caso de erro, notificamos
            yield json.dumps({
                "status": "erro",
                "produto_idx": i,
                "produto": target_product,
                "message": f"Erro ao processar produto: {str(e)}"
            }) + "\n"
            await asyncio.sleep(0.1)
    
    # Notificamos que todo o processamento foi concluído
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
            "X-Accel-Buffering": "no"  # Desativa o buffering no Nginx, se estiver usando
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
    # Obtém os dados do corpo da requisição
    data = await request.json()
    
    # Verifica se data é uma lista ou um dicionário
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
            "X-Accel-Buffering": "no"  # Desativa o buffering no Nginx, se estiver usando
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=1313,
        timeout_keep_alive=120,  # Aumenta o tempo de keep-alive
        log_level="info"
    )