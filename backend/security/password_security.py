from datetime import timedelta, datetime, timezone
from typing import Union, Annotated
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from backend.config import SECRET_KEY, ALGORITHM
from passlib.context import CryptContext
from jwt.exceptions import InvalidTokenError
from backend.core import rt
from backend.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 哈希加密是不可逆的，所以即使黑客获取了哈希值，他们也无法直接从中恢复出用户的密码。这与对称加密（比如 AES）不同，后者需要保护加密密钥。如果密钥丢失或泄露，数据就会被解密。

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# def authenticate_user(fake_db, username: str, password: str):

# 创建jwt的token
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 创建依赖，会自动验证请求头中的jwt令牌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login",scheme_name="Bearer")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name = payload.get("sub")
        if user_name is None:
            raise credentials_exception
            # 2. 验证过期时间
        expire = payload.get("exp")
        if expire is None or expire < datetime.utcnow().timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期",
            )
    except InvalidTokenError:
        raise credentials_exception

    key = f"user:{user_name}"
    # 先去redis里找，然后再去mysql里把那个给取出来存进redis里
    try:
        user_data = rt.hget(key)
        if user_data:
            return user_data
    except Exception:
        raise credentials_exception
    finally:
        user_data = await User.filter(name=user_name).first()
        if user_data:
            data = {
                "id": user_data.id,
                "name": user_data.name,
            }
            rt.hmset(key, data)
            rt.expire(key, 3600)
            return data
        else:
            raise credentials_exception
