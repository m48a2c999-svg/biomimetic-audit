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
            time.sleep(3 * (k + 1))
    raise RuntimeError(url)


def abstract(inv):
    if not inv:
        return ""
    pos = []
    for w, idx in inv.items():
        for i in idx:
            pos.append((i, w))
    return " ".join(w for _, w in sorted(pos))


def main(out="audit/raw/openalex.jsonl"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    flt = (f"title_and_abstract.search:{QUERY},from_publication_date:{DATE_FROM},"
           f"to_publication_date:{DATE_TO},type:{TYPES}")
    cursor, n, total = "*", 0, None
    with open(out, "w", encoding="utf-8") as f:
        while cursor:
            params = {"filter": flt, "per-page": 200, "cursor": cursor, "select": SELECT}
            if MAILTO:
                params["mailto"] = MAILTO
            d = get("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
            if total is None:
                total = d["meta"]["count"]
            for w in d["results"]:
                w["abstract"] = abstract(w.pop("abstract_inverted_index", None))
                f.write(json.dumps(w, ensure_ascii=False) + "\n")
                n += 1
            cursor = d["meta"].get("next_cursor")
            if not d["results"]:
                break
            time.sleep(0.2)
    meta = {"query": QUERY, "filter": flt, "date_from": DATE_FROM, "date_to": DATE_TO, "types": TYPES,
            "retrieved_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"),
            "openalex_count": total, "written": n}
    json.dump(meta, open("audit/raw/openalex_meta.json", "w"), ensure_ascii=False, indent=1)
    print(meta)


if __name__ == "__main__":
    main()
