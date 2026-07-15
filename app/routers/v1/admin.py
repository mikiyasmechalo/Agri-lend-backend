from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserUpdate, UserAdminResponse, RoleAssignment
from app.services.auth import AuthService
from app.core.dependencies import require_roles
from app.models.bank import BankPartner

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    return await service.get_all_users()


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    try:
        user = await service.admin_create_user(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await service.log_audit(
        user_id=admin["sub"],
        action="CREATE_USER",
        resource="User",
        resource_id=str(user.id),
        details=f"Created user {data.email} with role {data.role_name}",
        ip=request.client.host if request.client else None,
    )
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role_name": data.role_name,
        "is_active": user.is_active,
        "locale": user.locale,
        "created_at": user.created_at,
    }


@router.patch("/users/{user_id}/role")
async def assign_role(
    user_id: str,
    data: RoleAssignment,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    try:
        user = await service.assign_role(user_id, data.role_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="ASSIGN_ROLE",
        resource="User",
        resource_id=user_id,
        details=f"Assigned role {data.role_name}",
        ip=request.client.host if request.client else None,
    )
    return {"detail": f"Role set to {data.role_name}"}


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    user = await service.update_user(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="UPDATE_USER",
        resource="User",
        resource_id=user_id,
        details="Updated profile fields",
        ip=request.client.host if request.client else None,
    )
    return {"detail": "User updated"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="DELETE_USER",
        resource="User",
        resource_id=user_id,
        ip=request.client.host if request.client else None,
    )


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    service = AuthService(db)
    user = await service.deactivate_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await service.log_audit(
        user_id=admin["sub"],
        action="DEACTIVATE_USER",
        resource="User",
        resource_id=user_id,
        ip=request.client.host if request.client else None,
    )
    return {"detail": "User deactivated"}


@router.post("/banks/{bank_id}/activate")
async def activate_bank(
    bank_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_roles("Platform Admin")),
):
    from sqlalchemy import select
    result = await db.execute(select(BankPartner).where(BankPartner.id == bank_id))
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    bank.is_active = True
    await db.flush()
    service = AuthService(db)
    await service.log_audit(
        user_id=admin["sub"],
        action="ACTIVATE_BANK",
        resource="BankPartner",
        resource_id=bank_id,
        ip=request.client.host if request.client else None,
    )
    return {"detail": f"Bank '{bank.bank_name}' activated"}
