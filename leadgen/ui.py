from __future__ import annotations
import asyncio
from io import StringIO

import streamlit as st
import pandas as pd

from .models import EnrichmentOptions
from .enrich import enrich_domains_async, leads_to_dataframe


def _download_button(df: pd.DataFrame, label: str, file_name: str):
	csv_bytes = df.to_csv(index=False).encode("utf-8")
	st.download_button(label, csv_bytes, file_name=file_name, mime="text/csv")


def main():
	st.set_page_config(page_title="LeadGen", layout="wide")
	st.title("LeadGen: High-signal lead enrichment")

	with st.sidebar:
		st.header("Options")
		max_pages = st.slider("Max pages per site", min_value=1, max_value=15, value=5)
		timeout = st.slider("Timeout (seconds)", min_value=3, max_value=30, value=10)
		concurrency = st.slider("Concurrency", min_value=1, max_value=10, value=5)

	tab1, tab2 = st.tabs(["Paste domains", "Upload CSV"])

	domains: list[str] = []
	with tab1:
		text = st.text_area("Domains (one per line)", height=180, placeholder="acme.com\nfoo.io")
		if text:
			domains.extend([d.strip() for d in text.splitlines() if d.strip()])
	with tab2:
		file = st.file_uploader("CSV with 'domain' or 'url' column", type=["csv"])
		if file is not None:
			df = pd.read_csv(file)
			col = None
			for c in ("domain", "url", "website", "website_url"):
				if c in df.columns:
					col = c
					break
			if col:
				domains.extend(df[col].astype(str).tolist())
			else:
				st.error("CSV must contain a 'domain' or 'url' column")

	if st.button("Enrich leads", type="primary", disabled=not domains):
		with st.spinner("Enriching..."):
			options = EnrichmentOptions(max_pages=max_pages, timeout_seconds=timeout, concurrency=concurrency)
			leads = asyncio.run(enrich_domains_async(domains, options))
			df = leads_to_dataframe(leads)
			st.success(f"Done. {len(df)} rows")
			st.dataframe(df, use_container_width=True)
			_download_button(df, "Download CSV", "leads.csv")


if __name__ == "__main__":
	main()
