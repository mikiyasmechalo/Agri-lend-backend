from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.auth import User, Role
from app.schemas.auth import UserCreate
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, data: UserCreate) -> User:
        result = await self.db.execute(select(Role).where(Role.name == data.role_name))
        role = result.scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{data.role_name}' not found")

        user = User(
            email=data.email,
            phone_number=data.phone_number,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role_id=role.id,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate(self, email: str, password: str) -> tuple[User, str, str] | None:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        access = create_access_token(str(user.id), user.role.name)
        refresh = create_refresh_token(str(user.id))
        return user, access, refresh

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
