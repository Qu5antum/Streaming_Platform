from fastapi import APIRouter, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
import uuid

from src.database.db import AsyncSession, get_session
from src.services.auth_service import AuthService
from src.api.schemas.user_schema import UserCreate, DummyLoginRequest
from src.auth.jwt_handler import JWTHandler


auth_route = APIRouter(
    prefix="/api/user",
    tags=["Auth"]
)


async def get_auth_service(session: AsyncSession = Depends(get_session)):
    return AuthService(session=session, jwt_handler=JWTHandler)


@auth_route.post("/dummyLogin", status_code=201)
async def dummy_login(data: DummyLoginRequest):
    token = JWTHandler.create_access_token(
        subject=str(uuid.uuid4()),
        role=data.role
    )   

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@auth_route.post("/register", status_code=201)
async def register(
    user: UserCreate = Body(),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.add_new_user(user=user)


@auth_route.post("/login", status_code=201)
async def login(
    user: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.auth_user(credents=user)
    

@auth_route.post("/refresh", status_code=201)
async def refresh(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.refresh_token(refresh_token=token)


