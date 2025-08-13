from __future__ import annotations
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict


class Lead(BaseModel):
	company: str = Field(..., description="Company name if known")
	domain: Optional[str] = Field(None, description="Primary website domain")
	website_url: Optional[HttpUrl] = None
	emails: List[str] = []
	phones: List[str] = []
	socials: Dict[str, str] = {}
	meta_title: Optional[str] = None
	meta_description: Optional[str] = None
	contact_pages: List[str] = []
	technologies: List[str] = []
	has_pricing_page: bool = False
	has_careers_page: bool = False
	score: float = 0.0
	score_reasons: List[str] = []


class EnrichmentOptions(BaseModel):
	max_pages: int = 5
	timeout_seconds: float = 10.0
	concurrency: int = 5
	user_agent: str = (
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
		"(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
	)
