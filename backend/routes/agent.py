"""Claude agent endpoints — discover questions + draft review workflow."""

from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from db import get_db

router = APIRouter()


@router.post("/discover")
async def trigger_discovery(track: str | None = Query(None)):
    """Trigger Claude to search for trending interview questions.
    
    Results are saved to agent_drafts with status 'pending'.
    """
    from agents.question_discoverer import discover_questions

    try:
        drafts = await discover_questions(track=track)
        return {
            "discovered": len(drafts),
            "drafts": drafts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drafts")
async def list_drafts(status: str = Query("pending")):
    """List agent-discovered drafts, filterable by status."""
    db = get_db()
    cursor = db.agent_drafts.find({"status": status}).sort("discoveredAt", -1)
    docs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        docs.append(doc)
    return docs


@router.get("/drafts/{draft_id}")
async def get_draft(draft_id: str):
    """Get a single draft by ID."""
    db = get_db()
    doc = await db.agent_drafts.find_one({"_id": ObjectId(draft_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    doc["_id"] = str(doc["_id"])
    return doc


@router.post("/drafts/{draft_id}/approve")
async def approve_draft(draft_id: str, body: dict | None = None):
    """Approve a draft → creates a published question in the questions collection."""
    db = get_db()
    body = body or {}

    draft = await db.agent_drafts.find_one({"_id": ObjectId(draft_id)})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Draft is already {draft['status']}")

    # Check for slug collision
    existing = await db.questions.find_one({"slug": draft["slug"]})
    if existing:
        raise HTTPException(status_code=409, detail="A question with this slug already exists")

    # Create published question from draft
    question = {
        "slug": draft["slug"],
        "title": draft["title"],
        "track": draft["track"],
        "difficulty": draft.get("difficulty", "core"),
        "timeboxMinutes": 45,
        "prompt": draft.get("prompt", ""),
        "outline": draft.get("outline", []),
        "sources": draft.get("sources", []),
        "status": "published",
        "discoveredBy": "claude-agent",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "versions": [],  # Breakdowns to be added later
    }

    await db.questions.insert_one(question)

    # Mark draft as approved
    await db.agent_drafts.update_one(
        {"_id": ObjectId(draft_id)},
        {
            "$set": {
                "status": "approved",
                "reviewedAt": datetime.utcnow(),
                "reviewedBy": body.get("reviewedBy", "admin"),
                "reviewNotes": body.get("notes", ""),
            }
        },
    )

    return {"approved": True, "slug": draft["slug"]}


@router.post("/drafts/{draft_id}/reject")
async def reject_draft(draft_id: str, body: dict | None = None):
    """Reject a draft with optional notes."""
    db = get_db()
    body = body or {}

    result = await db.agent_drafts.update_one(
        {"_id": ObjectId(draft_id), "status": "pending"},
        {
            "$set": {
                "status": "rejected",
                "reviewedAt": datetime.utcnow(),
                "reviewedBy": body.get("reviewedBy", "admin"),
                "reviewNotes": body.get("notes", ""),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Draft not found or already reviewed")
    return {"rejected": True}
