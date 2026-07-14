from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class Food(Base):
    """Master food database - seeded with common Indian foods."""
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=True)          # grain, protein, vegetable, fruit, dairy, fat
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False, default=0)
    carbs_per_100g = Column(Float, nullable=False, default=0)
    fat_per_100g = Column(Float, nullable=False, default=0)
    fiber_per_100g = Column(Float, nullable=True, default=0)
    is_vegetarian = Column(Boolean, default=True)
    serving_size_g = Column(Float, nullable=True, default=100)
    serving_description = Column(String, nullable=True)  # e.g. "1 cup", "1 roti"


class NutritionLog(Base):
    """A daily nutrition log entry container for a member."""
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(DateTime, nullable=False)
    total_calories = Column(Float, nullable=True, default=0)
    total_protein = Column(Float, nullable=True, default=0)
    total_carbs = Column(Float, nullable=True, default=0)
    total_fat = Column(Float, nullable=True, default=0)
    total_fiber = Column(Float, nullable=True, default=0)
    water_ml = Column(Float, nullable=True, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    meals = relationship("MealEntry", back_populates="nutrition_log", cascade="all, delete-orphan")


class MealEntry(Base):
    """A single food item logged within a NutritionLog."""
    __tablename__ = "meal_entries"

    id = Column(Integer, primary_key=True, index=True)
    nutrition_log_id = Column(Integer, ForeignKey("nutrition_logs.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="SET NULL"), nullable=True)
    food_name = Column(String, nullable=False)          # Denormalized for flexibility
    meal_type = Column(String, nullable=False, default="lunch")  # breakfast, lunch, dinner, snack
    quantity_g = Column(Float, nullable=False, default=100)
    calories = Column(Float, nullable=False, default=0)
    protein = Column(Float, nullable=False, default=0)
    carbs = Column(Float, nullable=False, default=0)
    fat = Column(Float, nullable=False, default=0)
    logged_at = Column(DateTime, default=datetime.utcnow)

    nutrition_log = relationship("NutritionLog", back_populates="meals")
    food = relationship("Food", foreign_keys=[food_id])
