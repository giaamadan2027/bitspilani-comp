# FINTRACE AI — Beyond the Numbers

**ATMOS 2026 · Track C — Consumer, FMCG & Retail**

**Live Streamlit application:** https://fintrace-ai-atmos.streamlit.app/

## What version 0.2 adds

- Company-name search across public web indexes and Google News RSS (best effort).
- User-supplied official financial sources as a reliable fallback.
- Extraction from public HTTPS HTML pages and text-based PDFs, with page-linked snippets.
- Evidence ledger with publication URL, retrieval timestamp, source excerpts and export to CSV/JSON.
- Candidate hypothesis/contradiction leads labeled **unverified**.
- Deterministic price/mix residual and indicative receivable-days calculations.
- Research checklist, counterargument and falsification fields.
- Downloadable Markdown research brief, with confidence clearly marked unassessed.

## Important limitations

This is **a research prototype**, not yet a fully autonomous financial discovery agent. Public web search may be blocked; some sites block automated retrieval, PDFs may be scanned, and underlying financial values are not yet automatically normalized. Host diversity alone does not validate independent source corroboration. Claim detection generates leads, **not established contradictions**. Counterarguments and falsification are currently human-assisted rather than autonomous. Do not interpret this tool's outputs as investment advice or verified discoveries.

## Launch

Streamlit Cloud: select `giaamadan2027/bitspilani-comp`, branch `main`, entrypoint `app.py`. Changes to `main` normally trigger a redeploy.

Local setup:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Demo flow

1. Enter a company and click **Discover public sources**.
2. Add at least one company investor-relations filing URL if public search does not return suitable results.
3. Click **Investigate sources**.
4. Inspect document excerpts and original links.
5. Enter verified growth and working-capital figures in **Financial analysis**.
6. Complete adversarial questions and download the research brief.

Use public data only. Verify all financial metrics and dates against original disclosures.
