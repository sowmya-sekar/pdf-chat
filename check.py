from pinecone import Pinecone
from dotenv import load_dotenv
import os

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
info = pc.describe_index("pdf-rag-index")
print("Dimension:", info.dimension)