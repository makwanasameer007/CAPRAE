from __future__ import annotations
import asyncio
from urllib.parse import urljoin, urlparse
from typing import Set, Tuple, Optional, List, Dict

import httpx
from selectolax.parser import HTMLParser

from .models import Lead, EnrichmentOptions
from .utils import extract_emails, extract_phones, normalize_domain, unique_preserve_order


SAME_SITE_PATH_HINTS = (
	"/contact",
	"/support",
	"/help",
	"/about",
	"/pricing",
	"/plans",
	"/careers",
	"/jobs",
)

SOCIAL_HOSTS = {
	"linkedin.com": "linkedin",
	"x.com": "x",
	"twitter.com": "twitter",
	"facebook.com": "facebook",
	"instagram.com": "instagram",
	"youtube.com": "youtube",
	"tiktok.com": "tiktok",
}

TECH_HINTS = {
	"cdn.shopify.com": "Shopify",
	"myshopify.com": "Shopify",
	"static1.squarespace.com": "Squarespace",
	"wixstatic.com": "Wix",
	"/wp-content/": "WordPress",
	"js.stripe.com": "Stripe",
	"googletagmanager.com": "Google Tag Manager",
	"www.googletagmanager.com": "Google Tag Manager",
	"www.google-analytics.com": "Google Analytics",
	"gtag(": "Google Analytics",
	"cdn.segment.com": "Segment",
	"hs-scripts.com": "HubSpot",
	"widget.intercom.io": "Intercom",
	"static.cloudflareinsights.com": "Cloudflare Analytics",
}


def _is_same_site(url: str, base_domain: str) -> bool:
	try:
		parsed = urlparse(url)
		if not parsed.netloc:
			return True
		domain = parsed.netloc.lower()
		return base_domain in domain
	except Exception:
		return False


def _extract_links(html: str, base_url: str, base_domain: str) -> Set[str]:
	links: Set[str] = set()
	parser = HTMLParser(html)
	for node in parser.css("a"):
		href = node.attrs.get("href")
		if not href:
			continue
		joined = urljoin(base_url, href)
		if _is_same_site(joined, base_domain):
			links.add(joined)
	return links


def _detect_meta(parser: HTMLParser) -> Tuple[Optional[str], Optional[str]]:
	title_node = parser.css_first("title")
	title = title_node.text(strip=True) if title_node else None
	desc_node = parser.css_first('meta[name="description"]') or parser.css_first('meta[name="Description"]')
	description = desc_node.attrs.get("content") if desc_node else None
	return title, description


def _detect_socials(parser: HTMLParser) -> Dict[str, str]:
	socials: Dict[str, str] = {}
	for a in parser.css("a"):
		href = a.attrs.get("href", "").strip()
		for host, name in SOCIAL_HOSTS.items():
			if host in href:
				socials[name] = href
	return socials


def _detect_technologies(html: str, parser: HTMLParser) -> List[str]:
	techs = set()
	text = html
	for hint, label in TECH_HINTS.items():
		if hint in text:
			techs.add(label)
	gen = parser.css_first('meta[name="generator"], meta[name="Generator"], meta[generator], meta[name="powered-by"]')
	if gen:
		content = (gen.attrs.get("content") or gen.attrs.get("generator") or "").lower()
		if "wordpress" in content:
			techs.add("WordPress")
	return sorted(techs)


def _flags_from_url(url: str) -> Tuple[bool, bool, bool]:
	low = url.lower()
	has_pricing = any(seg in low for seg in ("/pricing", "/plans"))
	has_careers = any(seg in low for seg in ("/careers", "/jobs"))
	is_contact = any(seg in low for seg in ("/contact", "/support", "/help"))
	return has_pricing, has_careers, is_contact


async def _fetch(client: httpx.AsyncClient, url: str) -> Optional[str]:
	try:
		resp = await client.get(url, follow_redirects=True)
		if resp.status_code >= 400:
			return None
		return resp.text
	except Exception:
		return None


async def gather_site_data(domain_or_url: str, options: EnrichmentOptions) -> Lead:
	base_domain = normalize_domain(domain_or_url)
	seed_urls = [f"https://{base_domain}", f"http://{base_domain}"]
	seen: Set[str] = set()
	queue: List[str] = []
	queue.extend(seed_urls)
	emails: Set[str] = set()
	phones: Set[str] = set()
	contact_pages: Set[str] = set()
	socials: Dict[str, str] = {}
	meta_title: Optional[str] = None
	meta_description: Optional[str] = None
	technologies: Set[str] = set()
	has_pricing_page = False
	has_careers_page = False

	limits = httpx.Limits(max_connections=options.concurrency)
	timeout = httpx.Timeout(options.timeout_seconds)
	headers = {"User-Agent": options.user_agent}

	async with httpx.AsyncClient(http2=True, limits=limits, timeout=timeout, headers=headers) as client:
		pages_fetched = 0
		while queue and pages_fetched < options.max_pages:
			url = queue.pop(0)
			if url in seen:
				continue
			seen.add(url)
			html = await _fetch(client, url)
			if not html:
				continue
			pages_fetched += 1

			parser = HTMLParser(html)
			emails.update(extract_emails(html))
			phones.update(extract_phones(html))
			socials.update(_detect_socials(parser))
			techs = _detect_technologies(html, parser)
			for t in techs:
				technologies.add(t)

			if meta_title is None or meta_description is None:
				title, desc = _detect_meta(parser)
				meta_title = meta_title or title
				meta_description = meta_description or desc

			hp, hc, ic = _flags_from_url(url)
			has_pricing_page = has_pricing_page or hp
			has_careers_page = has_careers_page or hc
			if ic:
				contact_pages.add(url)

			for link in _extract_links(html, url, base_domain):
				if link not in seen and any(h in link for h in SAME_SITE_PATH_HINTS):
					queue.append(link)

	return Lead(
		company=base_domain.split(".")[0].capitalize(),
		domain=base_domain,
		website_url=f"https://{base_domain}",
		emails=list(unique_preserve_order(sorted(emails))),
		phones=list(unique_preserve_order(sorted(phones))),
		socials=socials,
		meta_title=meta_title,
		meta_description=meta_description,
		contact_pages=list(contact_pages),
		technologies=sorted(technologies),
		has_pricing_page=has_pricing_page,
		has_careers_page=has_careers_page,
	)
