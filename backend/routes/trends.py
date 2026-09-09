"""Trend ranking — ranks questions from MongoDB."""

from fastapi import APIRouter, Query

from db import get_db

router = APIRouter()

SOURCE_WEIGHTS = {
    "https://github.com/donnemartin/system-design-primer": 24,
    "https://github.com/ashishps1/awesome-low-level-design": 20,
    "https://news.ycombinator.com": 12,
    "https://leetcode.com/explore/interview/card/top-interview-questions-easy/": 10,
    "https://leetcode.com/explore/interview/card/top-interview-questions-medium/": 10,
}

TRACK_BASE = {
    "hld": 18,
    "lld": 16,
    "coding": 12,
    "behavioral": 8,
}


def rank_question(q: dict) -> int:
    source_score = sum(SOURCE_WEIGHTS.get(s, 6) for s in q.get("sources", []))
    role_spread = len(q.get("versions", [])) * 3
    diff = q.get("difficulty", "foundation")
    difficulty_boost = 8 if diff == "foundation" else 12 if diff == "core" else 5
    return TRACK_BASE.get(q.get("track", "hld"), 10) + source_score + role_spread + difficulty_boost


@router.get("")
async def get_trends(track: str | None = Query(None)):
    """Return questions ranked by trending score."""
    db = get_db()
    query: dict = {"status": "published"}
    if track:
        query["track"] = track

    cursor = db.questions.find(query, {"versions.breakdown": 0})
    questions = [doc async for doc in cursor]

    hits = []
    for q in questions:
        score = rank_question(q)
        hits.append({
            "slug": q["slug"],
            "title": q["title"],
            "track": q["track"],
            "score": score,
            "why": (
                f"Ranked from public corpora ({len(q.get('sources', []))} source{'s' if len(q.get('sources', [])) != 1 else ''}) plus role coverage."
                if q.get("sources")
                else "Ranked from internal frequency across levels — common in onsite loops."
            ),
            "sources": q.get("sources", []),
        })

    hits.sort(key=lambda h: h["score"], reverse=True)
    return {
        "generatedAt": __import__("datetime").datetime.utcnow().isoformat(),
        "method": "seeded-ranker",
        "hits": hits,
    }
