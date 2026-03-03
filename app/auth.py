import os
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi_azure_auth.user import User
from . import models, schemas, database

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
# Security Rule: ALWAYS provide SECRET_KEY in production.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("FATAL: SECRET_KEY environment variable is not set. This is required for security.")

AUTH_MODE = os.getenv("AUTH_MODE", "LOCAL").upper()  # LOCAL or AZURE
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Special marker for users that MUST NOT use local password auth (e.g. Azure users)
EXTERNAL_AUTH_MARKER = "!!!EXTERNAL_AUTH_ONLY!!!"

# --- AZURE GROUPS ---
AZURE_OPERATORS_GROUP_ID = os.getenv("AZURE_OPERATORS_GROUP_ID", "")
AZURE_VIEWERS_GROUP_ID = os.getenv("AZURE_VIEWERS_GROUP_ID", "")

# --- ROLE CONSTANTS ---
ROLE_VIEWER = "Viewer"
ROLE_OPERATOR = "Operator"
ROLE_ADMIN = "Admin"

# --- LOCAL AUTH CONFIG ---
# Fix for passlib/bcrypt > 4.0 issue
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- AZURE AUTH CONFIG ---
# Only configure if in AZURE mode to avoid startup errors if env vars missing
azure_scheme = None
if AUTH_MODE == "AZURE":
    azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id=os.getenv("AZURE_CLIENT_ID", ""),
        tenant_id=os.getenv("AZURE_TENANT_ID", ""),
        scopes={
            f"api://{os.getenv('AZURE_CLIENT_ID')}/user_impersonation": "user_impersonation",
        }
    )

def _get_azure_user_stub():
    return None

azure_scheme_dep = azure_scheme if azure_scheme else _get_azure_user_stub

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def _pre_hash_password(password: str) -> str:
    """
    Pre-hashes password using SHA-256 and base64 encodes it.
    This bypasses bcrypt's 72-byte limit while maintaining security.
    """
    return base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest()).decode('ascii')


def verify_password(plain_password, hashed_password):
    if hashed_password == EXTERNAL_AUTH_MARKER:
        return False # External users cannot use local passwords
    return pwd_context.verify(_pre_hash_password(plain_password), hashed_password)


def get_password_hash(password):
    return pwd_context.hash(_pre_hash_password(password))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    azure_user: Optional[User] = Depends(azure_scheme_dep),
    db: Session = Depends(database.get_db)
):
    if AUTH_MODE == "AZURE":
        if not azure_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Azure AD authentication required",
            )
        
        # Map Azure groups to roles
        groups = azure_user.claims.get("groups", [])
        role = ROLE_VIEWER # Default
        
        if AZURE_OPERATORS_GROUP_ID in groups:
            role = ROLE_OPERATOR # Map to Operator as requested
        elif AZURE_VIEWERS_GROUP_ID in groups:
            role = ROLE_VIEWER
        else:
            # If user is in neither group, they aren't authorized for this app
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this application (not in approved Azure groups)"
            )

        # JIT Provisioning / Shadow Account
        username = azure_user.claims.get("preferred_username") or azure_user.claims.get("upn")
        if not username:
             raise HTTPException(status_code=400, detail="Azure token missing username claim")

        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            # Create shadow account
            user = models.User(
                username=username,
                hashed_password=EXTERNAL_AUTH_MARKER, # Cannot be verified by local auth
                role=role,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update role from Azure if it changed
            if user.role != role:
                user.role = role
                db.commit()
                db.refresh(user)
                
        return user

    # LOCAL MODE
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", ROLE_VIEWER)
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_operator_user(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role not in [ROLE_OPERATOR, ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires Operator or Admin role"
        )
    return current_user


async def get_admin_user(current_user: models.User = Depends(get_current_active_user)):
    if current_user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires Admin role"
        )
    return current_user


