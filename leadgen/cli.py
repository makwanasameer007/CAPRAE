from __future__ import annotations
import sys
import asyncio
from pathlib import Path
from typing import Optional

import typer
import pandas as pd
from rich import print as rprint

from .models import EnrichmentOptions
from .enrich import enrich_domains_async, leads_to_dataframe

app = typer.Typer(add_completion=False, no_args_is_help=True, help="Lead enrichment CLI")


def _parse_domains(domains: Optional[str], file: Optional[Path]) -> list[str]:
	domain_list: list[str] = []
	if domains:
		domain_list.extend([d.strip() for d in domains.split(",") if d.strip()])
	if file:
		df = pd.read_csv(file)
		col = None
		for candidate in ("domain", "url", "website", "website_url"):
			if candidate in df.columns:
				col = candidate
				break
		if col is None:
			raise typer.BadParameter("CSV must include a 'domain' or 'url' column")
		domain_list.extend(df[col].astype(str).tolist())
	return [d for d in domain_list if d]


@app.command()
def enrich(
	domains: Optional[str] = typer.Option(None, help="Comma-separated domains, e.g., 'acme.com,foo.io'"),
	file: Optional[Path] = typer.Option(None, help="CSV file with a 'domain' column"),
	out: Optional[Path] = typer.Option(None, help="Output path; infers format by extension (.csv, .parquet)"),
	max_pages: int = typer.Option(5, help="Max pages to crawl per site"),
	timeout: float = typer.Option(10.0, help="Request timeout seconds"),
	concurrency: int = typer.Option(5, help="Concurrent connections"),
):
	"""Enrich a list of domains into a scored lead list."""
	domain_list = _parse_domains(domains, file)
	if not domain_list:
		rprint("[yellow]No domains provided.[/yellow]")
		typer.Exit(code=1)
	options = EnrichmentOptions(max_pages=max_pages, timeout_seconds=timeout, concurrency=concurrency)
	leads = asyncio.run(enrich_domains_async(domain_list, options))
	df = leads_to_dataframe(leads)
	if out is None:
		# show small preview
		rprint(df.head(20))
		return
	out = Path(out)
	out.parent.mkdir(parents=True, exist_ok=True)
	if out.suffix.lower() == ".parquet":
		df.to_parquet(out, index=False)
		rprint(f"[green]Wrote {len(df)} rows to {out}[/green]")
	else:
		df.to_csv(out, index=False)
		rprint(f"[green]Wrote {len(df)} rows to {out}[/green]")


if __name__ == "__main__":
	app()
