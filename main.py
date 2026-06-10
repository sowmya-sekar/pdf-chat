from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from google import genai
from groq import Groq
import os, tempfile
from dotenv import load_dotenv
from ingest import ingest_pdf

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        index.delete(delete_all=True)
    except Exception:
        pass
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    ingest_pdf(tmp_path)
    return {"message": f"{file.filename} ingested!"}

@app.post("/query")
async def query(req: QueryRequest):
    q_emb = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=req.question
    ).embeddings[0].values

    results = index.query(
        vector=q_emb,
        top_k=req.top_k,
        include_metadata=True
    )
    chunks = [m.metadata["text"] for m in results.matches]
    context = "\n\n---\n\n".join(chunks)

    prompt = f"""Answer the question based ONLY on the context below.
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {req.question}"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return {
        "answer": response.choices[0].message.content,
        "sources": chunks[:3]
    }

@app.post("/summarize")
async def summarize():
    results = index.query(
        vector=[0.0] * 3072,
        top_k=10,
        include_metadata=True
    )
    chunks = [m.metadata["text"] for m in results.matches]
    context = "\n\n".join(chunks)

    prompt = f"""Based on the document below, provide:
1. **Summary** - 5 sentence overview
2. **Key Points** - 7 most important bullet points
3. **Important Terms** - 5 key terms with definitions

Document:
{context}"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"summary": response.choices[0].message.content}

@app.get("/")
def root():
    return {"status": "RAG API running!"}