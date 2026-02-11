import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from backend.config import ALGORITHM, SECRET_KEY


def _extract_user_id_from_token(token: str) -> int:
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="凭证无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decoded.get("uid")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="凭证无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
