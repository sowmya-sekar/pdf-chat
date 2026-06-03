from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os, time

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

print("Deleting old index...")
pc.delete_index("pdf-rag-index")
time.sleep(10)

print("Creating new index with dimension 3072...")
pc.create_index(
    name="pdf-rag-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
print("Done!")