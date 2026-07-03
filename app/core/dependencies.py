from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import decode_token
from app.core.config import settings

bearer_scheme = HTTPBearer()


class RBACException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload


def require_roles(*roles: str):
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in roles:
            raise RBACException()
        return current_user

    return role_checker
