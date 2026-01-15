from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.ai import AiProvider, AiModel, AiUsageLog
from app.schemas import ai as schemas

router = APIRouter()

# --- PROVIDERS ---
@router.get("/providers", response_model=List[schemas.AiProvider])
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AiProvider).order_by(AiProvider.name))
    return result.scalars().all()

@router.post("/providers", response_model=schemas.AiProvider)
async def create_provider(data: schemas.AiProviderCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    res = await db.execute(select(AiProvider).where(AiProvider.name == data.name))
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Provider with this name already exists")
    
    obj = AiProvider(**data.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/providers/{provider_id}", response_model=schemas.AiProvider)
async def update_provider(provider_id: int, data: schemas.AiProviderUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AiProvider).where(AiProvider.id == provider_id))
    obj = res.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    for k, v in data.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AiProvider).where(AiProvider.id == provider_id))
    obj = res.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    await db.delete(obj)
    await db.commit()
    return {"status": "deleted"}

# --- MODELS ---
@router.get("/models", response_model=List[schemas.AiModelDetail])
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AiModel)
        .options(selectinload(AiModel.provider))
        .order_by(AiModel.name)
    )
    return result.scalars().all()

@router.get("/models/enabled", response_model=List[schemas.AiModelDetail])
async def list_enabled_models(db: AsyncSession = Depends(get_db)):
    """List only enabled models, joined with provider info for UI selectors"""
    result = await db.execute(
        select(AiModel)
        .join(AiProvider)
        .where(AiModel.is_enabled == True)
        .where(AiProvider.is_enabled == True)
        .options(selectinload(AiModel.provider))
        .order_by(AiModel.name)
    )
    return result.scalars().all()

@router.post("/models", response_model=schemas.AiModel)
async def create_model(data: schemas.AiModelCreate, db: AsyncSession = Depends(get_db)):
    obj = AiModel(**data.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@router.put("/models/{model_id}", response_model=schemas.AiModel)
async def update_model(model_id: int, data: schemas.AiModelUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AiModel).where(AiModel.id == model_id))
    obj = res.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="Model not found")
    
    for k, v in data.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    
    await db.commit()
    await db.refresh(obj)
    return obj

@router.delete("/models/{model_id}")
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AiModel).where(AiModel.id == model_id))
    obj = res.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="Model not found")
    
    await db.delete(obj)
    await db.commit()
    return {"status": "deleted"}

# --- USAGE / LOGS (Internal mostly, but exposed for querying) ---
@router.get("/logs", response_model=List[schemas.AiUsageLog])
async def list_logs(
    run_id: str = None, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(AiUsageLog).order_by(AiUsageLog.created_at.desc()).limit(limit)
    if run_id:
        query = query.where(AiUsageLog.run_id == run_id)
        
    result = await db.execute(query)
    return result.scalars().all()
