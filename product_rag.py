from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
import requests
from langchain_core.documents import Document


def get_similar_products(product_name: str):
    try:
        persist_directory = "vector_db_products"
        embedding_function = OpenAIEmbeddings(model="text-embedding-3-large")

        if os.path.exists(persist_directory):
            try:
                vectordb = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=embedding_function
                )
            except Exception as e:
                print(f"Erro ao carregar banco de vetores: {str(e)}")
                raise Exception("Falha ao acessar banco de vetores")
        else:
            try:
                url = os.getenv("WEB_SERVICE_URL")
                if not url:
                    raise Exception("URL do serviço web não configurada")

                token = os.getenv("TOKEN")
                if not token:
                    raise Exception("Token não configurado")

                schema = os.getenv("SCHEMA")
                if not schema:
                    raise Exception("Schema não configurado")

                params = {
                    "token": token,
                    "query": f'SELECT "ItemName" FROM {schema}."OITM" WHERE "validFor" = \'Y\' AND "ItemType" = \'I\' ORDER BY "ItemCode"'
                }
                
                response = requests.get(url + "/consultaSQL", params=params, timeout=10)
                response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
                products_data = response.json()
                
                if not products_data:
                    raise Exception("Nenhum produto encontrado na base de dados")

                documents = [
                    Document(page_content=item["ItemName"]) 
                    for item in products_data
                ]

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                all_splits = text_splitter.split_documents(documents)

                vectordb = Chroma.from_documents(
                    documents=all_splits,
                    embedding=embedding_function,
                    persist_directory=persist_directory
                )
                vectordb.persist()
            except requests.RequestException as e:
                print(f"Erro na requisição HTTP: {str(e)}")
                raise Exception("Falha na comunicação com o serviço web")
            except Exception as e:
                print(f"Erro ao criar banco de vetores: {str(e)}")
                raise

        retrieved_docs = vectordb.similarity_search_with_score(product_name, k=300)
        
        if not retrieved_docs:
            return []

        filtered_docs = [(doc, score) for doc, score in retrieved_docs if score <= 0.91]

        seen_contents = set()
        unique_filtered_docs = []
        for doc, score in filtered_docs:
            if doc.page_content not in seen_contents:
                unique_filtered_docs.append((doc, score))
                seen_contents.add(doc.page_content)

        print(f"Total de documentos filtrados: {len(unique_filtered_docs)}")
        
        for doc, score in unique_filtered_docs:
            print(f"Conteúdo: {doc.page_content}, Pontuação: {score}")

        return [doc for doc, score in unique_filtered_docs]

    except Exception as e:
        print(f"Erro ao processar busca de produtos similares: {str(e)}")
        raise
