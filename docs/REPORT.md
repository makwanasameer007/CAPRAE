# LeadGen: 5-hour AI-Readiness Lead Enrichment Tool

## What I built (scope)
A lean lead enrichment tool with CLI + Streamlit UI that:
- Crawls a company's website (few pages) to extract contact signals (emails/phones), social links, meta info, tech hints, and key pages (pricing/careers/contact).
- Scores leads via simple, business-aligned heuristics that prioritize intent and SaaS readiness.
- Exports clean CSV/Parquet for easy handoff into CRM or prospecting workflows.

## Why this matters (business rationale)
- High-signal > high-volume: SDRs waste time on low-intent prospects. Pricing/careers pages and generic inboxes (sales@, info@) are strong buying/hiring signals.
- Enrichment beats raw scraping: Actionable fields (contact pages, tech stack hints, socials) improve reply rates and personalization.
- Fast operational fit: CSV export, simple CLI, and a zero-config UI make this easy to adopt across teams.

## Design choices (5-hour constraints)
- Async HTTP + shallow crawl (5 pages default) to balance coverage and speed.
- Heuristic tech detection via static hints (Stripe, Segment, HubSpot, GA, WordPress); no heavy ML to stay within timebox.
- Rule-based scoring aligned to ICP: pricing (+15), careers (+10), generic inbox (+10), email present (+30), SaaS tech signals (+3–12), socials (+5).
- Minimal schema with Pydantic models for clean typing and future extension.

## Data flow
Input (domains) -> Async fetch -> Parse HTML (selectolax) -> Extract signals -> Score -> DataFrame -> Export CSV/Parquet.

## Accuracy/quality tactics
- Site-constrained link expansion to only high-yield paths (contact/pricing/careers/about).
- Tech detection from headers/scripts/meta and generator tags.
- Deduplication for emails/phones; generic inbox detection.

## Risks and mitigations
- Site blockers/CAPTCHAs: conservative concurrency, user-agent, short timeouts; future work could add rotating proxies.
- Partial coverage: shallow crawl may miss signals; user can raise `--max-pages`.
- Parsing variance: selectolax is tolerant and fast; future work could add JS rendering for SPAs.

## Next iterations (if more time)
- Email verification (SMTP/pattern-based), role/person extraction (regex + enrichment APIs), and de-dup across runs.
- Headless rendering fallback (Playwright), proxy pools, and retry policies.
- CRM/Zapier exports, saved searches, and scheduled jobs.
- ML-based scoring fine-tuned on conversion labels; domain classification (SaaS vs non-SaaS).

## How to run
- CLI: `leadgen enrich --domains acme.com,foo.io --out leads.csv`
- UI: `leadgen-ui` then open local URL.
- API: `leadgen-api` then POST `/enrich` with `{ "domains": ["acme.com"] }`.
