"""
开始实现jwt令牌
"""

from fastapi import APIRouter
from backend.schemas import UserIn_Pydantic
from backend.schemas import User_Pydantic
from backend.models import User
from fastapi import HTTPException, status
from starlette.responses import JSONResponse
from backend.security import get_password_hash, verify_password
from fastapi import APIRouter, Depends
from backend.security.password_security import get_current_user

user = APIRouter(dependencies=[Depends(get_current_user)])


@user.get("/user")
async def get_user(user: dict = Depends(get_current_user)):
    result = await User.get(name=user.get("name"))
    user_data = await User_Pydantic.from_tortoise_orm(result)
    return user_data.dict(include={"id", "name", "avatar"})




@user.put("/user/name")
async def put_name(name: str, user: dict = Depends(get_current_user)):
    try:
        exist = await User.filter(name=name).exists()
        if exist:
            return {"msg": "用户名重复"}

        user = await User.get(id=user.get("id"))
        user.name = name
        await user.save()
        return {"msg": "用户名修改成功"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名修改失败")


@user.put("/password")
async def update_user(fast_password: str, next_password: str, user: dict = Depends(get_current_user)):
    try:
        result = await User.filter(id=user.get("id")).first()
        password_hash = result.password_hash
        if verify_password(fast_password, password_hash):
            result.password_hash = get_password_hash(next_password)
            await result.save()
            return JSONResponse(status_code=status.HTTP_200_OK, content={
                "message": "修改密码成功",
                "user_name": result.name,
                "status": 200,
            })
        else:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={
                "message": "输入的原始密码错误",
            })
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")


@user.put("/user/email")
async def change_email(email: str, user: dict = Depends(get_current_user)):
    result = await User.get(id=user.get("id"))
    result.email = email
    await result.save()
    return {
        "status": 200,
        "msg": "修改密码成功"
    }


@user.delete("/user")
async def delete_user(name: str):
    try:
        user = await User.get(name=name)
        await user.delete()
        return JSONResponse(status_code=status.HTTP_200_OK, content={
            "message": "注销成功"
        })
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="注销的用户不存在")


@user.get("/user/parse_token_to_user")
def parse_token_to_user(verify_token: dict = Depends(get_current_user)):
    return {
        "message": "欢迎！",
        "user_info": verify_token  # 包含用户信息的字典
    }


@user.get("/user/poster_infos")
async def get_poster_infos(name: str):
    try:
        result = await User.get(name=name).values("name", "avatar")
        return result
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="查看用户信息失败")


@user.get("/user/avatar")
async def get_avatar(name: str):
    try:
        result = await User.get(name=name).values("avatar")
        return result
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="获取头像失败！")


@user.put("/user/avatar")
async def put_avatar(avatar: str, user: dict = Depends(get_current_user)):
    try:
        result = await User.get(id=user.get("id"))
        result.avatar = avatar
        await result.save()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="更改头像失败！")
