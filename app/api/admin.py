from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.database.session import get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserOut
from app.auth.deps import RoleChecker
from app.auth.security import get_password_hash

router = APIRouter()
require_admin = RoleChecker(["admin"])

_workout_templates: list = []
_diet_templates: list = []


class WorkoutTemplateCreate(BaseModel):
    plan_name: str
    member: Optional[str] = None
    difficulty: str = "intermediate"
    duration_min: int = 60
    exercises: str
    notes: Optional[str] = None


class DietTemplateCreate(BaseModel):
    plan_name: str
    member: Optional[str] = None
    calories: int
    protein_g: int
    carbs_g: Optional[int] = None
    fat_g: Optional[int] = None
    meals: str
    restrictions: Optional[str] = None


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Return platform-level aggregate stats."""
    total_members  = db.query(User).filter(User.role == "member").count()
    total_trainers = db.query(User).filter(User.role == "trainer").count()
    total_admins   = db.query(User).filter(User.role == "admin").count()
    active_users   = db.query(User).filter(User.is_active == True).count()
    total_users    = db.query(User).count()

    return {
        "total_members": total_members,
        "total_trainers": total_trainers,
        "total_admins": total_admins,
        "active_users": active_users,
        "total_users": total_users,
    }


# ── User Listing ──────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    role: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """List all users, optionally filtered by role."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.order_by(User.created_at.desc()).all()

    return {
        "users": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.strftime("%Y-%m-%d"),
            }
            for u in users
        ]
    }


# ── Create User ───────────────────────────────────────────────────────────────

class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(default="member", pattern="^(member|trainer|admin)$")
    password: str = Field(min_length=6)


@router.post("/users", status_code=201)
def create_user(
    user_in: AdminUserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Admin creates a new user (any role)."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        role=user_in.role,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    profile = UserProfile(user_id=new_user.id)
    db.add(profile)
    db.commit()

    return {
        "message": f"{user_in.role.title()} account created",
        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "email": new_user.email,
            "role": new_user.role,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at.strftime("%Y-%m-%d"),
        },
    }


# ── Toggle Active ─────────────────────────────────────────────────────────────

@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Toggle a user's is_active status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    user.is_active = not user.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}", "is_active": user.is_active}


# ── Delete User ───────────────────────────────────────────────────────────────

@router.delete("/users/{user_id}", status_code=200)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Permanently delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


# ── Trainer Plan Templates ──────────────────────────────────────────────────

@router.get("/trainer-plans")
def list_trainer_plans() -> Any:
    """Return workout and diet templates created by trainers."""
    return {
        "workout_templates": _workout_templates,
        "diet_templates": _diet_templates,
    }


@router.post("/trainer-plans/workouts", status_code=201)
def create_workout_template(payload: WorkoutTemplateCreate) -> Any:
    record = {
        "id": len(_workout_templates) + 1,
        "plan_name": payload.plan_name,
        "member": payload.member,
        "difficulty": payload.difficulty,
        "duration_min": payload.duration_min,
        "exercises": payload.exercises,
        "notes": payload.notes,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    _workout_templates.insert(0, record)
    return {"message": "Workout template saved", "template": record}


@router.post("/trainer-plans/diets", status_code=201)
def create_diet_template(payload: DietTemplateCreate) -> Any:
    record = {
        "id": len(_diet_templates) + 1,
        "plan_name": payload.plan_name,
        "member": payload.member,
        "calories": payload.calories,
        "protein_g": payload.protein_g,
        "carbs_g": payload.carbs_g,
        "fat_g": payload.fat_g,
        "meals": payload.meals,
        "restrictions": payload.restrictions,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    _diet_templates.insert(0, record)
    return {"message": "Diet template saved", "template": record}
