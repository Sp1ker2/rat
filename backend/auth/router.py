"""Authentication endpoints"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.models import LoginRequest, AdminToken
from backend.auth.utils import verify_password, create_access_token, decode_access_token
from backend.config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/login", response_model=AdminToken)
async def login(request: LoginRequest):
    """Admin login"""
    print(f"DEBUG: Login attempt - username: {request.username}, expected: {ADMIN_USERNAME}")
    
    # Verify credentials
    if request.username != ADMIN_USERNAME:
        print(f"DEBUG: Username mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    print(f"DEBUG: Verifying password, hash: {ADMIN_PASSWORD_HASH[:30]}...")
    password_valid = verify_password(request.password, ADMIN_PASSWORD_HASH)
    print(f"DEBUG: Password valid: {password_valid}")
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": request.username})
    print(f"DEBUG: Token created successfully")
    
    return AdminToken(access_token=access_token)


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Admin logout (client-side token removal)"""
    return {"message": "Logged out successfully"}


@router.get("/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {"username": payload.get("sub"), "valid": True}


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current authenticated admin"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return username

