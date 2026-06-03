import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from google import genai
import os, sys
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=100
    )
    return splitter.split_text(text)

def embed(text):
    res = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return res.embeddings[0].values

def ingest_pdf(pdf_path):
    print(f"Reading {pdf_path}...")
    text = extract_text(pdf_path)
    chunks = chunk_text(text)
    print(f"{len(chunks)} chunks ready. Embedding...")

    for i, chunk in enumerate(chunks):
        embedding = embed(chunk)
        index.upsert(vectors=[{
            "id": f"chunk-{i}",
            "values": embedding,
            "metadata": {"text": chunk, "source": pdf_path}
        }])
        if i % 10 == 0:
            print(f"  {i+1}/{len(chunks)} done...")

    print("Done!")

if __name__ == "__main__":
    ingest_pdf(sys.argv[1])