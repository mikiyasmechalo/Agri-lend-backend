import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.db.base import Base
from app.core.security import hash_password
from app.models.auth import Role, User
from app.seed import ROLES

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as s:
        for name in ROLES:
            result = await s.execute(select(Role).where(Role.name == name))
            if not result.scalar_one_or_none():
                s.add(Role(name=name, description=f"{name} role"))
        await s.commit()
    async with session_factory() as s:
        yield s
        await s.rollback()


async def _get_role_by_name(session: AsyncSession, name: str) -> Role | None:
    result = await session.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


@pytest.fixture
async def admin_user(session: AsyncSession) -> User:
    role = await _get_role_by_name(session, "Platform Admin")
    if not role:
        role = Role(name="Platform Admin", description="Platform Admin role")
        session.add(role)
        await session.flush()
    user = User(
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=hash_password("password123"),
        role_id=role.id,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
async def farmer_role(session: AsyncSession) -> Role:
    role = await _get_role_by_name(session, "Farmer")
    if not role:
        role = Role(name="Farmer", description="Farmer role")
        session.add(role)
        await session.flush()
    return role


@pytest.fixture
async def farmer_user(session: AsyncSession, farmer_role: Role) -> User:
    user = User(
        email="farmer@test.com",
        full_name="Test Farmer",
        hashed_password=hash_password("password123"),
        role_id=farmer_role.id,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user
