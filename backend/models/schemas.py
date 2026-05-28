from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# Enums for validation
class OpportunityType(str, Enum):
    hackathon = "hackathon"
    internship = "internship"
    job = "job"
    scholarship = "scholarship"
    oss = "oss"
    ambassador = "ambassador"
    event = "event"
    job = "job"


class DifficultyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ApplicationStatus(str, Enum):
    saved = "saved"
    preparing = "preparing"
    applied = "applied"
    interviewing = "interviewing"
    offered = "offered"
    rejected = "rejected"


# Opportunities
class Opportunity(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=10000)
    organizer: Optional[str] = Field(None, max_length=200)
    type: str = "hackathon"
    url: Optional[str] = Field(None, max_length=2000)
    source: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deadline: Optional[date] = None
    location: Optional[str] = Field(None, max_length=500)
    is_offline: bool = False
    image_url: Optional[str] = Field(None, max_length=2000)
    prize: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list, max_length=20)
    difficulty: Optional[str] = None
    is_closed: bool = False
    created_at: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = [t.value for t in OpportunityType]
        if v not in valid_types:
            return "hackathon"
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v):
        if v is None:
            return v
        valid_levels = [d.value for d in DifficultyLevel]
        if v not in valid_levels:
            return "beginner"
        return v


# Profiles
class Profile(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    name: str = Field("", max_length=200)
    university: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1, le=10)
    bio: Optional[str] = Field(None, max_length=2000)
    avatar_url: Optional[str] = Field(None, max_length=2000)
    skills: List[str] = Field(default_factory=list, max_length=50)
    interests: List[str] = Field(default_factory=list, max_length=50)


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    university: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1, le=10)
    bio: Optional[str] = Field(None, max_length=2000)
    avatar_url: Optional[str] = Field(None, max_length=2000)
    skills: Optional[List[str]] = Field(None, max_length=50)
    interests: Optional[List[str]] = Field(None, max_length=50)


# Bookmarks
class Bookmark(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    opportunity_id: str = Field(..., min_length=1)
    notes: Optional[str] = Field(None, max_length=2000)


# Applications
class Application(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    opportunity_id: str = Field(..., min_length=1)
    status: str = "saved"
    applied_at: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = [s.value for s in ApplicationStatus]
        if v not in valid_statuses:
            return "saved"
        return v


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = [s.value for s in ApplicationStatus]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v


# Alias for backward compatibility
ApplicationUpdate = ApplicationStatusUpdate


class ApplicationEvent(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = Field(None, max_length=2000)


class PeerActivity(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    opportunity_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1, max_length=50)


class ScrapeResponse(BaseModel):
    status: str = "completed"
    new: int = 0
    updated: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    per_source: dict = Field(default_factory=dict)


# AI Matching
class MatchRequest(BaseModel):
    opportunity_id: str = Field(..., min_length=1)


class RecommendationRequest(BaseModel):
    types: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=50)


# Team Finder
class TeamRequest(BaseModel):
    opportunity_id: str = Field(..., min_length=1)
    looking_for: List[str] = Field(default_factory=list, max_length=20)
    description: str = Field("", max_length=2000)
