import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from llama_stack_client import LlamaStackClient, RAGDocument

logger = logging.getLogger("vector_db")
router = APIRouter(prefix="/vector-db", tags=["vector-database"])

# Globals set from main.py or startup
client: Optional[LlamaStackClient] = None
DEFAULT_VECTOR_DB_ID: Optional[str] = None
DEFAULT_CHUNK_SIZE: int = 512

def set_vector_db_client(
    injected_client: LlamaStackClient,
    default_vector_db_id: Optional[str] = None,
    default_chunk_size: int = 512
):
    global client, DEFAULT_VECTOR_DB_ID, DEFAULT_CHUNK_SIZE
    client = injected_client
    DEFAULT_VECTOR_DB_ID = default_vector_db_id
    DEFAULT_CHUNK_SIZE = default_chunk_size
    logger.info(f"Vector DB client initialized with default DB: {default_vector_db_id}")

# ----------- Models ------------

class CreateVectorDBRequest(BaseModel):
    vector_db_id: str
    embedding_model: str
    embedding_dimension: Optional[int] = 384
    provider_id: Optional[str] = "faiss"

class QueryRequest(BaseModel):
    query: str

class IngestResponse(BaseModel):
    success: bool
    document_id: str
    filename: Optional[str]
    chunks_created: Optional[int] = None

# ----------- Vector DB Management ------------

@router.get("/list")
async def list_vector_dbs():
    """List all vector databases"""
    if not client:
        raise HTTPException(status_code=500, detail="LlamaStackClient not initialized")
    try:
        result = client.vector_dbs.list()
        return result
    except Exception as e:
        logger.error(f"Failed to list vector DBs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_vector_db(request: CreateVectorDBRequest):
    """Create a new vector database"""
    if not client:
        raise HTTPException(status_code=500, detail="LlamaStackClient not initialized")
    try:
        resp = client.vector_dbs.register(
            vector_db_id=request.vector_db_id,
            embedding_model=request.embedding_model,
            embedding_dimension=request.embedding_dimension,
            provider_id=request.provider_id
        )
        return {
            "success": True,
            "vector_db_id": request.vector_db_id,
            "embedding_model": request.embedding_model,
            "response": resp
        }
    except Exception as e:
        logger.error(f"Failed to create vector DB {request.vector_db_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{vector_db_id}")
async def delete_vector_db(vector_db_id: str):
    """Delete an existing vector database"""
    if not client:
        raise HTTPException(status_code=500, detail="LlamaStackClient not initialized")
    try:
        result = client.vector_dbs.unregister(vector_db_id=vector_db_id)
        return {
            "success": True,
            "vector_db_id": vector_db_id,
            "message": "Vector database deleted successfully",
            "response": result
        }
    except Exception as e:
        logger.error(f"Failed to delete vector DB {vector_db_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------- Document Ingestion ------------

@router.post("/{vector_db_id}/ingest", response_model=IngestResponse)
async def ingest_document(vector_db_id: str, file: UploadFile = File(...)):
    """Ingest/upload a document to a vector database"""
    if not client:
        raise HTTPException(status_code=500, detail="LlamaStackClient not initialized")
    try:
        content = await file.read()
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text_content = content.decode('latin-1')
            except Exception:
                raise HTTPException(status_code=400, detail="Unable to decode file content as text")
        doc_id = str(uuid.uuid4())
        rag_doc = RAGDocument(
            document_id=doc_id,
            content=text_content,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content)
            },
            mime_type=file.content_type or "text/plain",
        )
        resp = client.tool_runtime.rag_tool.insert(
            vector_db_id=vector_db_id,
            documents=[rag_doc],
            chunk_size_in_tokens=DEFAULT_CHUNK_SIZE
        )
        return IngestResponse(
            success=True,
            document_id=doc_id,
            filename=file.filename or "unknown",
            chunks_created=getattr(resp, 'chunks_created', None)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{vector_db_id}/ingest-text")
async def ingest_text(vector_db_id: str, text: str = Query(...), title: Optional[str] = Query(None)):
    """Ingest raw text into a vector database"""
    if not client:
        raise HTTPException(status_code=500, detail="LlamaStackClient not initialized")
    try:
        doc_id = str(uuid.uuid4())
        rag_doc = RAGDocument(
            document_id=doc_id,
            content=text,
            metadata={
                "title": title or "Raw text input",
                "type": "text_input",
                "size": len(text)
            },
            mime_type="text/plain",
        )
        resp = client.tool_runtime.rag_tool.insert(
            vector_db_id=vector_db_id,
            documents=[rag_doc],
            chunk_size_in_tokens=DEFAULT_CHUNK_SIZE
        )
        return {
            "success": True,
            "document_id": doc_id,
            "title": title,
            "response": resp
        }
    except Exception as e:
        logger.error(f"Text ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------- Query ------------

@router.post("/{vector_db_id}/query")
async def query_vector_db(vector_db_id: str, request: QueryRequest):
    """Query a vector database for relevant context chunks"""
    if not client:
        raise HTTPException(status_code=500, detail="LlamaStackClient not initialized")
    try:
        resp = client.tool_runtime.rag_tool.query(
            content=request.query,
            vector_db_ids=[vector_db_id]
        )
        if hasattr(resp, 'content'):
            chunks = resp.content if isinstance(resp.content, list) else [resp.content]
            return {
                "success": True,
                "query": request.query,
                "vector_db_id": vector_db_id,
                "chunks": chunks,
                "total_results": len(chunks)
            }
        else:
            return {
                "success": True,
                "query": request.query,
                "vector_db_id": vector_db_id,
                "response": resp
            }
    except Exception as e:
        logger.error(f"Query failed for {vector_db_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vector_db_id}/info")
async def get_vector_db_info(vector_db_id: str):
    """Get information about a specific vector database"""
    if not client:
        raise HTTPException(status_code=500, detail="LlamaStackClient not initialized")
    try:
        all_dbs = client.vector_dbs.list()
        target_db = None
        for db in getattr(all_dbs, 'data', []):
            if getattr(db, 'vector_db_id', None) == vector_db_id:
                target_db = db
                break
        if not target_db:
            raise HTTPException(status_code=404, detail=f"Vector DB '{vector_db_id}' not found")
        return {
            "vector_db_id": vector_db_id,
            "info": target_db,
            "status": "active"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get info for vector DB {vector_db_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------- Health ------------

@router.get("/health")
async def vector_db_health():
    """Health check for vector database service"""
    return {
        "status": "healthy" if client else "not_initialized",
        "client_available": client is not None,
        "default_vector_db": DEFAULT_VECTOR_DB_ID,
        "default_chunk_size": DEFAULT_CHUNK_SIZE
    }
