from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from fastapi import FastAPI

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from product_rag import get_similar_products

app = FastAPI()

class FoundObject(BaseModel):
    ItemName: str = Field(description="Name of the item found")
    Similarity: float = Field(description="Similarity of the item found")
    
class FoundObjects(BaseModel):
    found_objects: list[FoundObject] = Field(description="List of found objects of high similarity")

pydantic_parser = PydanticOutputParser(pydantic_object=FoundObjects)


def load_env():
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY_NEW")
    os.environ["OPENAI_API_KEY"] = key



def get_model():
    model = "gpt-4o-mini"
    temperature = 0.0
    llm = ChatOpenAI(model=model, temperature=temperature)

    return llm

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
    try:
        print("Iniciando busca por produtos similares...")
        product_list = get_similar_products(target_product)
        print("Lista de produtos obtida.")

        if not product_list:
            return {"error": "Nenhum produto similar encontrado."}

        query = query_template.format(product_list=product_list, target_product=target_product)
        result = chain.invoke({"query": query})
        return result
    except Exception as e:
        print(f"Erro ao buscar produtos: {str(e)}")
        return {"error": f"Erro ao processar a requisição: {str(e)}"}


@app.get("/product/{target_product}")
async def get_product(target_product: str):
    try:
        if not target_product or target_product.isspace():
            return {"error": "Produto alvo não fornecido."}
        result = get_products(target_product)
        return result
    except Exception as e:
        return {"error": f"Erro no servidor: {str(e)}", "status": 500}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=1313)