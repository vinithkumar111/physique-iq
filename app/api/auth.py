from fastapi import APIRouter, Depends, HTTPException, status, Response, Form
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Any
from app.database.session import get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserCreate, UserOut, Token
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.auth.deps import get_current_user
from app.config.config import settings

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """API endpoint to register a new user."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-create profile for user
    profile = UserProfile(user_id=new_user.id)
    db.add(profile)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login-json", response_model=Token)
def login_json(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Standard OAuth2 / JSON compatible token login."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(user.email, role=user.role, expires_delta=access_token_expires)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login-form")
def login_form(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
) -> Any:
    """Web login form endpoint that sets a secure cookie."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        # Redirect back to login with error parameter
        return RedirectResponse(url="/login?error=Invalid credentials", status_code=status.HTTP_303_SEE_OTHER)
    elif not user.is_active:
        return RedirectResponse(url="/login?error=Inactive user", status_code=status.HTTP_303_SEE_OTHER)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(user.email, role=user.role, expires_delta=access_token_expires)
    
    # Check roles and define redirect landing page
    if user.role == "admin":
        redirect_url = "/admin"
    elif user.role == "trainer":
        redirect_url = "/trainer"
    else:
        redirect_url = "/member"
        
    redirect = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    
    # Set the JWT cookie (httponly for security)
    redirect.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    return redirect

@router.get("/logout")
def logout() -> Any:
    """Logs out by clearing cookie and redirecting to login."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(get_current_user)) -> Any:
    """Retrieve the current logged in user."""
    return current_user
