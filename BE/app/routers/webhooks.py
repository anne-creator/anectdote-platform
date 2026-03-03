from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from svix.webhooks import Webhook, WebhookVerificationError
from supabase import Client

from app.config import Settings, get_settings
from app.dependencies import get_supabase

router = APIRouter(prefix="/api", tags=["webhooks"])


@router.post("/webhooks/clerk")
async def clerk_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    body = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }

    try:
        wh = Webhook(settings.clerk_webhook_signing_secret)
        payload = wh.verify(body, headers)
    except WebhookVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    event_type = payload.get("type")
    data = payload.get("data", {})

    if event_type == "user.created":
        user_id = data.get("id")
        email = _extract_primary_email(data)
        display_name = _build_display_name(data)
        supabase.table("users").upsert(
            {
                "user_id": user_id,
                "user_email": email,
                "display_name": display_name,
            }
        ).execute()

    elif event_type == "user.updated":
        user_id = data.get("id")
        email = _extract_primary_email(data)
        display_name = _build_display_name(data)
        supabase.table("users").update(
            {
                "user_email": email,
                "display_name": display_name,
            }
        ).eq("user_id", user_id).execute()

    elif event_type == "user.deleted":
        user_id = data.get("id")
        if user_id:
            supabase.table("users").delete().eq("user_id", user_id).execute()

    return {"status": "ok"}


def _extract_primary_email(data: dict) -> str:
    email_addresses = data.get("email_addresses", [])
    primary_id = data.get("primary_email_address_id")
    for addr in email_addresses:
        if addr.get("id") == primary_id:
            return addr.get("email_address", "")
    if email_addresses:
        return email_addresses[0].get("email_address", "")
    return ""


def _build_display_name(data: dict) -> str | None:
    first = data.get("first_name") or ""
    last = data.get("last_name") or ""
    name = f"{first} {last}".strip()
    return name if name else None
