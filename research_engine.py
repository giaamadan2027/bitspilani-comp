"""FINTRACE AI research pipeline: best-effort public search, extraction, evidence ledger.
No discovery is asserted without cited evidence. Search coverage depends on public endpoints.
"""
from __future__ import annotations
import io, re, html, ipaddress, socket
from urllib.parse import urlparse, parse_qs, unquote, urljoin
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

HEADERS = {"User-Agent":"Mozilla/5.0 (compatible; FINTRACE-AI/0.2 public-finance-research)"}
TIMEOUT=11
MAX_BYTES=7_000_000
PRIMARY_DOMAINS=("nseindia.com","bseindia.com","hul.co.in","itcportal.com","nestle.in","britannia.co.in","dabur.com","marico.com","godrejcp.com","tataconsumer.com","colgatepalmolive.co.in","asianpaints.com","titancompany.in","trentlimited.com")
KEYWORDS=("volume growth","sales growth","price growth","pricing","price mix","product mix","receivable","inventory","working capital","quick commerce","distribution","channel","premiumisation","cash flow","rural","urban")
CLAIMS=("volume-led","demand-led","price-led","pricing-led","cash conversion","inventory reduction","distribution expansion","volume growth","volume decline","margin expansion","working capital improvement")

def valid_url(url):
    p=urlparse(url)
    if p.scheme!="https" or not p.hostname or p.username or p.password:
        return False
    host=p.hostname.lower()
    if host in ("localhost","localhost.localdomain") or host.endswith((".local",".internal",".localhost")):
        return False
    try:
        addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        if not addresses: return False
        if any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):
            return False
    except (OSError, ValueError):
        return False
    return True

def get_public(url):
    if not valid_url(url): raise ValueError("HTTPS URL must resolve to a public host.")
    # Disable redirects; validate each destination to limit SSRF.
    for _ in range(4):
        with requests.get(url,headers=HEADERS,timeout=TIMEOUT,stream=True,allow_redirects=False) as r:
            if r.status_code in (301,302,303,307,308):
                target=urljoin(url,r.headers.get("Location",""))
                if not valid_url(target): raise ValueError("Unsafe redirect")
                url=target
                continue
            r.raise_for_status()
            size=0
            raw=bytearray()
            for part in r.iter_content(chunk_size=65536):
                raw.extend(part); size+=len(part)
                if size>MAX_BYTES: raise ValueError("Document exceeds 7MB limit")
            return bytes(raw),r.headers.get("Content-Type",""),url
    raise ValueError("Too many redirects")

def discover(company, limit=10):
    """Find candidate public sources via Bing HTML and Google News RSS (best effort)."""
    queries=[f'"{company}" investor relations annual report financial results',
             f'"{company}" quarterly results volume growth receivables',
             f'"{company}" investor presentation earnings transcript']
    hits=[]; seen=set(); errors=[]
    for q in queries:
        try:
            raw,_,_=get_public("https://www.bing.com/search?q="+requests.utils.quote(q))
            soup=BeautifulSoup(raw,"html.parser")
            for a in soup.select("li.b_algo h2 a"):
                url=a.get("href","")
                if not url.startswith("https://") or url in seen: continue
                seen.add(url)
                hits.append({"title":a.get_text(" ",strip=True)[:150],"url":url,"discovered_via":"Public web search","query":q})
        except Exception as ex: errors.append("Web search unavailable: "+str(ex)[:100])
    try:
        q=requests.utils.quote(f'"{company}" financial results investor presentation')
        raw,_,_=get_public("https://news.google.com/rss/search?q="+q+"&hl=en-IN&gl=IN&ceid=IN:en")
        soup=BeautifulSoup(raw,"xml")
        for item in soup.find_all("item")[:12]:
            link=(item.link.get_text(strip=True) if item.link else "")
            if link.startswith("https://") and link not in seen:
                seen.add(link)
                hits.append({"title":item.title.get_text(" ",strip=True) if item.title else "News item","url":link,"discovered_via":"Google News RSS","query":company})
    except Exception as ex: errors.append("News search unavailable: "+str(ex)[:100])
    def rank(hit):
        host=urlparse(hit["url"]).hostname or ""
        score=(4 if any(host.endswith(d) for d in PRIMARY_DOMAINS) else 0)
        title=hit["title"].lower()
        score+=2*sum(s in title for s in ("annual report","financial results","investor presentation","quarterly results"))
        score+=sum(s in title for s in ("volume","fmcg","revenue","earnings"))
        return score
    return sorted(hits,key=rank,reverse=True)[:limit],errors

def extract_document(url):
    raw,ctype,final_url=get_public(url)
    if raw[:4]==b"%PDF" or "application/pdf" in ctype.lower():
        pdf=PdfReader(io.BytesIO(raw))
        texts=[]
        for i,page in enumerate(pdf.pages[:35],1):
            s=page.extract_text() or ""
            if s.strip(): texts.append((f"p. {i}",s))
        if not texts: raise ValueError("Scanned or image-only PDF: no extractable text")
        return final_url,"PDF",texts
    if not ("text/html" in ctype.lower() or "text/plain" in ctype.lower() or raw[:200].lstrip().startswith(b"<")):
        raise ValueError("Unsupported file format")
    soup=BeautifulSoup(raw,"html.parser")
    for tag in soup(["script","style","nav","footer","header"]):tag.decompose()
    text=soup.get_text(" ",strip=True)
    return final_url,"HTML",[("webpage",text)]

def excerpts(pages, max_items=9):
    output=[]
    for page,text in pages:
        clean=re.sub(r"\s+"," ",text)
        for keyword in KEYWORDS:
            m=re.search(r"(?i)\b"+re.escape(keyword)+r"\b",clean)
            if not m:continue
            snippet=clean[max(0,m.start()-135):min(len(clean),m.end()+240)]
            if not any(snippet[:50]==x["excerpt"][:50] for x in output):
                output.append({"page":page,"topic":keyword,"excerpt":snippet})
            if len(output)>=max_items: return output
    return output

def investigate(company, sources, max_sources=7):
    records=[]; failures=[]
    for hit in sources[:max_sources]:
        url=hit["url"]
        try:
            final_url,kind,pages=extract_document(url)
            findings=excerpts(pages)
            records.append({"title":hit.get("title",url),"url":final_url,"format":kind,
                            "discovered_via":hit.get("discovered_via","Provided by researcher"),
                            "retrieved_utc":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                            "excerpts":findings,"pages_read":len(pages)})
        except Exception as ex:
            failures.append({"url":url,"error":str(ex)[:180]})
    return records,failures

def investigate_claims(records):
    """Rule-based *leads*, not validated contradiction decisions."""
    leads=[]
    for rec in records:
        for x in rec["excerpts"]:
            t=x["excerpt"].lower()
            if any(k in t for k in CLAIMS):
                leads.append({"candidate_claim":x["topic"],"snippet":x["excerpt"],
                              "url":rec["url"],"page":x["page"],"status":"Unverified lead"})
    return leads[:20]

def cross_check(records):
    """Count distinct registrable-ish hosts. Different documents on one host are NOT independent."""
    hosts=set()
    for x in records:
        host=urlparse(x["url"]).hostname or ""
        hosts.add(host.removeprefix("www."))
    return len(hosts)
