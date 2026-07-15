from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserUpdate, UserResponse,
)
from app.services.auth import AuthService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    try:
        user = await service.register_user(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.authenticate(data.email, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials or account deactivated")
    return TokenResponse(access_token=result[1], refresh_token=result[2])


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.refresh_access_token(data.refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return TokenResponse(access_token=result[0], refresh_token=result[1])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.get_user_by_id(current_user.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = AuthService(db)
    user = await service.update_user(current_user["sub"], data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
