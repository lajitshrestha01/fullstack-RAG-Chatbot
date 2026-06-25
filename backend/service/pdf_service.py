import uuid 
import logging
from io import BytesIO

import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from config import settings
from rag.prompt import build_query_prompt, DOCUMENT_QA_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
groq_client = OpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)
chroma_client = chromadb.EphemeralClient()


# pdf processing

def extract_text_by_page(pdf_bytes: bytes) -> list[dict]:
    """
    Extracts text page by page, preserving page numbers.
    Page numbers are how citations work.
    """
    reader = PdfReader(BytesIO(pdf_bytes))

    if len(reader.pages) > settings.MAX_PDF_PAGES:
        raise ValueError(
            f"Pdf has {len(reader.pages)} pages. "
            f"Maximum allowed is {settings.MAX_PDF_PAGES}"
        )

    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({"page": i + 1, "text": text.strip()})

    return pages


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Splits each page into chunks, keeping page number attached.
    Overlap ensures context isn't lost at chunk boundaries.
    """
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = settings.CHUNK_SIZE, 
        chunk_overlap = settings.CHUNK_OVERLAP, 
        separators=["\n\n", "\n",  ". ", " ", ""]
    )
    
    chunks = []
    for page_data in pages: 
        splits = splitter.split_text(page_data["text"])
        for i, split in enumerate(splits): 
            chunks.append(
                {
                    "text": split, 
                    "page": page_data["page"], 
                    "chunk_index": i
                }
            )
    
    return chunks

#Embedding

def embed_text(texts: list[str]) -> list[list[float]]:
    """
    One API call for all texts. Never call this in a loop.
    OpenAI batches up to 2048 inputs per request.
    """
    response = openai_client.embeddings.create(
        model=settings.EMBED_MODEL, 
        input=texts,
    )
    return [item.embedding for item in response.data]

#main pipeline entry points 

def process_pdf(pdf_bytes: bytes, filename: str) -> dict:
    """
    The only function the controller calls for uploads.
    Takes raw bytes in, returns session_id + stats out.
    """
    pages = extract_text_by_page(pdf_bytes)
    logger.info("%s: %d pages extracted", filename, len(pages))

    chunks = chunk_pages(pages)
    logger.info("%s: %d chunks created", filename, len(chunks))

    texts = [c["text"] for c in chunks]
    embedding = embed_text(texts)
    logger.info("%s: %d embeddings generated", filename, len(embedding))
    
    session_id = str(uuid.uuid4())
    collection = chroma_client.create_collection(
        name=f"{settings.CHROMA_COLLECTION_PREFIX}_{session_id}"
    ) 
    
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        embeddings=embedding, 
        documents=texts, 
        metadatas=[
            {
                "page": c["page"],
                "chunk_index": c["chunk_index"],
                "source": filename,
            }
            for c in chunks
        ],
    )
    logger.info("Session %s: %d chunks stored", session_id, len(chunks))
    
    return {
        "session_id": session_id, 
        "pages": len(pages), 
        "chunks_stored": len(chunks),
    }
    
    
def retrieve_chunks(session_id: str, question: str, top_k: int = 5) -> list[dict]:
    """
    Retrieves the top_k most relevant chunks for a question.
    Scoped strictly to one session's collection.
    """
    try:
        collection = chroma_client.get_collection(
            name=f"{settings.CHROMA_COLLECTION_PREFIX}_{session_id}"
        )
    except Exception as exc:
        raise ValueError(
            f"Session '{session_id}' not found. Upload a pdf first"
        ) from exc

    question_embedding = embed_text([question])[0]

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "content": doc,
            "page": meta["page"],
            "chunk_index": meta["chunk_index"],
            "source": meta["source"],
            "relevance_score": round(1 - distance, 4),
        })
    return chunks


def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a context string for the LLM.
    The [source] tags are what makes citation possible.
    LLM is instructed to reference these tags in its answer.
    """
    parts = []
    for chunk in chunks:
        parts.append(
            f"[Source: {chunk['source']}, Page {chunk['page']}\n{chunk['content']}]"
        )

    return "\n\n---\n\n".join(parts)

def query_llm(question: str, context: str) -> str:
    """
    Sends context + question to Groq. Non-streaming version.
    """
    response = groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": DOCUMENT_QA_SYSTEM_PROMPT},
            {"role": "user", "content": build_query_prompt(context, question)},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content
    
