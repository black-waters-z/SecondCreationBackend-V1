from fastapi import APIRouter, Depends
from backend.security.password_security import get_current_user

test = APIRouter()


