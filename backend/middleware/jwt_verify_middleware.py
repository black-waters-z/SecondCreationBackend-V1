import time
from fastapi import Request


async def jwt_verify_middleware(request: Request, call_next):
    request.headers.get("")
    response = await call_next(request)
    return response
