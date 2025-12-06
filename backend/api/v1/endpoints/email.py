import uuid
from backend.core import rt
from backend.models import User
from backend.schemas import User_Pydantic, UserIn_Pydantic
from fastapi import APIRouter, BackgroundTasks
from starlette.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType


class EmailSchema(BaseModel):
    user_name:str
    email: EmailStr


conf = ConnectionConfig(
    MAIL_USERNAME="zy160709379@163.com",
    MAIL_PASSWORD="RKmYKEAQe2bK29Py",
    MAIL_FROM="zy160709379@163.com",
    MAIL_PORT=25,
    MAIL_SERVER="smtp.163.com",
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)

email = APIRouter()


@email.post("/email")
def send_email(background_task: BackgroundTasks, email: EmailSchema):
    """
    email:user_name,email
    随机生成数，然后保存在redis数据库中
    """
    data=uuid.uuid4()
    html = f"<p>用户{email.user_name},您的账号激活码为{str(data)}，有效时间为30分钟</p>"
    rt.setex(f"{email.user_name}_email_code",value=str(data),time=1800)
    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[email.dict().get("email")],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    background_task.add_task(fm.send_message, message)

    return JSONResponse(status_code=200, content={"message": "email has been send"})
