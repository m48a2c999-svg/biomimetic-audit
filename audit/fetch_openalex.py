"""생체모방 건축 외피 문헌 수집 (OpenAlex). GitHub Actions에서 실행한다.

재현 정보: 질의식·기간·유형을 아래 상수로 고정하고, 실행 시각과 결과 건수를 meta에 기록한다.
연락처(polite pool)는 환경 변수 OPENALEX_MAILTO가 있을 때만 쓴다.
"""
import json, time, urllib.parse, urllib.request, datetime, sys, os

MAILTO = os.environ.get("OPENALEX_MAILTO", "")
UA = "biomimetic-audit/1.0"
BIO = ['"biomimetic"', '"biomimicry"', '"biomimetics"', '"bio-inspired"', '"bioinspired"',
       '"nature-inspired"', '"biologically inspired"', '"bionic"']
ENV = ['"facade"', '"façade"', '"facades"', '"façades"', '"building envelope"', '"building envelopes"',
       '"building skin"', '"building skins"', '"shading device"', '"shading system"',
       '"adaptive skin"', '"kinetic facade"', '"climate adaptive building shell"']
QUERY = "(" + " OR ".join(BIO) + ") AND (" + " OR ".join(ENV) + ")"
DATE_FROM, DATE_TO = "2000-01-01", "2026-11-22"
TYPES = "article|review|book-chapter"
SELECT = ("id,doi,title,display_name,publication_year,publication_date,type,language,cited_by_count,"
          "primary_location,open_access,authorships,abstract_inverted_index,topics,keywords,is_retracted,referenced_works_count")


def get(url, tries=5):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            print("retry", k, e, file=sys.stderr)
            time.sleep(5 * (k + 1))
    raise RuntimeError(url)


def abstract(inv):
    if not inv:
        return ""
    pos = []
    for w, idx in inv.items():
        for i in idx:
            pos.append((i, w))
    return " ".join(w for _, w in sorted(pos))


def page(flt):
    params = {"filter": flt, "per-page": 200, "page": 1, "select": SELECT}
    if MAILTO:
        params["mailto"] = MAILTO
    time.sleep(1.2)
    return get("https://api.openalex.org/works?" + urllib.parse.urlencode(params))


def windows():
    """커서 없이 1쪽(200건) 안에 들도록 기간을 나눈다: 연 단위 → 넘치면 월 단위."""
    for y in range(int(DATE_FROM[:4]), int(DATE_TO[:4]) + 1):
        a, b = f"{y}-01-01", min(f"{y}-12-31", DATE_TO)
        yield a, b


def main(out="audit/raw/openalex.jsonl"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    base = f"title_and_abstract.search:{QUERY},type:{TYPES}"
    seen, n, total, log = set(), 0, 0, []
    with open(out, "w", encoding="utf-8") as f:
        for a, b in windows():
            spans = [(a, b)]
            d = page(base + f",from_publication_date:{a},to_publication_date:{b}")
            cnt = d["meta"]["count"]
            if cnt > 200:
                import calendar
                y = int(a[:4])
                spans = [(f"{y}-{m:02d}-01", f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}") for m in range(1, 13)]
                spans = [(x, min(z, DATE_TO)) for x, z in spans if x <= DATE_TO]
                results = []
                for x, z in spans:
                    dd = page(base + f",from_publication_date:{x},to_publication_date:{z}")
                    if dd["meta"]["count"] > 200:
                        print("WARN month over 200", x, dd["meta"]["count"], file=sys.stderr)
                    results += dd["results"]
            else:
                results = d["results"]
            total += cnt
            log.append({"from": a, "to": b, "count": cnt, "got": len(results)})
            for w in results:
                if w["id"] in seen:
                    continue
                seen.add(w["id"])
                w["abstract"] = abstract(w.pop("abstract_inverted_index", None))
                f.write(json.dumps(w, ensure_ascii=False) + "\n")
                n += 1
    meta = {"query": QUERY, "filter_base": base, "date_from": DATE_FROM, "date_to": DATE_TO, "types": TYPES,
            "retrieved_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"),
            "openalex_count_sum": total, "written_unique": n, "windows": log}
    json.dump(meta, open("audit/raw/openalex_meta.json", "w"), ensure_ascii=False, indent=1)
    print(n, total)


if __name__ == "__main__":
    main()
