import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config.config import settings
from app.database.session import Base, engine, get_db
from app.models.user import User, UserProfile
from app.auth.security import get_password_hash
from app.auth.deps import get_current_active_user_optional, RoleChecker
from app.api import auth
from app.api import members as members_api
from app.api import admin as admin_api

# Ensure required directories exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("uploads/progress_photos", exist_ok=True)


def seed_database(db: Session):
    """Seed default accounts for testing."""
    seeds = [
        {"email": "admin@physiqueiq.com",   "name": "System Administrator", "role": "admin",   "pw": "adminpassword"},
        {"email": "trainer@physiqueiq.com", "name": "Coach Alex Miller",    "role": "trainer", "pw": "trainerpassword"},
        {"email": "member@physiqueiq.com",  "name": "John Doe",             "role": "member",  "pw": "memberpassword"},
    ]
    for s in seeds:
        if not db.query(User).filter(User.email == s["email"]).first():
            user = User(
                email=s["email"],
                hashed_password=get_password_hash(s["pw"]),
                full_name=s["name"],
                role=s["role"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            profile_kwargs = {"user_id": user.id}
            if s["role"] == "member":
                profile_kwargs.update({
                    "age": 28, "gender": "male", "height": 180.0,
                    "weight": 82.0, "target_weight": 76.0,
                    "fitness_goal": "fat_loss", "experience_level": "intermediate",
                    "equipment_access": "gym", "dietary_preference": "veg",
                    "daily_activity_level": "moderately_active"
                })
            db.add(UserProfile(**profile_kwargs))
            db.commit()
            print(f"Seeded: {s['email']} / {s['pw']}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan-based startup/shutdown."""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Personal Fitness Coach and Smart Gym Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Mount static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Exception Handler ─────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        if exc.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
            return RedirectResponse(
                url=f"/login?error={exc.detail}",
                status_code=status.HTTP_303_SEE_OTHER
            )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router,       prefix=f"{settings.API_V1_STR}/auth",    tags=["Authentication"])
app.include_router(members_api.router, prefix=f"{settings.API_V1_STR}/members", tags=["Members"])
app.include_router(admin_api.router,   prefix=f"{settings.API_V1_STR}/admin",   tags=["Admin"])


# ── Helper: render template ───────────────────────────────────────────────────
def render(name: str, request: Request, ctx: dict = None):
    """Shorthand for TemplateResponse using new Starlette positional API."""
    context = ctx or {}
    context["request"] = request
    return templates.TemplateResponse(request=request, name=name, context=context)


# ── Web Views ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index_view(request: Request, current_user: User = Depends(get_current_active_user_optional)):
    if current_user:
        return RedirectResponse(url=f"/{current_user.role}", status_code=303)
    return render("index.html", request, {"current_user": None})


@app.get("/login", response_class=HTMLResponse)
def login_view(request: Request, current_user: User = Depends(get_current_active_user_optional)):
    if current_user:
        return RedirectResponse(url=f"/{current_user.role}", status_code=303)
    return render("login.html", request, {"current_user": None})


@app.get("/register", response_class=HTMLResponse)
def register_view(request: Request, current_user: User = Depends(get_current_active_user_optional)):
    if current_user:
        return RedirectResponse(url=f"/{current_user.role}", status_code=303)
    return render("register.html", request, {"current_user": None})


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard_view(request: Request, current_user: User = Depends(RoleChecker(["admin"])), db: Session = Depends(get_db)):
    try:
        # Pass live stats to the template on initial load
        total_members  = db.query(User).filter(User.role == "member").count()
        total_trainers = db.query(User).filter(User.role == "trainer").count()
        active_users   = db.query(User).filter(User.is_active == True).count()
        total_users    = db.query(User).count()
        print(f"DEBUG: Admin dashboard - stats loaded: members={total_members}, trainers={total_trainers}, active={active_users}, total={total_users}")
        result = render("admin_dashboard.html", request, {
            "current_user": current_user,
            "stats": {
                "total_members": total_members,
                "total_trainers": total_trainers,
                "active_users": active_users,
                "total_users": total_users,
            }
        })
        print("DEBUG: Admin dashboard rendered successfully")
        return result
    except Exception as e:
        print(f"ERROR in admin_dashboard_view: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.get("/trainer", response_class=HTMLResponse)
def trainer_dashboard_view(request: Request, current_user: User = Depends(RoleChecker(["trainer"])), db: Session = Depends(get_db)):
    # Pass all members to roster view
    members = db.query(User).filter(User.role == "member", User.is_active == True).all()
    return render("trainer_dashboard.html", request, {
        "current_user": current_user,
        "members": members,
    })


@app.get("/member", response_class=HTMLResponse)
def member_dashboard_view(request: Request, current_user: User = Depends(RoleChecker(["member"])), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    return render("member_dashboard.html", request, {
        "current_user": current_user,
        "profile": profile,
    })
