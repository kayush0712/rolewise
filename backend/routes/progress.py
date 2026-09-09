"""User progress endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from db import get_db

router = APIRouter()


@router.get("/{user_id}")
async def get_user_progress(user_id: str):
    """Get all progress records for a user."""
    db = get_db()
    cursor = db.user_progress.find({"userId": user_id})
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


@router.put("/{user_id}/{question_slug}")
async def update_progress(user_id: str, question_slug: str, body: dict):
    """Create or update progress for a user on a question."""
    db = get_db()
    update_data = {
        "userId": user_id,
        "questionSlug": question_slug,
        "role": body.get("role", "senior"),
        "completedSections": body.get("completedSections", []),
        "lastAccessedAt": datetime.utcnow(),
        "notes": body.get("notes", ""),
    }

    result = await db.user_progress.update_one(
        {"userId": user_id, "questionSlug": question_slug},
        {"$set": update_data},
        upsert=True,
    )

    return {"upserted": result.upserted_id is not None, "modified": result.modified_count > 0}
