from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from product_rag import get_similar_products

class FoundObject(BaseModel):
    ItemName: str = Field(description="Name of the item found")
    Similarity: float = Field(description="Similarity of the item found")
    
class FoundObjects(BaseModel):
    found_objects: list[FoundObject] = Field(description="List of found objects of high similarity")

pydantic_parser = PydanticOutputParser(pydantic_object=FoundObjects)


def load_env():
    load_dotenv()
    googleKey=os.getenv("GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = googleKey


def get_model():
    google_model = "gemini-1.5-pro"
    temperature = 0.0
    llm = ChatGoogleGenerativeAI(model=google_model, temperature=temperature)

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


query = """
<product-list>
{product_list}
</product-list>


<target-product>
{target_product}
</target-product>
"""






target_product = "Detergente de roupa perfect white 7L"








print("Initiating similar product search...")
product_list = get_similar_products(target_product)
print("Product list obtained.")

query = query.format(product_list=product_list, target_product=target_product)
result = chain.invoke({"query": query})
print(result)

