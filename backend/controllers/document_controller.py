import logging 
from fastapi import UploadFile, HTTPException

from service.pdf_service import process_pdf, retrieve_chunks, build_context, query_llm
from schemas.document import UploadResponse, QueryRequest, QueryResponse, SourceChunk
from config import settings
logger = logging.getLogger(__name__)

async def handle_upload(file: UploadFile) -> UploadResponse: 
    """
    orchestrates the upload flwo. 
    Validates -> reads bytes -> calls services -> returns response schema. 
    no business logic here, but coordination. 
    
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="only pdf files are accepted")
    
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE: 
        raise HTTPException(status_code=400, detail="file exceeds 10MB limit.")
    
    try: 
        result = process_pdf(pdf_bytes=content, filename=file.filename)
    except ValueError as e:
        logger.error("pdf processing faied: %s", e)
        raise HTTPException(status_code=500, detail="failed to process pdf.") from e
    
    return UploadResponse(
        session_id=result["session_id"], 
        filename=file.filename, 
        pages = result['pages'], 
        chunks_stored=result["chunks_stored"],
        message=f"Sucessfully processed {result['pages']}  pages into {result['chunks_stored']} chunks. "
    )

async def handle_query(request: QueryRequest) -> QueryResponse:
    """
    Orchestrates the query flow.
    Retrieve → build context → query LLM → return response with citations.
    """
    try:
        chunks = retrieve_chunks(
            session_id=request.session_id,
            question=request.question,
        )
    except ValueError as e:
        # Session not found
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Retrieval failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve documents.") from e

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant content found in document for this question."
        )

    context = build_context(chunks)

    try:
        answer = query_llm(question=request.question, context=context)
    except Exception as e:
        logger.error("LLM query failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate answer.") from e

    return QueryResponse(
        answer=answer,
        session_id=request.session_id,
        sources=[
            SourceChunk(
                content=c["content"],
                page=c["page"],
                chunk_index=c["chunk_index"],
                relevance_score=c["relevance_score"],
            )
            for c in chunks
        ],
    )
