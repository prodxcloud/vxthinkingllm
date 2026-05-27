"""Web-scraping models for VxThinkingLLM.

Trimmed-down port of va_fastapiclient/.../webscraper/models.py — keeps
only what the LLM-fallback flow needs: page metadata, scrape result,
contact info, link info. Drops cloud-resource persistence, platform
scrape requests, and the persistence report (we don't write to a DB
from the LLM platform).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MediaAsset(BaseModel):
    src: str
    alt: Optional[str] = None
    title: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    srcset: Optional[str] = None
    media_type: Literal["image", "video", "audio", "other"] = "image"


class LinkInfo(BaseModel):
    href: str
    text: str = ""
    title: Optional[str] = None
    rel: Optional[str] = None
    kind: Literal["internal", "external", "email", "tel", "social", "anchor", "javascript"] = "external"
    domain: Optional[str] = None


class ContactInfo(BaseModel):
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    social_handles: Dict[str, List[str]] = Field(default_factory=dict)
    addresses: List[str] = Field(default_factory=list)


class PageMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    canonical_url: Optional[str] = None
    language: Optional[str] = None
    favicon: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    open_graph: Dict[str, str] = Field(default_factory=dict)
    twitter_card: Dict[str, str] = Field(default_factory=dict)
    schema_org: List[Dict[str, Any]] = Field(default_factory=list)


class TableData(BaseModel):
    caption: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    total_rows: int = 0


class ScrapeResult(BaseModel):
    """Single-URL fetch + extract result. Serialisable, no DB coupling."""
    url: str
    final_url: Optional[str] = None
    status: Literal["success", "partial", "failed"] = "success"
    status_code: Optional[int] = None
    fetcher: Literal["httpx", "playwright", "requests"] = "httpx"
    load_time_ms: Optional[int] = None
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    metadata: PageMetadata = Field(default_factory=PageMetadata)
    text: str = ""
    word_count: int = 0
    reading_time_minutes: float = 0.0

    images: List[MediaAsset] = Field(default_factory=list)
    videos: List[MediaAsset] = Field(default_factory=list)
    links: Dict[str, List[LinkInfo]] = Field(default_factory=dict)
    tables: List[TableData] = Field(default_factory=list)
    contacts: ContactInfo = Field(default_factory=ContactInfo)

    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class SearchHit(BaseModel):
    """One entry from a query→URLs search."""
    title: str
    url: str
    snippet: str = ""
    rank: int = 0
