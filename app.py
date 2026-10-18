import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from research_engine import discover, investigate, investigate_claims, cross_check

st.set_page_config(page_title="FINTRACE AI | Financial Investigator",page_icon="🔎",layout="wide")
st.markdown("""<style>
.block-container {padding-top:2rem;max-width:1250px}
[data-testid="stMetric"] {border:1px solid #dfe6ec;border-radius:12px;padding:12px}
</style>""",unsafe_allow_html=True)
st.title("🔎 FINTRACE AI")
st.caption("BEYOND THE NUMBERS · ATMOS 2026 · TRACK C — CONSUMER, FMCG & RETAIL")
st.markdown("**Autonomous source discovery → Evidence extraction → Financial hypothesis lab → Adversarial checks → Downloadable research brief**")
st.warning("Research preview, not investment advice. Search and extraction are automated; hypotheses and contradiction leads are NOT automatically verified. Finance calculations require verified input until structured extraction is implemented.")

with st.sidebar:
    st.header("Research settings")
    company=st.text_input("Company to investigate",value="Hindustan Unilever")
    st.caption("Works with company names beyond the example; source access and disclosure quality vary.")
    max_sources=st.slider("Maximum sources to fetch",2,10,6)
    st.info("Public HTTPS pages and text-based PDFs supported. Some exchange websites block automated retrieval.")
    st.markdown("[GitHub source code](https://github.com/giaamadan2027/bitspilani-comp)")

tab1,tab2,tab3,tab4=st.tabs(["🔍 Discover sources","📑 Evidence & hypotheses","📊 Financial analysis","🧾 Export research brief"])

with tab1:
    st.subheader("1 · Search for public company disclosures")
    st.write("Search investor relations, financial results, industry news and investor presentations, then choose sources for extraction.")
    if st.button("Discover public sources",type="primary"):
        with st.spinner("Searching public indexes…"):
            hits,issues=discover(company,limit=14)
        st.session_state["hits"]=hits
        st.session_state["issues"]=issues
        st.session_state.pop("records",None)
    for issue in st.session_state.get("issues",[]):
        st.caption("Search note: "+issue)
    hits=st.session_state.get("hits",[])
    if hits:
        st.dataframe(pd.DataFrame(hits)[["title","url","discovered_via"]],use_container_width=True,hide_index=True)
    else:
        st.info("Search results will appear here. Automated public search may be blocked; enter official URLs below instead.")
    with st.form("sources"):
        manual=st.text_area("Add official HTTPS sources, one URL per line",height=100,placeholder="https://www.company.com/investors/annual-report.pdf")
        st.caption("For a credible demo, prioritize official investor-relations documents, NSE/BSE disclosures and company earnings presentations.")
        run=st.form_submit_button("Investigate sources",type="primary")
    if run:
        chosen=list(hits)
        for i,url in enumerate(manual.splitlines()):
            url=url.strip()
            if url:
                chosen.insert(i,{"title":f"Researcher-supplied source {i+1}","url":url,"discovered_via":"User supplied"})
        if not chosen:st.error("Discover sources or enter at least one official source URL.")
        else:
            with st.spinner("Retrieving documents and extracting evidence…"):
                records,failures=investigate(company,chosen,max_sources)
            st.session_state["records"]=records
            st.session_state["failures"]=failures
            st.session_state["research_company"]=company
            st.success(f"Retrieved {len(records)} source(s); {len(failures)} failed.")
            st.caption("Open the Evidence tab for page-linked excerpts.")

with tab2:
    records=st.session_state.get("records",[])
    st.subheader("2 · Auditable evidence ledger")
    if records:
        a,b,c=st.columns(3)
        a.metric("Documents accessed",len(records))
        b.metric("Distinct source hosts",cross_check(records))
        c.metric("Extracted excerpts",sum(len(r["excerpts"]) for r in records))
        st.caption("Different hosts are a rough provenance indicator, NOT proof of independent corroboration.")
        for i,rec in enumerate(records,1):
            with st.expander(f"{i:02d} · {rec['title'][:85]} · {rec['format']}"):
                st.markdown(f"**Original:** [{rec['url']}]({rec['url']})")
                st.caption(f"Retrieved {rec['retrieved_utc']} · {rec['pages_read']} extracted page(s) · {rec['discovered_via']}")
                for x in rec["excerpts"]:
                    st.markdown(f"**{x['topic']} · {x['page']}**")
                    st.write(x["excerpt"])
        st.subheader("3 · Potential contradiction / hypothesis leads")
        leads=investigate_claims(records)
        st.caption("These are keyword-linked research leads, not verified contradictions. Compare comparable periods, units and reporting definitions before claiming inconsistency.")
        if leads:
            st.dataframe(pd.DataFrame(leads)[["candidate_claim","snippet","url","page","status"]],hide_index=True,use_container_width=True)
        else:st.info("No claim leads found in extracted excerpts.")
    else:st.info("Run source investigation first.")
    if st.session_state.get("failures"):
        with st.expander("Retrieval failures and limitations"):
            st.dataframe(pd.DataFrame(st.session_state["failures"]),hide_index=True,use_container_width=True)

with tab3:
    st.subheader("4 · Reproducible financial calculations")
    st.write("Enter values from verified financial statements. Do not mix standalone/consolidated or different reporting periods.")
    l,r=st.columns(2)
    with l:
        usg=st.number_input("Underlying sales growth (%)",value=5.0,step=0.1)
        uvg=st.number_input("Underlying volume growth (%)",value=4.0,step=0.1)
        if uvg>-100:
            residual=100*((1+usg/100)/(1+uvg/100)-1)
            st.metric("Implied price/mix residual",f"{residual:.2f}%")
        else:
            residual=None;st.error("UVG must be greater than -100%.")
        st.caption("Illustrative defaults reflect previously reported HUL FY26 metrics. Residual is not pure price inflation; volume definitions can include product mix.")
    with r:
        receivables=st.number_input("Average trade receivables (₹ crore)",min_value=0.0,value=0.0)
        sales=st.number_input("Annual credit sales / proxy revenue (₹ crore)",min_value=0.0,value=0.0)
        recdays=(receivables/sales*365 if sales>0 else None)
        st.metric("Approx. receivable days",f"{recdays:.1f}" if recdays is not None else "Enter figures")
        st.caption("Prefer average receivables ÷ credit sales × 365; state when revenue is a proxy.")
    st.subheader("5 · Self-falsification checks")
    checklist=[
        "Find a rival primary-source explanation for the observed trend",
        "Verify dates, accounting basis and metric definitions",
        "Compare at least one peer over comparable periods",
        "Test whether acquisition/divestment, seasonality or product mix explains the pattern",
        "Identify a measurable future condition that would overturn the hypothesis",
        "Downgrade or reject findings that lack independent evidence"
    ]
    chosen=[]
    for i,item in enumerate(checklist):
        if st.checkbox(item,key="check_"+str(i)): chosen.append(item)
    hypothesis=st.text_area("Working hypothesis (not an established discovery)",placeholder="Company X appears to have ...")
    opposing=st.text_area("Strongest counterargument / disconfirming evidence",placeholder="An alternative explanation may be ...")
    falsifier=st.text_area("Falsification condition",placeholder="This interpretation would weaken if ...")
    st.session_state["manual_findings"]={"hypothesis":hypothesis,"counterargument":opposing,"falsification":falsifier,"checks":chosen}
    st.info("Evidence strength remains UNASSESSED until an analyst validates claim-source alignment, corroboration and counterevidence.")

with tab4:
    st.subheader("6 · Export research brief")
    records=st.session_state.get("records",[])
    findings=st.session_state.get("manual_findings",{})
    if not records:
        st.info("Investigate at least one source to export a report.")
    else:
        payload={
            "company":st.session_state.get("research_company",company),
            "generated_utc":datetime.now(timezone.utc).isoformat(),
            "status":"RESEARCH PREVIEW — not an independently verified autonomous discovery",
            "evidence_strength":"UNASSESSED",
            "source_count":len(records),
            "distinct_source_hosts":cross_check(records),
            "candidate_leads":investigate_claims(records),
            "working_hypothesis":findings.get("hypothesis",""),
            "counterargument":findings.get("counterargument",""),
            "falsification_condition":findings.get("falsification",""),
            "adversarial_review_checked":findings.get("checks",[]),
            "sources":records,"retrieval_failures":st.session_state.get("failures",[])
        }
        md=[
            "# FINTRACE AI — Research Preview",
            f"Company: {payload['company']}",
            f"Generated: {payload['generated_utc']}",
            "**Status: unverified research preview; not an investment recommendation.**",
            "## Working hypothesis",
            payload["working_hypothesis"] or "Not yet developed.",
            "## Why it matters",
            "To be established from verified findings.",
            "## Financial calculations",
            "Reproduce values in the Financial Analysis tab using primary-source figures.",
            "## Timeline",
            "Not validated; dated source events require analyst review.",
            "## Counterargument",
            payload["counterargument"] or "Not yet assessed.",
            "## Falsification condition",
            payload["falsification_condition"] or "Not yet specified.",
            "## Evidence strength",
            "UNASSESSED (do not claim Strong/Moderate/Weak before validation).",
            "## Traceable source excerpts"
        ]
        for i,s in enumerate(records,1):
            md.extend([f"### [{i}] {s['title']}",s["url"],f"Retrieved: {s['retrieved_utc']}"])
            for x in s["excerpts"]:
                md.append(f"- {x['page']} — {x['topic']}: {x['excerpt']}")
        st.download_button("Download research brief (.md)","\n\n".join(md),"fintrace_research_brief.md","text/markdown")
        st.download_button("Download full evidence ledger (.json)",json.dumps(payload,indent=2,ensure_ascii=False),"fintrace_evidence.json","application/json")
        st.download_button("Download evidence table (.csv)",pd.DataFrame([{"title":s["title"],"url":s["url"],"page":x["page"],"topic":x["topic"],"excerpt":x["excerpt"]} for s in records for x in s["excerpts"]]).to_csv(index=False),"fintrace_evidence.csv","text/csv")
        st.success("The exported brief includes evidence links and explicit uncertainty labels.")

st.divider()
st.caption("FINTRACE AI · Experimental research tool · Public information only · No investment recommendations")
