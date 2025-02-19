from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from typing import List
from product_rag import get_similar_products

app = FastAPI()

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
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )
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
    print("Initiating similar product search...")
    product_list = get_similar_products(target_product)
    print("Product list obtained.")

    query = query_template.format(product_list=product_list, target_product=target_product)
    result = chain.invoke({"query": query})
    return result


@app.get("/product/{target_product}")
def get_product(target_product: str):
    if (target_product is None or target_product == ""):
        return {"error": "No target product provided."}
    result = get_products(target_product)
    return result

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=1313)