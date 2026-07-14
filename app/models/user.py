from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="member", nullable=False)  # admin, trainer, member
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # We will build other relationships incrementally
    # workouts = relationship("WorkoutLog", back_populates="user")
    # attendance = relationship("Attendance", back_populates="user")
    # measurements = relationship("BodyMeasurement", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    target_weight = Column(Float, nullable=True)  # in kg
    fitness_goal = Column(String, default="fat_loss", nullable=False)  # fat_loss, muscle_gain, maintenance, strength
    experience_level = Column(String, default="beginner", nullable=False)  # beginner, intermediate, advanced
    equipment_access = Column(String, default="gym", nullable=False)  # gym, home, dumbbells
    dietary_preference = Column(String, default="veg", nullable=False)  # veg, non_veg, eggitarian
    daily_activity_level = Column(String, default="moderately_active", nullable=False)  # sedentary, active, very_active
    medical_conditions = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="profile")
