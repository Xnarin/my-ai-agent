from pathlib import Path

PDF_PATH = Path(__file__).resolve().parent / "data" / "SPRi AI Brief_9월호_산업동향_0909_F.pdf"
PERSIST_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "spri_ai_brief"
EMBEDDING_MODEL = "gemini-embedding-2"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
