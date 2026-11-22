"""홈페이지용 판정 자료(docs/data/audit.json, audit.csv) 생성."""
import json, csv, re
C = json.load(open("audit/manual_codes_all.json")); L = json.load(open("audit/levels.json"))["levels"]
FT = json.load(open("audit/fulltext_codes.json"))
corpus = {json.loads(l)["id"]: json.loads(l) for l in open("audit/corpus.jsonl")}
first = {}
for l in open("audit/raw/openalex.jsonl"):
    w = json.loads(l); au = w.get("authorships") or []
    if au: first[w["id"].split("/")[-1]] = (au[0].get("author") or {}).get("display_name") or ""
for l in open("audit/raw/s2_search.jsonl"):
    w = json.loads(l); au = w.get("authors") or []
    if au:
        first.setdefault("S2_" + (w.get("paperId") or "")[:12], au[0].get("name") or "")
        d = ((w.get("externalIds") or {}).get("DOI") or "").lower()
        if d: first.setdefault("doi:" + d, au[0].get("name") or "")
def fa(rid):
    nm = first.get(rid) or first.get("doi:" + (corpus[rid].get("doi") or "").lower(), "")
    p = nm.split(); s = p[-1] if len(p) > 1 else nm
    if len(p) > 1 and re.fullmatch(r"(?:[A-Z]\.?){1,3}", p[-1].replace(".", "")+"") and len(p[-1]) <= 5: s = p[0]
    return (s.title() if s.isupper() else s) or "—"
Lk = {"form": "형태", "material": "구조·재료", "process": "과정·행동", "ecosystem": "생태계", "unclear": "불명"}
rows = []
for rid, c in C.items():
    d = corpus[rid]
    t = re.sub(r"\s+", " ", d.get("title") or "").strip()
    if t.isupper(): t = t.capitalize()
    rows.append(dict(id=rid, year=d.get("year"), author=fa(rid), title=t, venue=d.get("venue") or "", doi=d.get("doi") or "",
                     B1=c["B1"], B2=c["B2"], T1=c["T1"], L=Lk.get(c["L"], c["L"]), E=c["E"], Q=c["Q"], R=c["R"], S1=c["S1"], S2=c["S2"],
                     level=L[rid], fulltext=rid in FT))
rows.sort(key=lambda r: (r["year"] or 0, r["title"].lower()))
for i, r in enumerate(rows, 1): r["no"] = i
json.dump(rows, open("docs/data/audit.json", "w"), ensure_ascii=False)
with open("docs/data/audit.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows))
