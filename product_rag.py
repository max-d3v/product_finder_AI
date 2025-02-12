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
    retrieved_docs = vectordb.similarity_search_with_score(product_name, k=300)

    # Filter out documents with score above 0.9
    filtered_docs = [(doc, score) for doc, score in retrieved_docs if score <= 0.91]

    # Remove duplicate documents based on page content
    seen_contents = set()
    unique_filtered_docs = []
    for doc, score in filtered_docs:
        if doc.page_content not in seen_contents:
            unique_filtered_docs.append((doc, score))
            seen_contents.add(doc.page_content)



    # Extract and print page contents and scores
    for doc, score in unique_filtered_docs:
        print(f"Page Content: {doc.page_content}, Score: {score}")


    # Print the total number of filtered documents
    print(f"Total number of filtered documents: {len(unique_filtered_docs)}")

    unique_filtered_docs_without_score = [doc for doc, score in unique_filtered_docs]
    return unique_filtered_docs_without_score

#products = get_similar_products("INS CANUDO 10MM 100 UN")
