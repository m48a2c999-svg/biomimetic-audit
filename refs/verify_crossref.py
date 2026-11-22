"""참고문헌 DOI 서지 대조 (Crossref, OpenAlex 보조). GitHub Actions에서 실행한다.

입력: refs/refs_input.json  [{key, doi, title, year, first_author}]
출력: refs/refs_verified.json — Crossref 원 메타데이터(제목·저자·연도·학술지·권호·쪽)와 입력값 일치 여부
"""
import json, time, urllib.request, urllib.parse, urllib.error, difflib

UA = "biomimetic-audit/1.0"


def get(url):
    for k in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (k + 1))
        except Exception:
            time.sleep(2 * (k + 1))
    return None


def norm(s):
    return "".join(ch.lower() for ch in (s or "") if ch.isalnum())


def main():
    refs = json.load(open("refs/refs_input.json", encoding="utf-8"))
    out = []
    for r in refs:
        rec = dict(r)
        doi = (r.get("doi") or "").replace("https://doi.org/", "").strip()
        if not doi:
            # DOI가 없으면 제목으로 Crossref 검색해 상위 3건을 후보로 기록(확정은 사람이 함)
            if r.get("title") and r.get("type") in ("J", "C", "BC", "B"):
                q = urllib.parse.urlencode({"query.bibliographic": f"{r.get('title')} {r.get('first_author','')}", "rows": 3})
                s = get("https://api.crossref.org/works?" + q)
                cands = []
                for it in ((s or {}).get("message", {}).get("items", []) or []):
                    t = (it.get("title") or [""])[0]
                    cands.append({"doi": it.get("DOI"), "title": t,
                                  "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
                                  "container": (it.get("container-title") or [""])[0],
                                  "ratio": round(difflib.SequenceMatcher(None, norm(r.get("title")), norm(t)).ratio(), 3)})
                rec["candidates"] = cands
                rec["status"] = "candidate" if cands and cands[0]["ratio"] > 0.9 else "no_doi"
            else:
                rec["status"] = "no_doi"
            out.append(rec)
            continue
        d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
        if not d:
            o = get("https://api.openalex.org/works/doi:" + doi)
            if o:
                rec.update({"status": "openalex_only", "cr_title": o.get("display_name"),
                            "cr_year": o.get("publication_year"),
                            "cr_container": ((o.get("primary_location") or {}).get("source") or {}).get("display_name"),
                            "cr_authors": [a["author"]["display_name"] for a in o.get("authorships", [])]})
            else:
                rec["status"] = "doi_not_found"
            out.append(rec)
            continue
        m = d["message"]
        title = (m.get("title") or [""])[0]
        yr = None
        for k in ("published-print", "published-online", "issued"):
            if m.get(k, {}).get("date-parts"):
                yr = m[k]["date-parts"][0][0]
                break
        rec.update({
            "cr_title": title, "cr_year": yr,
            "cr_year_online": (m.get("published-online", {}).get("date-parts") or [[None]])[0][0],
            "cr_year_print": (m.get("published-print", {}).get("date-parts") or [[None]])[0][0],
            "cr_container": (m.get("container-title") or [""])[0],
            "cr_volume": m.get("volume"), "cr_issue": m.get("issue"), "cr_page": m.get("page"),
            "cr_article_number": m.get("article-number"),
            "cr_authors": [f"{a.get('family','')}, {a.get('given','')}".strip(", ") for a in m.get("author", [])],
            "cr_publisher": m.get("publisher"), "cr_type": m.get("type"),
            # 철회·정정 여부(Crossmark update-to / updated-by)
            "cr_updated_by": [{"type": u.get("type"), "doi": u.get("DOI"), "label": u.get("label")}
                              for u in (m.get("updated-by") or [])],
            "cr_update_to": [{"type": u.get("type"), "doi": u.get("DOI")} for u in (m.get("update-to") or [])],
        })
        # OpenAlex의 철회 표시도 함께 확인
        o = get("https://api.openalex.org/works/doi:" + doi)
        rec["oa_is_retracted"] = bool(o and o.get("is_retracted"))
        rec["title_ratio"] = round(difflib.SequenceMatcher(None, norm(r.get("title")), norm(title)).ratio(), 3)
        fa = norm(r.get("first_author"))
        rec["author_match"] = bool(fa) and bool(rec["cr_authors"]) and fa in norm(rec["cr_authors"][0])
        rec["year_match"] = r.get("year") in (rec["cr_year"], rec["cr_year_online"], rec["cr_year_print"])
        rec["status"] = "ok" if rec["title_ratio"] > 0.85 and rec["year_match"] else "check"
        out.append(rec)
        time.sleep(0.15)
    json.dump(out, open("refs/refs_verified.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(x["status"] for x in out))


if __name__ == "__main__":
    main()
