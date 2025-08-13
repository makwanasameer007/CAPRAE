from __future__ import annotations
import asyncio
from typing import Iterable, List

import pandas as pd

from .models import Lead, EnrichmentOptions
from .scraper import gather_site_data
from .scoring import score_lead


async def _enrich_one(domain: str, options: EnrichmentOptions) -> Lead:
	lead = await gather_site_data(domain, options)
	score, reasons = score_lead(lead)
	lead.score = score
	lead.score_reasons = reasons
	return lead


async def enrich_domains_async(domains: Iterable[str], options: EnrichmentOptions) -> List[Lead]:
	real_domains = [d.strip() for d in domains if d and d.strip()]
	leads = await asyncio.gather(*[_enrich_one(d, options) for d in real_domains])
	return list(leads)


def leads_to_dataframe(leads: List[Lead]) -> pd.DataFrame:
	rows = []
	for l in leads:
		rows.append({
			"company": l.company,
			"domain": l.domain,
			"website_url": l.website_url,
			"emails": ", ".join(l.emails),
			"phones": ", ".join(l.phones),
			"socials": ", ".join(f"{k}:{v}" for k, v in sorted(l.socials.items())),
			"meta_title": l.meta_title or "",
			"meta_description": l.meta_description or "",
			"contact_pages": ", ".join(l.contact_pages),
			"technologies": ", ".join(l.technologies),
			"has_pricing_page": l.has_pricing_page,
			"has_careers_page": l.has_careers_page,
			"score": l.score,
			"score_reasons": "; ".join(l.score_reasons),
		})
	return pd.DataFrame(rows)
