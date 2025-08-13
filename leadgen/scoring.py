from __future__ import annotations
from typing import List, Tuple
from .models import Lead


SAAS_TECH_SIGNALS = {
	"Stripe": 12,
	"Segment": 8,
	"HubSpot": 6,
	"Intercom": 6,
	"Google Analytics": 3,
	"Google Tag Manager": 3,
}


def score_lead(lead: Lead) -> Tuple[float, List[str]]:
	score = 0.0
	reasons: List[str] = []

	if lead.emails:
		score += 30
		reasons.append("Has contact email")
		sales_like = [e for e in lead.emails if any(x in e.lower() for x in ("sales@", "hello@", "info@", "contact@"))]
		if sales_like:
			score += 10
			reasons.append("Has generic inbox")

	if lead.has_pricing_page:
		score += 15
		reasons.append("Has pricing page")

	if lead.has_careers_page:
		score += 10
		reasons.append("Hiring signal (careers)")

	if lead.socials:
		score += 5
		reasons.append("Has social presence")

	for tech in lead.technologies:
		if tech in SAAS_TECH_SIGNALS:
			w = SAAS_TECH_SIGNALS[tech]
			score += w
			reasons.append(f"Tech: {tech}")

	return score, reasons
