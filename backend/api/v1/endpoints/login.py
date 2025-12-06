from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from backend.schemas import loginIn_pydantic, UserIn_Pydantic, User_Pydantic
from backend.models import User
from backend.security import get_password_hash, verify_password, create_access_token
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordRequestForm
from backend.core import rt
login = APIRouter()


"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
定义了 OAuth2PasswordBearer，它会从请求的 Authorization 头中提取 Bearer 令牌。
之后每次访问页面都要携带这个token去数据库里边查。
"""


@login.post("/login", status_code=200)
async def user_login(form_data: OAuth2PasswordRequestForm = Depends()):
    # try:
    existing_user = await User.filter(name=form_data.username).first()
    if verify_password(form_data.password, existing_user.password_hash):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )

        return {
            "data": "登陆成功",
            "access_token": access_token,
            "token_type": "bearer",
        }
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码不正确，登录失败")
    # except Exception:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="登录失败")


@login.post("/user", status_code=200)
async def reg_user(user: UserIn_Pydantic,avatar="avatar1.PNG"):
    # 开始验证数据库中是否存在用户名
    # 前端判断验证密码是否符合规格
    # 向数据库插入数据，注册成功，但是未激活状态，返回状态码200表明注册成功
    existing_user = await User.filter(name=user.name).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="用户名已存在")

    # 在这里进行密码的加密
    password_hash = get_password_hash(user.password_hash)
    user_data = user.dict(exclude={"password_hash"})
    user_data["password_hash"] = password_hash
    await User.create(**user_data,avatar=avatar)

    return {
        "message": "注册成功，请前往邮箱激活账号",
        "user": "name",
        "status": "active"
    }
