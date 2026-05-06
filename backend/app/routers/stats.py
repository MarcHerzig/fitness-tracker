from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Activity, BodyWeight, User
from app.routers.auth import get_current_user
from app.schemas import DashboardOut, DayStars, MonthStars, UserDashboard, BodyWeightOut

router = APIRouter(prefix="/stats", tags=["stats"])

MONTHS_DE = ["", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
             "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def _month_label(year: int, month: int) -> str:
    return f"{MONTHS_DE[month]} {str(year)[2:]}"


async def build_user_dashboard(db: AsyncSession, user: User) -> UserDashboard:
    today = date.today()
    month_start = date(today.year, today.month, 1)

    # Start of 6-month window (first day, 5 months back)
    six_months_ago = month_start
    for _ in range(5):
        if six_months_ago.month == 1:
            six_months_ago = date(six_months_ago.year - 1, 12, 1)
        else:
            six_months_ago = date(six_months_ago.year, six_months_ago.month - 1, 1)

    # Single query covering all 6 months
    result = await db.execute(
        select(Activity.activity_date, Activity.stars, Activity.subtype, Activity.distance_km)
        .where(Activity.user_id == user.id, Activity.activity_date >= six_months_ago)
    )
    all_rows = result.all()

    # Accumulate per-day: stars (capped at 3) and cycling km
    per_day: dict[date, dict] = defaultdict(lambda: {"stars": 0, "cycling_km": 0.0})
    for d, s, subtype, dist_km in all_rows:
        per_day[d]["stars"] = min(per_day[d]["stars"] + s, 3)
        if subtype == "cycling" and dist_km:
            per_day[d]["cycling_km"] += dist_km

    # Two-week summary
    two_weeks_ago = today - timedelta(days=13)
    today_stars = per_day[today]["stars"] if today in per_day else 0
    two_week_total_stars = sum(v["stars"] for d, v in per_day.items() if d >= two_weeks_ago)
    two_week_training_days = sum(1 for d, v in per_day.items() if d >= two_weeks_ago and v["stars"] > 0)

    # Current month: day 1 through today
    month_days = [
        DayStars(date=date(today.year, today.month, day_num),
                 stars=per_day.get(date(today.year, today.month, day_num), {}).get("stars", 0))
        for day_num in range(1, today.day + 1)
    ]

    # 6-month aggregation
    month_data: dict[tuple, dict] = {}
    for d, data in per_day.items():
        key = (d.year, d.month)
        if key not in month_data:
            month_data[key] = {"stars": 0, "training_days": 0, "cycling_km": 0.0}
        month_data[key]["stars"] += data["stars"]
        if data["stars"] > 0:
            month_data[key]["training_days"] += 1
        month_data[key]["cycling_km"] += data["cycling_km"]

    monthly_stars = []
    cur = six_months_ago
    for _ in range(6):
        key = (cur.year, cur.month)
        data = month_data.get(key, {"stars": 0, "training_days": 0, "cycling_km": 0.0})
        monthly_stars.append(MonthStars(
            year=cur.year,
            month=cur.month,
            label=_month_label(cur.year, cur.month),
            stars=data["stars"],
            training_days=data["training_days"],
            cycling_km=round(data["cycling_km"], 1),
        ))
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)

    # Body weight
    bw_result = await db.execute(
        select(BodyWeight)
        .where(BodyWeight.user_id == user.id)
        .order_by(BodyWeight.measured_at.desc())
        .limit(60)
    )
    weights = bw_result.scalars().all()
    last_weight = weights[0].weight_kg if weights else None

    return UserDashboard(
        user_id=user.id,
        username=user.username,
        today_stars=today_stars,
        month=month_days,
        two_week_total_stars=two_week_total_stars,
        two_week_training_days=two_week_training_days,
        last_weight=last_weight,
        weight_history=[BodyWeightOut.model_validate(w) for w in reversed(weights)],
        monthly_stars=monthly_stars,
    )


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.is_active == True))
    all_users = result.scalars().all()

    marc = next((u for u in all_users if u.username.lower() == "marc"), None)
    pia = next((u for u in all_users if u.username.lower() == "pia"), None)

    return DashboardOut(
        marc=await build_user_dashboard(db, marc) if marc else None,
        pia=await build_user_dashboard(db, pia) if pia else None,
    )
