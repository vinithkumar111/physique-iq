from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserProfileOut, UserProfileUpdate
from app.auth.deps import get_current_user, RoleChecker

router = APIRouter()

require_member = RoleChecker(["member", "admin", "trainer"])  # allow admin to test too


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/me/profile", response_model=UserProfileOut)
def get_my_profile(
    current_user: User = Depends(require_member),
    db: Session = Depends(get_db)
) -> Any:
    """Return current member's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/me/profile", response_model=UserProfileOut)
def update_my_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(require_member),
    db: Session = Depends(get_db)
) -> Any:
    """Update current member's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


# ── In-memory workout logs (Phase 1 — no DB table yet) ───────────────────────
_workout_logs: list = []
_nutrition_logs: list = []
_measurement_logs: list = []


class WorkoutLogCreate(BaseModel):
    date: str = Field(default_factory=lambda: date.today().isoformat())
    exercise: str
    sets: int = Field(ge=1)
    reps: int = Field(ge=1)
    weight_kg: Optional[float] = None
    notes: Optional[str] = None


class NutritionLogCreate(BaseModel):
    date: str = Field(default_factory=lambda: date.today().isoformat())
    meal_name: str
    calories: int = Field(ge=0)
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    notes: Optional[str] = None


class MeasurementCreate(BaseModel):
    date: str = Field(default_factory=lambda: date.today().isoformat())
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    notes: Optional[str] = None


class CoachMessage(BaseModel):
    message: str = Field(min_length=1)


@router.get("/me")
def get_my_account(
    current_user: User = Depends(require_member),
    db: Session = Depends(get_db),
) -> Any:
    """Return the current member's profile summary."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    profile_data = None
    if profile:
        profile_data = {
            "id": profile.id,
            "user_id": profile.user_id,
            "age": profile.age,
            "gender": profile.gender,
            "height": profile.height,
            "weight": profile.weight,
            "target_weight": profile.target_weight,
            "fitness_goal": profile.fitness_goal,
            "experience_level": profile.experience_level,
            "equipment_access": profile.equipment_access,
            "dietary_preference": profile.dietary_preference,
            "daily_activity_level": profile.daily_activity_level,
            "medical_conditions": profile.medical_conditions,
            "created_at": profile.created_at.strftime("%Y-%m-%d"),
            "updated_at": profile.updated_at.strftime("%Y-%m-%d"),
        }
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.strftime("%Y-%m-%d"),
        "profile": profile_data,
    }


@router.post("/me/coach")
def ai_coach(
    payload: CoachMessage,
    current_user: User = Depends(require_member),
) -> Any:
    """Return a simple coaching response for the member dashboard chat UI."""
    text = payload.message.lower()
    if any(term in text for term in ["fat loss", "weight loss", "lose weight"]):
        advice = "For fat loss, stay in a modest calorie deficit, keep protein high, and pair strength work with 2-3 cardio sessions each week."
    elif any(term in text for term in ["protein", "macro", "macros"]):
        advice = "Aim for roughly 1.6-2.2g of protein per kg of bodyweight and build meals around lean protein, vegetables, and quality carbs."
    elif any(term in text for term in ["muscle", "bulk", "gain"]):
        advice = "For muscle gain, keep a small calorie surplus and progress your lifts week to week while sleeping 7-9 hours nightly."
    elif any(term in text for term in ["sleep", "recovery"]):
        advice = "Recovery matters as much as training. Prioritise sleep, hydration, and lighter movement on rest days."
    elif any(term in text for term in ["workout", "plan"]):
        advice = "A simple beginner plan is 3 full-body sessions per week with compound lifts, controlled reps, and steady progression."
    else:
        advice = "Consistency beats intensity. Track your workouts, hit your protein goal, and recover well so your progress compounds over time."

    return {"message": advice, "coach_name": "PhysiqueIQ Coach"}


@router.post("/me/workouts", status_code=201)
def log_workout(
    entry: WorkoutLogCreate,
    current_user: User = Depends(require_member),
) -> Any:
    """Log a workout entry."""
    record = {"user_id": current_user.id, "user_name": current_user.full_name, **entry.model_dump(), "logged_at": datetime.utcnow().isoformat()}
    _workout_logs.append(record)
    return {"message": "Workout logged successfully", "entry": record}


@router.get("/me/workouts")
def get_my_workouts(current_user: User = Depends(require_member)) -> Any:
    """Return all workout logs for current user."""
    entries = [e for e in _workout_logs if e["user_id"] == current_user.id]
    return {"workouts": entries}


@router.post("/me/nutrition", status_code=201)
def log_nutrition(
    entry: NutritionLogCreate,
    current_user: User = Depends(require_member),
) -> Any:
    """Log a nutrition entry."""
    record = {"user_id": current_user.id, **entry.model_dump(), "logged_at": datetime.utcnow().isoformat()}
    _nutrition_logs.append(record)
    return {"message": "Nutrition logged successfully", "entry": record}


@router.get("/me/nutrition")
def get_my_nutrition(current_user: User = Depends(require_member)) -> Any:
    """Return all nutrition logs for current user."""
    entries = [e for e in _nutrition_logs if e["user_id"] == current_user.id]
    return {"nutrition": entries}


@router.post("/me/measurements", status_code=201)
def log_measurement(
    entry: MeasurementCreate,
    current_user: User = Depends(require_member),
) -> Any:
    """Log a body measurement entry."""
    record = {"user_id": current_user.id, **entry.model_dump(), "logged_at": datetime.utcnow().isoformat()}
    _measurement_logs.append(record)
    return {"message": "Measurement logged successfully", "entry": record}


@router.get("/me/measurements")
def get_my_measurements(current_user: User = Depends(require_member)) -> Any:
    """Return all measurements for current user."""
    entries = [e for e in _measurement_logs if e["user_id"] == current_user.id]
    return {"measurements": entries}
