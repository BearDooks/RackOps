from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import os
import contextlib
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from .routers import sites, racks, devices, users, pages, audit_logs
from .database import engine, Base, get_db, SessionLocal
from . import models, auth, schemas, crud

# Create tables (Note: For advanced migrations, use Alembic)
Base.metadata.create_all(bind=engine)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Seed default admin user if database is empty and in LOCAL mode
    # This allows for a seamless "out of the box" experience while staying secure in Azure mode.
    seed_requested = os.getenv("SEED_DEFAULT_ADMIN", "auto").lower()
    
    should_seed = False
    if seed_requested == "true":
        should_seed = True
    elif seed_requested == "auto" and auth.AUTH_MODE == "LOCAL":
        should_seed = True
        
    if should_seed:
        db = SessionLocal()
        try:
            user_count = db.query(models.User).count()
            if user_count == 0:
                print("First run detected: No users found in database.")
                print("Creating default admin user 'admin'...")
                admin_user = schemas.UserCreate(
                    username="admin",
                    password="adminpassword",
                    role=auth.ROLE_ADMIN,
                    is_active=True
                )
                crud.create_user(db, admin_user)
                print("Success! Login with admin / adminpassword and change your password immediately.")
        finally:
            db.close()
    yield

app = FastAPI(title="RackOps", lifespan=lifespan)

# CORS Middleware (Restrictive by default)
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000")
allowed_origins = allowed_origins_raw.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include UI Routes
app.include_router(pages.router)

# Include API Routes
app.include_router(sites.router)
app.include_router(racks.router)
app.include_router(devices.router)
app.include_router(users.router)
app.include_router(audit_logs.router)


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: auth.OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if auth.AUTH_MODE == "AZURE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled. Please use Azure AD login.",
        )
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user
