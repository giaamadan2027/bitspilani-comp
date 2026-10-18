import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from datetime import datetime, timezone

st.set_page_config(page_title="FINTRACE AI | Evidence Investigator", page_icon="🔎", layout="wide")
st.title("🔎 FINTRACE AI")
st.caption("Beyond the Numbers · Track C — Consumer, FMCG & Retail")
st.info("Working prototype: public HTML evidence retrieval, transparent financial calculations, and an adversarial review checklist. Autonomous source discovery, independent triangulation, and agent-driven falsification are planned, not yet implemented.")

SOURCES = {
    "Hindustan Unilever": [
        ("HUL FY26 performance", "https://hul-performance-highlights.hul.co.in/performance-highlights-fy-2025-2026/performance/financial/", "Company performance"),
        ("HUL March 2026 results", "https://www.hul.co.in/news/press-releases/2026/march-quarter-and-financial-year-2026-results/", "Company results"),
        ("NSE HUL filing", "https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_INDAS_179457_28072026194155_iXBRL_WEB.html", "Exchange filing")
    ],
    "Custom company / URLs": []
}
company = st.selectbox("Company", list(SOURCES))
urls = st.text_area("Additional public HTTPS source URLs (one per line)", height=95, placeholder="https://example.com/investor-relations/...")

def fetch_evidence(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("A valid HTTPS URL is required")
    response = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0 (compatible; FINTRACE research prototype)"})
    response.raise_for_status()
    ctype = response.headers.get("Content-Type", "")
    if "html" not in ctype.lower() and "text" not in ctype.lower():
        raise ValueError("This prototype supports HTML/text pages; PDF parsing is planned.")
    soup = BeautifulSoup(response.text, "html.parser")
    for el in soup(["script", "style", "nav", "footer", "header"]):
        el.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:100000]

if st.button("Collect and inspect public evidence", type="primary"):
    entries = SOURCES[company] + [
        (f"Custom source {i+1}", url.strip(), "User-supplied")
        for i, url in enumerate(urls.splitlines()) if url.strip()
    ]
    if not entries:
        st.warning("Add at least one source URL.")
    else:
        records = []
        with st.spinner("Fetching sources…"):
            for name, url, kind in entries:
                try:
                    txt = fetch_evidence(url)
                    matches = list(re.finditer(r"(?i)underlying (?:sales|volume) growth|turnover|receivables|inventory|quick commerce|revenue", txt))[:12]
                    excerpts = [txt[max(0,m.start()-110):min(len(txt),m.end()+180)] for m in matches]
                    records.append({"Source":name,"Type":kind,"URL":url,"Retrieved UTC":datetime.now(timezone.utc).isoformat(timespec="seconds"),"Text length":len(txt),"Evidence excerpts":"\n\n".join(excerpts[:8]) or "No matching terms found"})
                except Exception as exc:
                    records.append({"Source":name,"Type":kind,"URL":url,"Retrieved UTC":"FAILED","Text length":0,"Evidence excerpts":str(exc)})
        st.session_state["records"] = records

if "records" in st.session_state:
    st.subheader("Evidence ledger")
    for record in st.session_state["records"]:
        with st.expander(f"{record['Source']} — {record['Retrieved UTC']}"):
            st.markdown(f"[Open original source]({record['URL']}) · {record['Type']}")
            st.write(record["Evidence excerpts"])
    st.download_button("Export evidence log (CSV)", pd.DataFrame(st.session_state["records"]).to_csv(index=False).encode("utf-8"), "evidence_log.csv", "text/csv")

st.subheader("Hypothesis lab — transparent calculations")
st.caption("Enter verified, period-matched financial figures. Initial values illustrate HUL FY26 USG/UVG disclosure, not an autonomous discovery.")
a,b,c = st.columns(3)
with a:
    sales = st.number_input("Underlying sales growth (%)", value=5.0, step=0.1)
with b:
    vol = st.number_input("Underlying volume growth (%)", value=4.0, step=0.1)
with c:
    if vol <= -100:
        st.metric("Implied price/mix residual", "Not defined")
    else:
        residual = ((1 + sales/100) / (1 + vol/100) - 1) * 100
        st.metric("Implied price/mix residual", f"{residual:.2f}%")
st.caption("Multiplicative decomposition: (1 + sales growth)/(1 + volume growth) − 1. Only valid when reporting definitions, periods, and scopes align. A price/mix residual is not pure pricing.")
left,right = st.columns(2)
with left:
    rec = st.number_input("Trade receivables (₹ crore)", min_value=0.0, value=0.0)
    revenue = st.number_input("Comparable annual revenue (₹ crore)", min_value=0.0, value=0.0)
with right:
    prior = st.number_input("Prior receivable days", min_value=0.0, value=0.0)
    days = 365*rec/revenue if revenue>0 else None
    st.metric("Approximate receivable days", f"{days:.1f}" if days is not None else "Enter figures")
    if days is not None and prior>0:
        st.metric("Change vs prior (days)", f"{days-prior:+.1f}")
st.caption("Approximation: closing trade receivables / annual revenue × 365. Prefer average receivables and credit sales where disclosed. Match accounting scope.")

st.subheader("Adversarial review: counter-hypotheses")
for question in [
    "Could acquisitions, disposals or category mix explain the growth difference?",
    "Are periods and consolidated/standalone accounting scopes comparable?",
    "Do competitors exhibit the same sector-wide pattern?",
    "Could seasonality or changing credit terms explain receivables?",
    "Are two genuinely independent primary sources supporting the finding?"
]:
    st.checkbox(question)
st.warning("Evidence strength: UNASSESSED. Completing checkboxes does not establish source independence or prove a hypothesis.")
st.markdown('**Falsification template:** “This hypothesis would be weakened if [specific metric] returns to [defined threshold] for [number of periods], confirmed by [source].”')
