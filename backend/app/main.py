from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app import auth as auth_utils
from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.models import ExerciseTemplate, User
from app.routers import activities, auth, exercises, bodyweight, stats


MARC_EXERCISES = [
    {"name": "Bizeps", "weight_kg": None, "is_duration_based": False, "sort_order": 0},
    {"name": "Trizeps", "weight_kg": None, "is_duration_based": False, "sort_order": 1},
    {"name": "Bauch Crunch", "weight_kg": None, "is_duration_based": False, "sort_order": 2},
    {"name": "Schulterdrücken", "weight_kg": None, "is_duration_based": False, "sort_order": 3},
    {"name": "Lat", "weight_kg": None, "is_duration_based": False, "sort_order": 4},
    {"name": "Rudern", "weight_kg": None, "is_duration_based": False, "sort_order": 5},
    {"name": "Laufen", "weight_kg": None, "is_duration_based": True, "sort_order": 6},
    {"name": "Liegestützen", "weight_kg": None, "is_duration_based": False, "sort_order": 7},
    {"name": "Klimmzüge", "weight_kg": None, "is_duration_based": False, "sort_order": 8},
]


async def seed_users():
    async with AsyncSessionLocal() as db:
        for username, email, password in [
            ("marc", "marc@fitness.local", "marc123"),
            ("pia", "pia@fitness.local", "pia123"),
        ]:
            result = await db.execute(select(User).where(User.username == username))
            if not result.scalar_one_or_none():
                user = User(
                    username=username,
                    email=email,
                    password_hash=auth_utils.hash_password(password),
                )
                db.add(user)
                await db.flush()

                if username == "marc":
                    for ex in MARC_EXERCISES:
                        db.add(ExerciseTemplate(user_id=user.id, **ex))

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_users()
    yield


app = FastAPI(title="Fitness Tracker API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(activities.router)
app.include_router(exercises.router)
app.include_router(bodyweight.router)
app.include_router(stats.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
