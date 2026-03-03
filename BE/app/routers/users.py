from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_supabase, get_current_user
from app.models.schemas import UserResponse

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users/me", response_model=UserResponse)
async def get_me(
    user_id: Annotated[str, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    result = (
        supabase.table("users")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database",
        )
    return result.data[0]
