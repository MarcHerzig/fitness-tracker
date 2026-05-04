import csv
import io
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Activity, EnduranceData, Exercise, ExerciseSet, User
from app.routers.auth import get_current_user
from app.schemas import ActivityCreate, ActivityOut

router = APIRouter(prefix="/activities", tags=["activities"])


def _build_activity_out(activity: Activity) -> ActivityOut:
    out = ActivityOut(
        id=activity.id,
        type=activity.type,
        subtype=activity.subtype,
        activity_date=activity.activity_date,
        duration_minutes=activity.duration_minutes,
        notes=activity.notes,
        created_at=activity.created_at,
        distance_km=activity.endurance_data.distance_km if activity.endurance_data else None,
        exercises=[
            {
                "id": ex.id,
                "name": ex.name,
                "order": ex.order,
                "sets": [
                    {"id": s.id, "set_number": s.set_number, "reps": s.reps, "weight_kg": s.weight_kg, "rest_seconds": s.rest_seconds}
                    for s in ex.sets
                ],
            }
            for ex in activity.exercises
        ],
    )
    return out


@router.get("", response_model=list[ActivityOut])
async def list_activities(
    skip: int = 0,
    limit: int = Query(50, le=200),
    type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Activity)
        .options(selectinload(Activity.endurance_data), selectinload(Activity.exercises).selectinload(Exercise.sets))
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.activity_date.desc(), Activity.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if type:
        q = q.where(Activity.type == type)
    result = await db.execute(q)
    return [_build_activity_out(a) for a in result.scalars().all()]


@router.post("", response_model=ActivityOut, status_code=201)
async def create_activity(
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    activity = Activity(
        user_id=current_user.id,
        type=data.type,
        subtype=data.subtype,
        activity_date=data.activity_date,
        duration_minutes=data.duration_minutes,
        notes=data.notes,
    )
    db.add(activity)
    await db.flush()

    if data.type == "endurance" and data.distance_km is not None:
        db.add(EnduranceData(activity_id=activity.id, distance_km=data.distance_km))

    for ex_data in data.exercises:
        exercise = Exercise(activity_id=activity.id, name=ex_data.name, order=ex_data.order)
        db.add(exercise)
        await db.flush()
        for s in ex_data.sets:
            db.add(ExerciseSet(exercise_id=exercise.id, **s.model_dump()))

    await db.commit()

    result = await db.execute(
        select(Activity)
        .options(selectinload(Activity.endurance_data), selectinload(Activity.exercises).selectinload(Exercise.sets))
        .where(Activity.id == activity.id)
    )
    return _build_activity_out(result.scalar_one())


@router.get("/{activity_id}", response_model=ActivityOut)
async def get_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Activity)
        .options(selectinload(Activity.endurance_data), selectinload(Activity.exercises).selectinload(Exercise.sets))
        .where(Activity.id == activity_id, Activity.user_id == current_user.id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return _build_activity_out(activity)


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id, Activity.user_id == current_user.id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    await db.delete(activity)
    await db.commit()


@router.get("/export/csv")
async def export_csv(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Activity)
        .options(selectinload(Activity.endurance_data))
        .where(Activity.user_id == current_user.id)
        .order_by(Activity.activity_date.desc())
    )
    activities = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "type", "subtype", "duration_minutes", "distance_km", "notes"])
    for a in activities:
        writer.writerow([
            a.activity_date,
            a.type,
            a.subtype,
            a.duration_minutes,
            a.endurance_data.distance_km if a.endurance_data else "",
            a.notes or "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fitness_export.csv"},
    )
