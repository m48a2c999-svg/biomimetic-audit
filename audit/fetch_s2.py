"""보완 수집: Semantic Scholar. (1) 같은 질의식의 제목·초록 검색, (2) OpenAlex에 초록이 없는 문헌의 초록 보완.
GitHub Actions에서 실행한다."""
import json, time, urllib.parse, urllib.request, urllib.error, sys, os, datetime

UA = "biomimetic-audit/1.0"
Q = ('("biomimetic" | "biomimicry" | "biomimetics" | "bio-inspired" | "bioinspired" | "nature-inspired" | '
     '"biologically inspired" | "bionic") + (facade | façade | facades | "building envelope" | "building envelopes" | '
     '"building skin" | "building skins" | "shading device" | "shading system" | "adaptive skin" | "kinetic facade" | '
     '"climate adaptive building shell")')
FIELDS = "title,abstract,year,externalIds,authors,venue,publicationTypes,citationCount,openAccessPdf,publicationDate"


def req(url, data=None):
    for k in range(8):
        try:
            r = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
            with urllib.request.urlopen(r, timeout=60) as f:
                return json.loads(f.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print("retry", k, e.code, file=sys.stderr)
            time.sleep(4 * (k + 1))
        except Exception as e:  # noqa
            print("retry", k, e, file=sys.stderr)
            time.sleep(4 * (k + 1))
    return None


def main():
    os.makedirs("audit/raw", exist_ok=True)
    out, token, total = [], None, None
    while True:
        p = {"query": Q, "fields": FIELDS, "year": "2000-2026"}
        if token:
            p["token"] = token
        d = req("https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(p))
        if not d:
            break
        total = d.get("total", total)
        out += d.get("data", [])
        token = d.get("token")
        time.sleep(1.5)
        if not token:
            break
    with open("audit/raw/s2_search.jsonl", "w", encoding="utf-8") as f:
        for w in out:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    # 초록 보완
    oa = [json.loads(l) for l in open("audit/raw/openalex.jsonl", encoding="utf-8")]
    ids = ["DOI:" + w["doi"].replace("https://doi.org/", "") for w in oa if not w.get("abstract") and w.get("doi")]
    filled = []
    for i in range(0, len(ids), 100):
        d = req("https://api.semanticscholar.org/graph/v1/paper/batch?fields=" + FIELDS,
                data=json.dumps({"ids": ids[i:i + 100]}).encode())
        for q, r in zip(ids[i:i + 100], d or []):
            if r:
                r["_query"] = q
                filled.append(r)
        time.sleep(1.5)
    with open("audit/raw/s2_abstracts.jsonl", "w", encoding="utf-8") as f:
        for w in filled:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    meta = {"query": Q, "year": "2000-2026", "retrieved_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"),
            "s2_total": total, "s2_written": len(out), "abstract_lookup": len(ids),
            "abstract_found": sum(1 for w in filled if w.get("abstract"))}
    json.dump(meta, open("audit/raw/s2_meta.json", "w"), indent=1, ensure_ascii=False)
    print(meta)


if __name__ == "__main__":
    main()
