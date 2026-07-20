import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth import AuthService
from app.schemas.auth import UserCreate
from app.core.security import verify_password


class TestAuthService:
    async def test_register_user(self, session: AsyncSession, farmer_role):
        service = AuthService(session)
        data = UserCreate(
            email="newfarmer@test.com",
            password="securePass1!",
            full_name="New Farmer",
            role_name="Farmer",
            phone_number="+251911111111",
        )
        user = await service.register_user(data)
        assert user.email == "newfarmer@test.com"
        assert user.full_name == "New Farmer"
        assert user.is_active is True
        assert verify_password("securePass1!", user.hashed_password)

    async def test_register_duplicate_email(self, session: AsyncSession, farmer_role):
        from sqlalchemy.exc import IntegrityError
        service = AuthService(session)
        data = UserCreate(
            email="dup@test.com", password="pass123", full_name="Dup", role_name="Farmer"
        )
        await service.register_user(data)
        with pytest.raises(IntegrityError):
            await service.register_user(data)

    async def test_register_invalid_role(self, session: AsyncSession):
        service = AuthService(session)
        data = UserCreate(
            email="badrole@test.com", password="pass123", full_name="Bad", role_name="NonExistent"
        )
        with pytest.raises(ValueError, match="Role 'NonExistent' not found"):
            await service.register_user(data)

    async def test_authenticate_success(self, session: AsyncSession, farmer_user):
        service = AuthService(session)
        result = await service.authenticate("farmer@test.com", "password123")
        assert result is not None
        user, access, refresh = result
        assert user.email == "farmer@test.com"
        assert access is not None
        assert refresh is not None

    async def test_authenticate_wrong_password(self, session: AsyncSession, farmer_user):
        service = AuthService(session)
        result = await service.authenticate("farmer@test.com", "wrongpassword")
        assert result is None

    async def test_authenticate_inactive_user(self, session: AsyncSession, farmer_user):
        farmer_user.is_active = False
        await session.flush()
        service = AuthService(session)
        result = await service.authenticate("farmer@test.com", "password123")
        assert result is None
