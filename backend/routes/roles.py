"""Roles read-only endpoints."""

from fastapi import APIRouter, HTTPException

from db import get_db

router = APIRouter()


from async_lru import alru_cache

@alru_cache(maxsize=1)
async def _cached_list_roles():
    db = get_db()
    cursor = db.roles.find()
    return [doc async for doc in cursor]


@router.get("")
async def list_roles():
    """List all roles."""
    return await _cached_list_roles()


@alru_cache(maxsize=32)
async def _cached_get_role(slug: str):
    db = get_db()
    return await db.roles.find_one({"_id": slug})


@router.get("/{slug}")
async def get_role(slug: str):
    """Get a single role by slug."""
    doc = await _cached_get_role(slug)
    if not doc:
        raise HTTPException(status_code=404, detail="Role not found")
    return doc
