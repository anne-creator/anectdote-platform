from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from supabase import create_client, Client

from app.config import Settings, get_settings
from app.middleware.clerk_auth import verify_clerk_jwt


def get_supabase(settings: Annotated[Settings, Depends(get_settings)]) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth_header.removeprefix("Bearer ")
    user_id = await verify_clerk_jwt(token, settings.clerk_jwks_url)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user_id
