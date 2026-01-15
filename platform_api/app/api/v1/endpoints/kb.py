from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio

from app.db.session import get_db
from app.models.kb import KnowledgeBase, KBFile, FileStatus
from app.schemas import kb as schemas
from shared.libs.openai_client import OpenAIClient

router = APIRouter()

@router.post("", response_model=schemas.KnowledgeBase)
async def create_kb(kb_in: schemas.KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new Knowledge Base and corresponding OpenAI Vector Store."""
    client = OpenAIClient()
    
    # 1. Create Vector Store
    try:
        vs_data = await client.create_vector_store(kb_in.name)
        vs_id = vs_data.get("id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Vector Store: {str(e)}")
        
    # 2. Save DB
    db_obj = KnowledgeBase(
        name=kb_in.name,
        description=kb_in.description,
        expires_after_days=kb_in.expires_after_days,
        strategy="openai_vector_store",
        openai_vector_store_id=vs_id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("", response_model=List[schemas.KnowledgeBase])
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
        raise HTTPException(status_code=404, detail="KB not found")
    return kb

@router.post("/{kb_id}/files", response_model=schemas.KBFile)
async def upload_kb_file(
    kb_id: int, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads file to OpenAI, attaches to Vector Store, and polls for completion.
    """
    # Verify KB
    res = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = res.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    client = OpenAIClient()
    
    # 1. Read content
    content = await file.read()
    filename = file.filename
    
    # 2. Upload File
    try:
        f_data = await client.upload_file(content, filename)
        file_id = f_data.get("id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI File Upload failed: {str(e)}")
        
    # 3. Attach to VS
    try:
        vs_f_data = await client.create_vector_store_file(kb.openai_vector_store_id, file_id)
        # Initial status is usually in_progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attach to VS failed: {str(e)}")
        
    # 4. Save DB Record (In Progress)
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
    
    # 5. Poll for Completion (Short duration for UX)
    # We will poll for up to 5 seconds. If not done, return as in_progress.
    # Client can poll the file endpoint later.
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
        except Exception:
            pass # Ignore poll errors, keep initial status
            
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
    res = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = res.scalar_one_or_none()
    if not kb or not kb.openai_vector_store_id:
        raise HTTPException(status_code=400, detail="KB not ready or invalid")
    
    client = OpenAIClient()
    try:
        answer = await client.one_shot_rag_query(kb.openai_vector_store_id, query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
