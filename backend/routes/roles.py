"""Roles read-only endpoints."""

from fastapi import APIRouter, HTTPException

from db import get_db

router = APIRouter()


@router.get("")
async def list_roles():
    """List all roles."""
    db = get_db()
    cursor = db.roles.find()
    return [doc async for doc in cursor]


@router.get("/{slug}")
async def get_role(slug: str):
    """Get a single role by slug."""
    db = get_db()
    doc = await db.roles.find_one({"_id": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Role not found")
    return doc
