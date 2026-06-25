import uuid 
import logging
from io import BytesIO

import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
groq_client = OpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)
chroma_client = chromadb.EphemeralClient()


#pdf processing: 
def extract_text_by_page(pdf_bytes: bytes) -> list[dict]: 
    """
    Extracts text page by page, preserving page numbers.
    page number sare how citiation work - don't wanna use them
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    
    if len(reader) > settings.MAX_PDF_PAGES: 
        raise ValueError(
            f"Pdf has {len(reader.pages)} pages."
            f"Maximum allowed is {settings.MAX_PDF_PAGES}"
        )
        
    pages = []
    
    if i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip(): 
            pages.append({"pages": i +1, "text": text.strip()})
            
            
    return pages


def chunk_pages(pages: list[dict]) -> list[dict]: 
    """
    Splits each page into chunks, keeping page number attached. 
    overlap ensure context ins't lost at chunk boundaries 
    
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
                    "chunk_index": 1
                }
            )
    
    return chunks

#Embedding

def embed_text(texts: list[str]) -> list[list[float]]: 
    """
    One api call from all texts. Never call this in a loop. 
    One batches upto 2048 inputs per request. 
    """
    
    response = openai_client.embeddings.create(
        model=settings.EMBED_MODEL, 
        input=texts,
    )
    return [item.embedding for item in response.data]

#main pipeline entry points 

def process_pdf(pdf_bytes: bytes, filename: str) -> dict:
    """
    The only fuction the controller calss for uploads 
    Takes raw bytes in, return session_id + stats out.
    """
    pages = extract_text_by_page(pdf_bytes)
    logger.info(f"{filename}: {len(pages)} pages extracted")
    
    chunks = chunk_pages(pages)
    logger.info(f"{filename}: {len(chunks)} chunks created")
    
    texts = [c["text"] for c in chunks]
    embedding = embed_text(texts)
    logger.info(f"{filename}: {len(embedding)} embeddings generated")
    
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
                "page" ; c["pages"], 
                "chunks_index": c["chunk_index"], 
                "source": filename,
            }
            for c in chunks
        ],
    )
    logger.info(f"Session {session_id}: {len(chunks)} chunks stored")
    
    return {
        "session_id": session_id, 
        "pages": len(pages), 
        "chunks_stored": len(chunks),
    }
    