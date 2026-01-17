from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio
import os
import uuid
import logging

from app.db.session import get_db
from app.models.kb import KnowledgeBase, KBFile, FileStatus
from app.schemas import kb as schemas
from shared.libs.openai_client import OpenAIClient

# Constants
KB_NOT_FOUND = "KB not found"
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES = ["text/plain", "text/markdown", "application/pdf"]

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=schemas.KnowledgeBaseSimple)
async def create_kb(kb_in: schemas.KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new Knowledge Base. Uses OpenAI if key is available, otherwise local storage."""
    
    # Check if OpenAI is configured
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if openai_key:
        # OpenAI Vector Store strategy
        client = OpenAIClient()
        try:
            vs_data = await client.create_vector_store(kb_in.name)
            vs_id = vs_data.get("id")
            strategy = "openai_vector_store"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create Vector Store: {str(e)}")
    else:
        # Local storage strategy
        vs_id = None
        strategy = "local"
        
    # Save DB
    db_obj = KnowledgeBase(
        name=kb_in.name,
        description=kb_in.description,
        expires_after_days=kb_in.expires_after_days,
        strategy=strategy,
        openai_vector_store_id=vs_id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("", response_model=List[schemas.KnowledgeBaseSimple])
async def list_kbs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()))
    return result.scalars().all()

@router.get("/{kb_id}", response_model=schemas.KnowledgeBase)
async def get_kb(kb_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_id)
        .options(selectinload(KnowledgeBase.files))
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail=KB_NOT_FOUND)
    return kb

@router.put("/{kb_id}", response_model=schemas.KnowledgeBaseSimple)
async def update_kb(
    kb_id: int,
    kb_update: schemas.KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update KB name and description"""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail=KB_NOT_FOUND)
    
    kb.name = kb_update.name
    kb.description = kb_update.description
    if kb_update.expires_after_days is not None:
        kb.expires_after_days = kb_update.expires_after_days
    
    await db.commit()
    await db.refresh(kb)
    return kb

@router.delete("/{kb_id}")
async def delete_kb(kb_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a Knowledge Base and all its files"""
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_id)
        .options(selectinload(KnowledgeBase.files))
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail=KB_NOT_FOUND)
    
    # Delete from OpenAI if applicable
    if kb.strategy == "openai_vector_store" and kb.openai_vector_store_id:
        # Note: OpenAI doesn't have a delete endpoint for vector stores in current API
        # Files will be orphaned but that's acceptable for now
        pass
    
    # Delete local files if applicable
    if kb.strategy == "local":
        for file in kb.files:
            if file.local_file_path and os.path.exists(file.local_file_path):
                try:
                    os.remove(file.local_file_path)
                except OSError as e:
                    logging.warning(f"Failed to delete file {file.local_file_path}: {e}")
    
    await db.delete(kb)
    await db.commit()
    return {"ok": True}

@router.post("/{kb_id}/files", response_model=schemas.KBFile)
async def upload_kb_file(
    kb_id: int, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads file. Uses OpenAI if KB uses that strategy, otherwise saves locally.
    """
    # Verify KB
    res = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = res.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail=KB_NOT_FOUND)

    # Read content
    content = await file.read()
    filename = file.filename
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
        )
    
    if kb.strategy == "openai_vector_store":
        # OpenAI flow (existing logic)
        client = OpenAIClient()
        
        try:
            f_data = await client.upload_file(content, filename)
            file_id = f_data.get("id")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI File Upload failed: {str(e)}")
            
        try:
            vs_f_data = await client.create_vector_store_file(kb.openai_vector_store_id, file_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Attach to VS failed: {str(e)}")
            
        db_file = KBFile(
            kb_id=kb.id,
            filename=filename,
            mime_type=file.content_type,
            openai_file_id=file_id,
            openai_vector_store_file_id=vs_f_data.get("id"),
            status=FileStatus.in_progress
        )
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
        
        # Poll for completion
        for _ in range(5):
            try:
                status_data = await client.get_vector_store_file(kb.openai_vector_store_id, file_id)
                current_status = status_data.get("status")
                
                if current_status == "completed":
                    db_file.status = FileStatus.completed
                    db_file.usage_bytes = status_data.get("usage_bytes", 0)
                    await db.commit()
                    break
                elif current_status == "failed":
                    db_file.status = FileStatus.failed
                    await db.commit()
                    break
                
                await asyncio.sleep(1)
            except Exception as e:
                logging.warning(f"Error polling file status: {e}")
                
    else:
        # Local storage flow
        # Create storage directory
        storage_dir = "/app/data/kb_files"
        os.makedirs(storage_dir, exist_ok=True)
        
        # Generate unique file path
        file_uuid = str(uuid.uuid4())
        local_path = f"{storage_dir}/{kb_id}_{file_uuid}_{filename}"
        
        # Save file
        with open(local_path, "wb") as f:
            f.write(content)
            
        # Extract text content (simple text extraction for now)
        try:
            file_text = content.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            file_text = ""
            
        db_file = KBFile(
            kb_id=kb.id,
            filename=filename,
            mime_type=file.content_type,
            local_file_path=local_path,
            file_content=file_text[:50000],  # Limit stored text to 50k chars
            status=FileStatus.completed,
            usage_bytes=len(content)
        )
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
            
    await db.refresh(db_file)
    return db_file

@router.delete("/{kb_id}/files/{file_id}")
async def delete_kb_file(kb_id: int, file_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KBFile).where(KBFile.id == file_id, KBFile.kb_id == kb_id))
    db_file = result.scalar_one_or_none()
    
    if not db_file:
         raise HTTPException(status_code=404, detail="File not found")
         
    # Detach from OpenAI
    # We ideally need the kb to get vector_store_id, but we can query it or join
    # Re-query with join for safety
    res_kb = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = res_kb.scalar_one_or_none()
    
    if kb and db_file.openai_file_id:
        client = OpenAIClient()
        try:
            # Attempt to delete from VS
            # But the endpoint takes file_id (OpenAI ID).
            await client.delete_vector_store_file(kb.openai_vector_store_id, db_file.openai_file_id)
            # Note: Deleting from VS doesn't delete the File object itself from OpenAI Files storage.
            # To be clean we should also delete the File, but "detach" is main requirement usually.
            # Let's keep it safe.
        except Exception:
            pass # Log warning?
            
@router.post("/{kb_id}/query")
async def query_kb(kb_id: int, query: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.id == kb_id)
        .options(selectinload(KnowledgeBase.files))
    )
    kb = res.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=400, detail="KB not found")
    
    if kb.strategy == "openai_vector_store":
        if not kb.openai_vector_store_id:
            raise HTTPException(status_code=400, detail="KB Vector Store not ready")
        
        client = OpenAIClient()
        try:
            answer = await client.one_shot_rag_query(kb.openai_vector_store_id, query)
            return {"answer": answer}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    else:
        # Local search: simple keyword matching
        query_lower = query.lower()
        matches = []
        
        for file in kb.files:
            if file.file_content and query_lower in file.file_content.lower():
                # Extract snippet around match
                idx = file.file_content.lower().find(query_lower)
                start = max(0, idx - 100)
                end = min(len(file.file_content), idx + 200)
                snippet = file.file_content[start:end]
                matches.append({
                    "filename": file.filename,
                    "snippet": snippet
                })
        
        if matches:
            answer = f"Found in {len(matches)} file(s):\n\n"
            for m in matches[:3]:  # Top 3 matches
                answer += f"**{m['filename']}**: ...{m['snippet']}...\n\n"
        else:
            answer = "No matches found in the knowledge base."
            
        return {"answer": answer, "sources": [m["filename"] for m in matches]}
