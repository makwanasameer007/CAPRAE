from __future__ import annotations
import re
import asyncio
from typing import Iterable, Set, Tuple
import tldextract

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_REGEX = re.compile(r"\+?\d[\d\s().-]{7,}\d")


def normalize_domain(url_or_domain: str) -> str:
	extracted = tldextract.extract(url_or_domain)
	domain = ".".join(p for p in [extracted.domain, extracted.suffix] if p)
	return domain.lower()


def extract_emails(text: str) -> Set[str]:
	return set(EMAIL_REGEX.findall(text or ""))


def extract_phones(text: str) -> Set[str]:
	return set(PHONE_REGEX.findall(text or ""))


def unique_preserve_order(items: Iterable[str]) -> Tuple[str, ...]:
	seen = set()
	result = []
	for item in items:
		if item not in seen:
			seen.add(item)
			result.append(item)
	return tuple(result)


async def run_limited(concurrency: int, coros: Iterable[asyncio.Future]):
	sem = asyncio.Semaphore(concurrency)

	async def wrapper(coro):
		async with sem:
			return await coro

	return await asyncio.gather(*(wrapper(c) for c in coros), return_exceptions=True)
