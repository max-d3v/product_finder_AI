from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time
import random
import logging
from langchain_google_genai._common import GoogleGenerativeAIError

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Variáveis globais
persist_directory = "./vector_db_products"
products_file = "./products.json"
vectordb = None
embedding_function = None

# Configurações de retry
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 60  # segundos
MAX_RETRY_DELAY = 600  # 10 minutos

def retry_with_exponential_backoff(func):
    """Decorator para implementar retry com backoff exponencial"""
    def wrapper(*args, **kwargs):
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except GoogleGenerativeAIError as e:
                if "429 Resource has been exhausted" in str(e):
                    retry_count += 1
                    if retry_count >= MAX_RETRIES:
                        logger.error(f"Número máximo de tentativas ({MAX_RETRIES}) excedido. Erro: {e}")
                        raise
                    
                    # Calcula o tempo de espera com jitter
                    delay = min(INITIAL_RETRY_DELAY * (2 ** (retry_count - 1)) + random.uniform(0, 1), MAX_RETRY_DELAY)
                    logger.warning(f"Cota da API excedida. Tentativa {retry_count}/{MAX_RETRIES}. Aguardando {delay:.2f} segundos...")
                    time.sleep(delay)
                else:
                    # Se não for erro de cota, propaga o erro
                    raise
    return wrapper

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
            logger.info(f"Carregando banco de dados existente de {persist_directory}")
            vectordb = Chroma(
                persist_directory=persist_directory,
                embedding_function=embedding_function
            )
            return
        except Exception as e:
            # Se ocorrer erro ao carregar o banco existente (como incompatibilidade de versão),
            # remove o banco e cria um novo
            if "no such column: collections.topic" in str(e) or "sqlite3.OperationalError" in str(e):
                logger.warning(f"Erro ao carregar banco de dados existente: {str(e)}")
                logger.info("Detectada incompatibilidade de versão do banco de dados. Recriando...")
                import shutil
                shutil.rmtree(persist_directory)
                logger.info(f"Banco de dados antigo removido de {persist_directory}")
            else:
                # Se for outro tipo de erro, propaga o erro
                raise e
    
    # Cria o banco de dados se não existir ou se foi removido devido a incompatibilidade
    logger.info(f"Criando novo banco de dados em {persist_directory}")
    
    # Carrega e processa os documentos
    loader = JSONLoader(
        file_path=products_file,
        jq_schema='.products[].ItemName',
        text_content=False
    )
    products = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(products)

    # Cria o banco de vetores e persiste com retry
    create_vector_db_with_retry(all_splits)
    logger.info(f"Banco de dados criado com sucesso em {persist_directory}")

@retry_with_exponential_backoff
def create_vector_db_with_retry(documents):
    """Cria o banco de dados vetorial com retry em caso de erro de cota"""
    global vectordb, embedding_function, persist_directory
    
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embedding_function,
        persist_directory=persist_directory
    )
    return vectordb

def recreate_db():
    """Força a recriação do banco de dados"""
    global vectordb
    
    # Força a recriação do banco de dados
    import shutil
    if os.path.exists(persist_directory):
        logger.info(f"Removendo banco de dados existente em {persist_directory}")
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
    
    # Realiza a busca por similaridade com retry
    return search_products_with_retry(product_name)

@retry_with_exponential_backoff
def search_products_with_retry(product_name: str):
    """Realiza a busca por similaridade com retry em caso de erro de cota"""
    global vectordb
    
    logger.info(f"Buscando produtos similares a: {product_name}")
    
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

    # Log do número total de documentos filtrados
    logger.info(f"Total de documentos filtrados: {len(unique_filtered_docs)}")

    unique_filtered_docs_without_score = [doc for doc, score in unique_filtered_docs]
    return unique_filtered_docs_without_score

#products = get_similar_products("INS CANUDO 10MM 100 UN")
