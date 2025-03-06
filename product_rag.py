from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time

# Variáveis globais
persist_directory = "./vector_db_products"
products_file = "./products.json"
vectordb = None
embedding_function = None

def initialize_db():
    """Inicializa o banco de dados vetorial apenas uma vez"""
    global vectordb, embedding_function
    
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Configura o Google AI
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada. Configure a variável de ambiente.")
    
    genai.configure(api_key=google_api_key)
    
    # Configura o embedding do Gemini
    embedding_function = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        task_type="retrieval_document",
        google_api_key=google_api_key
    )

    # Verifica se o banco de dados já existe
    if os.path.exists(persist_directory):
        try:
            print(f"Carregando banco de dados existente de {persist_directory}")
            vectordb = Chroma(
                persist_directory=persist_directory,
                embedding_function=embedding_function
            )
            return
        except Exception as e:
            # Se ocorrer erro ao carregar o banco existente (como incompatibilidade de versão),
            # remove o banco e cria um novo
            if "no such column: collections.topic" in str(e) or "sqlite3.OperationalError" in str(e):
                print(f"Erro ao carregar banco de dados existente: {str(e)}")
                print("Detectada incompatibilidade de versão do banco de dados. Recriando...")
                import shutil
                shutil.rmtree(persist_directory)
                print(f"Banco de dados antigo removido de {persist_directory}")
            else:
                # Se for outro tipo de erro, propaga o erro
                raise e
    
    # Cria o banco de dados se não existir ou se foi removido devido a incompatibilidade
    print(f"Criando novo banco de dados em {persist_directory}")
    
    # Carrega e processa os documentos
    loader = JSONLoader(
        file_path=products_file,
        jq_schema='.products[].ItemName',
        text_content=False
    )
    products = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(products)

    # Cria o banco de vetores e persiste
    vectordb = Chroma.from_documents(
        documents=all_splits,
        embedding=embedding_function,
        persist_directory=persist_directory
    )
    print(f"Banco de dados criado com sucesso em {persist_directory}")

def recreate_db():
    """Força a recriação do banco de dados"""
    global vectordb
    
    # Força a recriação do banco de dados
    import shutil
    if os.path.exists(persist_directory):
        print(f"Removendo banco de dados existente em {persist_directory}")
        shutil.rmtree(persist_directory)
    
    # Reinicializa o banco de dados
    vectordb = None
    initialize_db()

def get_similar_products(product_name: str):
    """Busca produtos similares no banco de dados vetorial"""
    global vectordb
    
    # Inicializa o banco de dados se ainda não foi inicializado
    if vectordb is None:
        initialize_db()
    
    # Realiza a busca por similaridade
    retrieved_docs = vectordb.similarity_search_with_score(product_name, k=300)

    filtered_docs = [(doc, score) for doc, score in retrieved_docs]

    # Remove documentos duplicados baseado no conteúdo
    seen_contents = set()
    unique_filtered_docs = []
    for doc, score in filtered_docs:
        if doc.page_content not in seen_contents:
            unique_filtered_docs.append((doc, score))
            seen_contents.add(doc.page_content)

    # Print the total number of filtered documents
    print(f"Total number of filtered documents: {len(unique_filtered_docs)}")

    unique_filtered_docs_without_score = [doc for doc, score in unique_filtered_docs]
    return unique_filtered_docs_without_score

#products = get_similar_products("INS CANUDO 10MM 100 UN")
