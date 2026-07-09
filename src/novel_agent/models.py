from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


ChapterStatus = Literal["planned", "drafted", "reviewed", "revised"]


class NovelConfig(BaseModel):
    """Top-level configuration for a novel project."""

    title: str
    genre: str = "未设定"
    language: str = "zh-CN"
    target_words: int = 100_000
    pov: str = "第三人称有限视角"
    style: str = "清晰、有画面感、避免空泛AI腔"
    premise: str = ""


class Character(BaseModel):
    """Reusable character card."""

    name: str
    role: str = ""
    goals: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    voice: str = ""


class ChapterPlan(BaseModel):
    """Plan and lifecycle state for one chapter."""

    number: int
    title: str
    goal: str
    conflict: str = ""
    summary: str = ""
    status: ChapterStatus = "planned"


class ProjectState(BaseModel):
    """Lightweight persisted state for a novel project."""

    current_chapter: int = 1
    chapters: list[ChapterPlan] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
