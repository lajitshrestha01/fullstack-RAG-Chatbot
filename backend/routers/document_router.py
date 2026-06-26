from fastapi import APIRouter, UploadFile, File
from controllers.document_controller import handle_upload, handle_query
from schemas.document import UploadResponse, QueryRequest, QueryResponse

router = APIRouter(prefix="/api/v1", tags=["documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)): 
    return await handle_upload(file)

@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    return await handle_query(request)