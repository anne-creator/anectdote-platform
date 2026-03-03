from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_supabase, get_current_user
from app.models.schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    user_id: Annotated[str, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    result = (
        supabase.table("project_documents")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.post(
    "/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def create_document(
    body: DocumentCreate,
    user_id: Annotated[str, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    result = (
        supabase.table("project_documents")
        .insert(
            {
                "user_id": user_id,
                "title": body.title,
                "project_description": body.project_description,
            }
        )
        .execute()
    )
    return result.data[0]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    result = (
        supabase.table("project_documents")
        .select("*")
        .eq("document_id", document_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return result.data[0]


@router.patch("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    body: DocumentUpdate,
    user_id: Annotated[str, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )

    result = (
        supabase.table("project_documents")
        .update(updates)
        .eq("document_id", document_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return result.data[0]


@router.delete(
    "/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_document(
    document_id: str,
    user_id: Annotated[str, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    result = (
        supabase.table("project_documents")
        .delete()
        .eq("document_id", document_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return None
