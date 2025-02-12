from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os

def load_env():
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY_NEW")
    os.environ["OPENAI_API_KEY"] = key

def get_similar_products(product_name: str):
    load_env()
    persist_directory = "vector_db_products"
    embedding_function = OpenAIEmbeddings(model="text-embedding-3-large")

    # Check if the persisted database exists
    if os.path.exists(persist_directory):
        # Load the persisted database
        vectordb = Chroma(
            persist_directory=persist_directory,
            embedding_function=embedding_function
        )
    else:
        # Load and process documents
        loader = JSONLoader(
            file_path='./products.json',
            jq_schema='.products[].ItemName',
            text_content=False
        )
        products = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        all_splits = text_splitter.split_documents(products)

        # Create the vector store and persist it
        vectordb = Chroma.from_documents(
            documents=all_splits,
            embedding=embedding_function,
            persist_directory=persist_directory
        )
        vectordb.persist()

    # Perform similarity search
    retrieved_docs = vectordb.similarity_search(product_name, k=300)
    page_contents = [doc.page_content for doc in retrieved_docs]

    print("Found products: ")
    print(page_contents)

    return page_contents

#products = get_similar_products("PAPEL TOALHA VIP 6X200 MTR - PROPAPER")
