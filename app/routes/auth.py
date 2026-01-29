from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.service.pocketbase import get_pocketbase_service, PocketBaseService

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/login")
async def login(
    payload: LoginRequest,
    pb: PocketBaseService = Depends(get_pocketbase_service)
):
    try:
        # PB uses 'identity' (email or username)
        result = await pb.auth_with_password(payload.email, payload.password)
        return {
            "token": result["token"],
            "user": result["record"]
        }
    except Exception as e:
        # Pass through exceptions (handled by Service usually, but fallback here)
        raise e

@router.post("/signup")
async def signup(
    payload: SignupRequest,
    pb: PocketBaseService = Depends(get_pocketbase_service)
):
    try:
        result = await pb.create_user(payload.email, payload.password, payload.name)
        return result
    except Exception as e:
        raise e

@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    pb: PocketBaseService = Depends(get_pocketbase_service)
):
    try:
        await pb.request_password_reset(payload.email)
        return {"message": "Password reset email sent."}
    except Exception as e:
        raise e
