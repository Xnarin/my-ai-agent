from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag.config import EMBEDDING_MODEL


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    load_dotenv()
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
