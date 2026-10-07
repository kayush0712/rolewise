"""Questions CRUD — role-versioned."""

from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from db import get_db

router = APIRouter()


def _serialize(doc: dict) -> dict:
    """Convert MongoDB doc to JSON-safe dict."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


from async_lru import alru_cache

@alru_cache(maxsize=128)
async def _cached_list_questions(track: str | None, role: str | None, difficulty: str | None, status: str):
    db = get_db()
    query: dict = {"status": status}
    if track:
        query["track"] = track
    if difficulty:
        query["difficulty"] = difficulty
    if role:
        query["versions.role"] = role

    cursor = db.questions.find(query, {"versions.breakdown": 0})  # Exclude heavy breakdowns in list
    return [_serialize(doc) async for doc in cursor]


@router.get("")
async def list_questions(
    track: str | None = Query(None),
    role: str | None = Query(None),
    difficulty: str | None = Query(None),
    status: str = Query("published"),
):
    """List all questions, filterable by track, role, difficulty, status."""
    return await _cached_list_questions(track, role, difficulty, status)


@alru_cache(maxsize=128)
async def _cached_get_question(slug: str, role: str | None):
    db = get_db()
    doc = await db.questions.find_one({"slug": slug})
    if not doc:
        return None

    doc = _serialize(doc)

    # If role is specified, filter versions to just that role
    if role and "versions" in doc:
        matching = [v for v in doc["versions"] if v["role"] == role]
        doc["versions"] = matching

    return doc


@router.get("/{slug}")
async def get_question(slug: str, role: str | None = Query(None)):
    """Get a question by slug. If role is specified, return only that role's version."""
    doc = await _cached_get_question(slug, role)
    if not doc:
        raise HTTPException(status_code=404, detail="Question not found")
    return doc


@alru_cache(maxsize=128)
async def _cached_get_question_version(slug: str, role: str):
    db = get_db()
    doc = await db.questions.find_one(
        {"slug": slug, "versions.role": role},
        {"versions.$": 1, "slug": 1, "title": 1, "track": 1, "difficulty": 1, "prompt": 1, "outline": 1},
    )
    if not doc:
        return None
    return _serialize(doc)


@router.get("/{slug}/versions/{role}")
async def get_question_version(slug: str, role: str):
    """Get a specific role version of a question."""
    doc = await _cached_get_question_version(slug, role)
    if not doc:
        raise HTTPException(status_code=404, detail="Question or version not found")
    return doc


@router.post("")
async def create_question(body: dict):
    """Create a new question."""
    db = get_db()

    # Check for duplicate slug
    existing = await db.questions.find_one({"slug": body.get("slug")})
    if existing:
        raise HTTPException(status_code=409, detail="Question with this slug already exists")

    body["createdAt"] = datetime.utcnow()
    body["updatedAt"] = datetime.utcnow()
    body.setdefault("status", "published")
    body.setdefault("versions", [])

    result = await db.questions.insert_one(body)
    
    # Invalidate cache
    _cached_list_questions.cache_clear()
    
    return {"_id": str(result.inserted_id), "slug": body["slug"]}


@router.put("/{slug}")
async def update_question(slug: str, body: dict):
    """Update a question (except versions — use the version endpoint)."""
    db = get_db()
    body["updatedAt"] = datetime.utcnow()
    body.pop("_id", None)  # Don't try to update _id
    body.pop("versions", None)  # Versions updated separately

    result = await db.questions.update_one({"slug": slug}, {"$set": body})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Invalidate cache
    _cached_list_questions.cache_clear()
    _cached_get_question.cache_clear()
    _cached_get_question_version.cache_clear()
    
    return {"updated": True}


@router.post("/{slug}/versions")
async def add_question_version(slug: str, version: dict):
    """Add or update a role version for a question."""
    db = get_db()
    role = version.get("role")
    if not role:
        raise HTTPException(status_code=400, detail="Version must include 'role'")

    # Remove existing version for this role, then add the new one
    await db.questions.update_one(
        {"slug": slug},
        {"$pull": {"versions": {"role": role}}},
    )
    result = await db.questions.update_one(
        {"slug": slug},
        {
            "$push": {"versions": version},
            "$set": {"updatedAt": datetime.utcnow()},
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Invalidate cache
    _cached_list_questions.cache_clear()
    _cached_get_question.cache_clear()
    _cached_get_question_version.cache_clear()
    
    return {"updated": True, "role": role}
