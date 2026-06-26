from pydantic import BaseModel, Field

class UploadResponse(BaseModel): 
    session_id : str
    filename: str
    pages: int 
    chunks_stored: int 
    message: str 
    
    
class QueryRequest(BaseModel): 
    session_id: str
    question: str = Field (..., min_length=1, max_length=1000)
    
class SourceChunk(BaseModel): 
    content: str
    page: int 
    chunk_index: int 
    relevance_score: float 
    
    
class QueryResponse(BaseModel): 
    answer: str 
    sources: list[SourceChunk]
    session_id: str 
    
    
class ErrorResponse(BaseModel):
    error: str
    details: str | None = None
