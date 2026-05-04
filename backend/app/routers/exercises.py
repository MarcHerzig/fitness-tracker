import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ExerciseTemplate, User
from app.routers.auth import get_current_user
from app.schemas import ExerciseTemplateCreate, ExerciseTemplateOut, ExerciseTemplateUpdate

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseTemplateOut])
async def list_exercises(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ExerciseTemplate)
        .where(ExerciseTemplate.user_id == current_user.id, ExerciseTemplate.is_active == True)
        .order_by(ExerciseTemplate.sort_order, ExerciseTemplate.name)
    )
    return result.scalars().all()


@router.post("", response_model=ExerciseTemplateOut, status_code=201)
async def create_exercise(
    data: ExerciseTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = ExerciseTemplate(user_id=current_user.id, **data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.patch("/{exercise_id}", response_model=ExerciseTemplateOut)
async def update_exercise(
    exercise_id: uuid.UUID,
    data: ExerciseTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ExerciseTemplate).where(
            ExerciseTemplate.id == exercise_id,
            ExerciseTemplate.user_id == current_user.id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ExerciseTemplate).where(
            ExerciseTemplate.id == exercise_id,
            ExerciseTemplate.user_id == current_user.id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Not found")
    template.is_active = False
    await db.commit()
