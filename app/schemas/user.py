from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

# Profile schemas
class UserProfileBase(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    height: Optional[float] = Field(None, ge=30, le=300) # in cm
    weight: Optional[float] = Field(None, ge=10, le=500) # in kg
    target_weight: Optional[float] = Field(None, ge=10, le=500)
    fitness_goal: str = "fat_loss"
    experience_level: str = "beginner"
    equipment_access: str = "gym"
    dietary_preference: str = "veg"
    daily_activity_level: str = "moderately_active"
    medical_conditions: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileOut(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "member"

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    profile: Optional[UserProfileOut] = None


# Authentication tokens
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
