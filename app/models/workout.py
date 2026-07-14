from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class Exercise(Base):
    """Master exercise library - admin seeded."""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=False)          # chest, back, legs, shoulders, arms, core, cardio
    muscle_group = Column(String, nullable=False)       # primary muscle targeted
    secondary_muscles = Column(String, nullable=True)  # comma-separated
    equipment = Column(String, nullable=True)          # barbell, dumbbell, machine, bodyweight
    movement_type = Column(String, nullable=True)      # compound, isolation
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkoutPlan(Base):
    """Predefined workout plan created by trainers or AI."""
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(String, nullable=False)               # fat_loss, muscle_gain, strength, maintenance
    level = Column(String, nullable=False)              # beginner, intermediate, advanced
    days_per_week = Column(Integer, default=3)
    duration_weeks = Column(Integer, default=12)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", foreign_keys=[created_by])
    logs = relationship("WorkoutLog", back_populates="plan")


class WorkoutLog(Base):
    """A single completed workout session logged by a member."""
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False, default="Custom Workout")
    notes = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    rpe = Column(Float, nullable=True)                  # Rate of Perceived Exertion 1-10
    total_volume = Column(Float, nullable=True)         # kg * reps summed across all sets
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    plan = relationship("WorkoutPlan", back_populates="logs")
    sets = relationship("WorkoutSet", back_populates="workout_log", cascade="all, delete-orphan")


class WorkoutSet(Base):
    """An individual set within a WorkoutLog."""
    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True, index=True)
    workout_log_id = Column(Integer, ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True)
    exercise_name = Column(String, nullable=False)       # Stored directly for denormalization
    set_number = Column(Integer, nullable=False, default=1)
    reps = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    duration_seconds = Column(Integer, nullable=True)   # For timed exercises
    distance_km = Column(Float, nullable=True)          # For cardio
    one_rm_estimate = Column(Float, nullable=True)      # Calculated Epley 1RM
    is_personal_record = Column(Boolean, default=False)
    notes = Column(String, nullable=True)

    workout_log = relationship("WorkoutLog", back_populates="sets")
    exercise = relationship("Exercise", foreign_keys=[exercise_id])
