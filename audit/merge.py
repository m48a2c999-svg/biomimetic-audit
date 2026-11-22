"""OpenAlex + Semantic Scholar 결과를 합쳐 판정 후보 목록(audit/corpus.jsonl)을 만든다."""
import json, re, collections

def norm_t(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())[:120]

oa = [json.loads(l) for l in open("audit/raw/openalex.jsonl", encoding="utf-8")]
s2 = [json.loads(l) for l in open("audit/raw/s2_search.jsonl", encoding="utf-8")]
s2ab = {w["_query"][4:].lower(): w for w in (json.loads(l) for l in open("audit/raw/s2_abstracts.jsonl", encoding="utf-8"))}
recs, by_doi, by_t = [], {}, {}

def add(r):
    d = (r.get("doi") or "").lower()
    t = norm_t(r["title"])
    k = by_doi.get(d) if d else None
    if k is None:
        k = by_t.get(t)
    if k is not None:
        base = recs[k]
        base["sources"] = sorted(set(base["sources"] + r["sources"]))
        if not base.get("abstract") and r.get("abstract"):
            base["abstract"] = r["abstract"]; base["abstract_src"] = r["sources"][0]
        if not base.get("doi") and d:
            base["doi"] = d
        return
    recs.append(r); i = len(recs) - 1
    if d: by_doi[d] = i
    by_t[t] = i

for w in oa:
    d = (w.get("doi") or "").replace("https://doi.org/", "").lower()
    ab = w.get("abstract") or ""
    src_ab = "openalex" if ab else ""
    if not ab and d in s2ab and s2ab[d].get("abstract"):
        ab, src_ab = s2ab[d]["abstract"], "s2"
    aff = []
    for a in w.get("authorships", []):
        aff += a.get("raw_affiliation_strings") or []
        aff += [i.get("display_name", "") for i in a.get("institutions") or []]
    loc = (w.get("primary_location") or {}).get("source") or {}
    add(dict(id=w["id"].split("/")[-1], doi=d, title=w.get("title") or w.get("display_name") or "",
             year=w.get("publication_year"), type=w.get("type"), language=w.get("language"),
             venue=loc.get("display_name"), publisher=loc.get("host_organization_name"),
             cited=w.get("cited_by_count"), oa_url=(w.get("open_access") or {}).get("oa_url"),
             is_oa=(w.get("open_access") or {}).get("is_oa"),
             abstract=ab, abstract_src=src_ab, affiliations=aff,
             keywords=[k.get("display_name") for k in w.get("keywords") or []], sources=["openalex"]))
for w in s2:
    ex = w.get("externalIds") or {}
    d = (ex.get("DOI") or "").lower()
    add(dict(id="S2_" + (w.get("paperId") or "")[:12], doi=d, title=w.get("title") or "", year=w.get("year"),
             type=",".join(w.get("publicationTypes") or []), language=None, venue=w.get("venue"), publisher=None,
             cited=w.get("citationCount"), oa_url=(w.get("openAccessPdf") or {}).get("url"),
             is_oa=bool((w.get("openAccessPdf") or {}).get("url")),
             abstract=w.get("abstract") or "", abstract_src="s2" if w.get("abstract") else "",
             affiliations=[], keywords=[], sources=["s2"]))
with open("audit/corpus.jsonl", "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
c = collections.Counter(tuple(r["sources"]) for r in recs)
print(len(recs), c, "with abstract", sum(1 for r in recs if r["abstract"]))
