"""Claude-powered question discoverer.

Uses Anthropic SDK to search the web for trending interview questions,
then creates draft entries in MongoDB for human review.
"""

import json
import os
import re
from datetime import datetime

import anthropic

from db import get_db

SEARCH_QUERIES = {
    "hld": [
        "most asked system design interview questions 2025 2026 FAANG",
        "trending high level design interview problems senior engineer",
    ],
    "lld": [
        "low level design interview questions 2025 2026 object oriented",
        "trending LLD interview problems FAANG senior",
    ],
    "coding": [
        "most frequently asked coding interview questions 2025 2026",
        "trending leetcode interview problems FAANG",
    ],
    "behavioral": [
        "behavioral interview questions senior staff engineer 2025 2026",
        "most common behavioral interview questions tech companies",
    ],
    None: [
        "most asked system design interview questions 2025 2026",
        "trending interview questions software engineer FAANG 2025",
    ],
}

EXTRACTION_PROMPT = """You are helping build an interview prep platform called ROLEWISE.

I need you to search the web and find trending, commonly-asked interview questions for software engineering roles. 

Focus on: {focus}

For each question you find, provide:
1. title — the interview question title (e.g. "Design a URL Shortener")
2. slug — a URL-friendly version (e.g. "design-url-shortener")  
3. track — one of: "hld" (high-level/system design), "lld" (low-level/OOP design), "coding" (algorithms), "behavioral"
4. difficulty — one of: "foundation", "core", "stretch"
5. prompt — the question prompt as an interviewer would state it
6. outline — 4-6 key topics to cover
7. suggestedRoles — which roles this is relevant for: "sde-1", "sde-2", "senior", "staff", "principal"
8. rationale — WHY this question is trending (what sources mention it)

Return your findings as a JSON array. Find 3-5 questions that are genuinely trending and frequently asked. Exclude these questions which we already have: {existing_slugs}

Return ONLY the JSON array, no other text."""


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


async def discover_questions(track: str | None = None) -> list[dict]:
    """Use Claude to search for trending interview questions and save as drafts."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Add it to backend/.env")

    db = get_db()

    # Get existing question slugs to avoid duplicates
    existing = []
    async for doc in db.questions.find({}, {"slug": 1}):
        existing.append(doc["slug"])
    async for doc in db.agent_drafts.find({"status": "pending"}, {"slug": 1}):
        existing.append(doc["slug"])

    # Determine focus
    focus_map = {
        "hld": "system design / high-level design questions",
        "lld": "low-level design / object-oriented design questions",
        "coding": "coding / algorithm / data structure questions",
        "behavioral": "behavioral / leadership interview questions",
    }
    focus = focus_map.get(track, "all types of software engineering interview questions")

    # Call Claude with web search
    client = anthropic.Anthropic(api_key=api_key)

    prompt = EXTRACTION_PROMPT.format(
        focus=focus,
        existing_slugs=", ".join(existing) if existing else "(none)",
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract JSON from response
        text = response.content[0].text
        # Try to parse the JSON array from the response
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if not json_match:
            raise ValueError("Claude did not return a valid JSON array")

        discoveries = json.loads(json_match.group())
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}")
    except json.JSONDecodeError:
        raise RuntimeError("Failed to parse Claude's response as JSON")

    # Save discoveries as drafts
    drafts_created = []
    for item in discoveries:
        slug = item.get("slug") or _slugify(item.get("title", "untitled"))

        # Skip if already exists
        if slug in existing:
            continue

        draft = {
            "title": item.get("title", "Untitled"),
            "slug": slug,
            "track": item.get("track", track or "hld"),
            "difficulty": item.get("difficulty", "core"),
            "prompt": item.get("prompt", ""),
            "outline": item.get("outline", []),
            "sources": item.get("sources", []),
            "aiRationale": item.get("rationale", "Discovered by Claude agent"),
            "suggestedRoles": item.get("suggestedRoles", ["senior"]),
            "status": "pending",
            "discoveredAt": datetime.utcnow(),
            "reviewedBy": None,
            "reviewedAt": None,
            "reviewNotes": None,
        }

        result = await db.agent_drafts.insert_one(draft)
        draft["_id"] = str(result.inserted_id)
        drafts_created.append(draft)
        existing.append(slug)  # Track to avoid dupes within this batch

    return drafts_created
