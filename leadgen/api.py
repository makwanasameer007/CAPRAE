from __future__ import annotations
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

from .models import EnrichmentOptions, Lead
from .enrich import enrich_domains_async


class EnrichRequest(BaseModel):
	domains: List[str]
	max_pages: int = 5
	timeout_seconds: float = 10.0
	concurrency: int = 5


class EnrichResponse(BaseModel):
	leads: List[Lead]


def create_app() -> FastAPI:
	app = FastAPI(title="LeadGen API", version="0.1.0")

	@app.post("/enrich", response_model=EnrichResponse)
	async def enrich(req: EnrichRequest) -> EnrichResponse:
		options = EnrichmentOptions(
			max_pages=req.max_pages,
			timeout_seconds=req.timeout_seconds,
			concurrency=req.concurrency,
		)
		leads = await enrich_domains_async(req.domains, options)
		return EnrichResponse(leads=leads)

	return app


def run(host: str = "0.0.0.0", port: int = 8000):
	import uvicorn
	uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
	run()
