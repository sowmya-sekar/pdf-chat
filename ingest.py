import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from google import genai
import os, sys, time
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    if len(text.strip()) < 50:
        try:
            import pytesseract
            from pdf2image import convert_from_path
            print("Scanned PDF — using OCR...")
            images = convert_from_path(pdf_path)
            text = "\n".join(pytesseract.image_to_string(img) for img in images)
        except Exception as e:
            print(f"OCR failed: {e}")
    return text

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=100
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

    vectors = []
    for i, chunk in enumerate(chunks):
        try:
            embedding = embed(chunk)
            vectors.append({
                "id": f"chunk-{i}",
                "values": embedding,
                "metadata": {"text": chunk, "source": pdf_path}
            })
            if i % 10 == 0:
                print(f"  {i+1}/{len(chunks)} done...")
            time.sleep(0.3)  # 0.7 → 0.3 குறைச்சோம்

            # batch 50-ஆ upsert பண்ணு
            if len(vectors) >= 50:
                index.upsert(vectors=vectors)
                vectors = []
        except Exception as e:
            print(f"Error at chunk {i}: {e}")
            time.sleep(2)
            continue

    # remaining vectors
    if vectors:
        index.upsert(vectors=vectors)

    print("Done!")

if __name__ == "__main__":
    ingest_pdf(sys.argv[1])