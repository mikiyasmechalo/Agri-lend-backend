from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models.auth import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[dict])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles("Platform Admin")),
):
    from sqlalchemy import select
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{"id": str(u.id), "email": u.email, "full_name": u.full_name, "is_active": u.is_active} for u in users]
