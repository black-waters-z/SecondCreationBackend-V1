from fastapi import APIRouter, HTTPException, status, Depends
from backend.models import User
from backend.core import rt
from starlette.responses import JSONResponse
from pydantic import BaseModel
from backend.security import get_current_user

"""
进行激活操作
"""

active = APIRouter(dependencies=[Depends(get_current_user)])


class activate_account(BaseModel):
    activate_code: str


@active.put("/activate_account")
async def activate_account(active_account: activate_account, user: dict = Depends(get_current_user)):
    redis_email_active_code = rt.get(f"{user.get('name')}_email_code").decode('utf-8')
    if not redis_email_active_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="输入的用户名错误")

    if active_account.activate_code == redis_email_active_code:
        try:
            user = await User.get(name=active_account.name)  # tortoise orm 找不到对象会直接抛出异常
            user.activated = True
            await user.save()
            rt.delete(f"{active_account.name}_email_code")
            return JSONResponse(status_code=200,
                                content={
                                    "message": "账号激活成功",
                                    "user": user.name,
                                    "activated": user.activated
                                })
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号未进行注册，请先进行注册")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="输入的激活码错误")
