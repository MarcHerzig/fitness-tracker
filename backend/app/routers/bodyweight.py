import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import BodyWeight, User
from app.routers.auth import get_current_user
from app.schemas import BodyWeightCreate, BodyWeightOut

router = APIRouter(prefix="/bodyweight", tags=["bodyweight"])


@router.get("", response_model=list[BodyWeightOut])
async def list_weights(
    limit: int = 60,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BodyWeight)
        .where(BodyWeight.user_id == current_user.id)
        .order_by(BodyWeight.measured_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("", response_model=BodyWeightOut, status_code=201)
async def add_weight(
    data: BodyWeightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = BodyWeight(user_id=current_user.id, **data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/{weight_id}", status_code=204)
async def delete_weight(
    weight_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BodyWeight).where(
            BodyWeight.id == weight_id,
            BodyWeight.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(entry)
    await db.commit()
