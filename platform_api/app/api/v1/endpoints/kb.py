from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import shutil
import os
import aiofiles

from app.db.session import get_db
from app.models.kb import KBDocument
from app.schemas.kb import KBDocument as KBDocumentSchema
from app.api import deps

router = APIRouter()

UPLOAD_DIR = "/app/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=KBDocumentSchema)
async def upload_document(
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(deps.get_current_active_user) # Optional auth
) -> Any:
    """
    Upload a document to the Knowledge Base.
    """
    try:
        # Save file locally
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        # Create DB entry
        client_ip = request.client.host if request else None
        
        db_obj = KBDocument(
            filename=file.filename,
            content_type=file.content_type,
            file_path=file_path,
            upload_ip=client_ip,
            processed=False # Will be processed by worker later
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@router.get("/documents", response_model=List[KBDocumentSchema])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(deps.get_current_active_user)
) -> Any:
    """
    List uploaded documents.
    """
    result = await db.execute(select(KBDocument).offset(skip).limit(limit))
    return result.scalars().all()
