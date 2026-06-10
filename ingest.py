import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from google import genai
import os, sys, time
from dotenv import load_dotenv
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

def extract_text(pdf_path):
    # Normal text try பண்ணு
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    
    # Text இல்லன்னா OCR use பண்ணு
    if len(text.strip()) < 50:
        print("Scanned PDF detected — using OCR...")
        images = convert_from_path(pdf_path)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
    
    return text

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
        time.sleep(0.7)

    print("Done!")

if __name__ == "__main__":
    ingest_pdf(sys.argv[1])