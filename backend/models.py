"""Pydantic models for all MongoDB collections."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ─── Enums ─────────────────────────────────────────────

class RoleSlug(str, Enum):
    SDE_1 = "sde-1"
    SDE_2 = "sde-2"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"


class TrackSlug(str, Enum):
    CODING = "coding"
    LLD = "lld"
    HLD = "hld"
    BEHAVIORAL = "behavioral"


class Difficulty(str, Enum):
    FOUNDATION = "foundation"
    CORE = "core"
    STRETCH = "stretch"


class QuestionStatus(str, Enum):
    PUBLISHED = "published"
    DRAFT = "draft"
    REVIEW = "review"


class DraftStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ─── Content Block Types (discriminated union) ─────────

class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    content: str


class RequirementsBlock(BaseModel):
    type: Literal["requirements"] = "requirements"
    core: list[str]
    out_of_scope: list[str] = Field(alias="outOfScope", default=[])

    model_config = {"populate_by_name": True}


class FunctionalNonFunctionalBlock(BaseModel):
    type: Literal["functional-nonfunctional"] = "functional-nonfunctional"
    functional: list[str]
    non_functional: list[str] = Field(alias="nonFunctional", default=[])

    model_config = {"populate_by_name": True}


class EntityRow(BaseModel):
    name: str
    purpose: str


class EntityTableBlock(BaseModel):
    type: Literal["entity-table"] = "entity-table"
    entities: list[EntityRow]


class ApiEndpoint(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    endpoint: str
    description: str


class ApiTableBlock(BaseModel):
    type: Literal["api-table"] = "api-table"
    endpoints: list[ApiEndpoint]


class EvolutionOption(BaseModel):
    number: str
    label: str
    description: str
    pros: list[str]
    cons: list[str]
    recommended: bool = False


class EvolutionBlock(BaseModel):
    type: Literal["evolution"] = "evolution"
    options: list[EvolutionOption]


class ArchitectureNode(BaseModel):
    label: str
    type: Literal["critical", "supporting"]


class ArchitectureConnection(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    style: Literal["bidirectional", "unidirectional"]

    model_config = {"populate_by_name": True}


class ArchitectureFlowBlock(BaseModel):
    type: Literal["architecture-flow"] = "architecture-flow"
    nodes: list[ArchitectureNode]
    connections: list[ArchitectureConnection]
    explanation: str | None = None


class ComparisonOption(BaseModel):
    label: str
    description: str


class ComparisonBlock(BaseModel):
    type: Literal["comparison"] = "comparison"
    title: str
    option_a: ComparisonOption = Field(alias="optionA")
    option_b: ComparisonOption = Field(alias="optionB")
    recommendation: str
    rationale: str

    model_config = {"populate_by_name": True}


class CalloutBlock(BaseModel):
    type: Literal["callout"] = "callout"
    variant: Literal["warning", "info", "definition"]
    title: str
    content: str


class UploadComparisonOption(BaseModel):
    label: str
    description: str
    details: str | None = None
    recommended: bool = False


class UploadComparisonBlock(BaseModel):
    type: Literal["upload-comparison"] = "upload-comparison"
    options: list[UploadComparisonOption]


# Union type for all blocks
ContentBlock = (
    TextBlock
    | RequirementsBlock
    | FunctionalNonFunctionalBlock
    | EntityTableBlock
    | ApiTableBlock
    | EvolutionBlock
    | ArchitectureFlowBlock
    | ComparisonBlock
    | CalloutBlock
    | UploadComparisonBlock
)


# ─── Breakdown Section ─────────────────────────────────

class BreakdownSection(BaseModel):
    id: str
    step_number: int = Field(alias="stepNumber")
    label: str
    title: str
    blocks: list[dict]  # Store as raw dicts for flexibility

    model_config = {"populate_by_name": True}


class QuestionBreakdown(BaseModel):
    focus_areas: list[str] = Field(alias="focusAreas", default=[])
    target_role: str = Field(alias="targetRole", default="")
    total_sections: int = Field(alias="totalSections", default=0)
    completed_sections: int = Field(alias="completedSections", default=0)
    sections: list[BreakdownSection] = []

    model_config = {"populate_by_name": True}


# ─── Role-Versioned Question Content ──────────────────

class QuestionVersion(BaseModel):
    role: str
    level_bar: str = Field(alias="levelBar", default="")
    breakdown: QuestionBreakdown | None = None

    model_config = {"populate_by_name": True}


# ─── Top-Level Collection Models ──────────────────────

class InterviewMix(BaseModel):
    track: str
    weight: int


class RoleDoc(BaseModel):
    slug: str = Field(alias="_id")
    title: str
    short_title: str = Field(alias="shortTitle")
    band: str
    summary: str
    interview_mix: list[InterviewMix] = Field(alias="interviewMix")
    bar: list[str]

    model_config = {"populate_by_name": True}


class TrackDoc(BaseModel):
    slug: str = Field(alias="_id")
    title: str
    short_title: str = Field(alias="shortTitle")
    summary: str

    model_config = {"populate_by_name": True}


class QuestionDoc(BaseModel):
    slug: str
    title: str
    track: str
    difficulty: str
    timebox_minutes: int = Field(alias="timeboxMinutes", default=45)
    prompt: str
    outline: list[str] = []
    sources: list[str] = []
    status: str = QuestionStatus.PUBLISHED.value
    discovered_by: str | None = Field(alias="discoveredBy", default=None)
    created_at: datetime = Field(alias="createdAt", default_factory=datetime.utcnow)
    updated_at: datetime = Field(alias="updatedAt", default_factory=datetime.utcnow)
    versions: list[QuestionVersion] = []

    model_config = {"populate_by_name": True}


class AgentDraftDoc(BaseModel):
    title: str
    slug: str
    track: str
    difficulty: str
    prompt: str
    outline: list[str] = []
    sources: list[str] = []
    ai_rationale: str = Field(alias="aiRationale", default="")
    suggested_roles: list[str] = Field(alias="suggestedRoles", default=[])
    status: str = DraftStatus.PENDING.value
    discovered_at: datetime = Field(alias="discoveredAt", default_factory=datetime.utcnow)
    reviewed_by: str | None = Field(alias="reviewedBy", default=None)
    reviewed_at: datetime | None = Field(alias="reviewedAt", default=None)
    review_notes: str | None = Field(alias="reviewNotes", default=None)

    model_config = {"populate_by_name": True}


class UserProgressDoc(BaseModel):
    user_id: str = Field(alias="userId")
    question_slug: str = Field(alias="questionSlug")
    role: str
    completed_sections: list[str] = Field(alias="completedSections", default=[])
    last_accessed_at: datetime = Field(alias="lastAccessedAt", default_factory=datetime.utcnow)
    notes: str = ""

    model_config = {"populate_by_name": True}
