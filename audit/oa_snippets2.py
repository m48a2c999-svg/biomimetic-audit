"""원문 판정 확대용 발췌(GitHub Actions에서 실행).

입력: audit/oa_targets2.json [{id, urls, items}] — items는 초록 판정(재점검 뒤)이다.
각 연구의 공개 원문(PDF)을 받아, 초록 판정에서 아직 최고 수준이 아닌 항목만 골라 그 항목을 판정할 수 있는
문장을 짧게 발췌한다. 원문 전체는 저장하지 않으며, 발췌는 암호화해 별도 브랜치로만 전달한다.
"""
import json, os, re, subprocess, urllib.request, urllib.parse, time, html

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 biomimetic-audit"
PAT = {
    "R": r"(compar\w+ (with|to|against)|baseline|reference (case|model|building)|base ?case|conventional|static (shading|facade|façade)|fixed (shading|louver|blind)|venetian|roller|benchmark|without (the )?(shading|device|facade|façade)|unshaded|generic|typical (facade|façade|building)|non-?bio)",
    "T1": r"(ISO 18458|abstraction|abstract(ed)? (principle|model)|transfer(red)? (to|into)|top-?down|bottom-?up|problem-?driven|solution-?driven|BioTRIZ|design spiral|AskNature|biomimetic design (process|method)|analog(y|ical))",
    "B2": r"(mechanism|cells?\b|tissue|swell|turgor|hygroscop|bilayer|stomat|guard cell|scale[s]? (of|open|close)|microstructur|nanostructur|epiderm|cuticle|vascular|thermoregulat|evaporat)",
    "B1": r"(inspired by (the )?[a-z]+|species|organism|plant|animal|insect|leaf|leaves|flower|tree|cactus|termite|pine ?cone|lotus|beetle|butterfly|skin of)",
    "E": r"(EnergyPlus|simulat|prototype|mock-?up|experiment|test(ed|ing) (in|under)|measur|monitor|field (test|study)|full-?scale|in situ|built (pavilion|building)|installed)",
    "Q": r"(\d+(\.\d+)?\s?(%|percent|kWh|°C|K\b|lux|lx|W/m))",
    "S2": r"(life ?cycle|LCA|embodied|cradle|global warming potential|GWP|end of life|recycl)",
}
CAP = {"R": 6, "T1": 5, "B2": 5, "B1": 3, "E": 4, "Q": 3, "S2": 3}


def need(items):
    n = []
    if items["R"] < 3: n.append("R")
    if items["T1"] == 0: n.append("T1")
    if items["B2"] < 2: n.append("B2")
    if items["B1"] == 0: n.append("B1")
    if items["E"] < 4: n.append("E")
    if items["Q"] == 0: n.append("Q")
    if items["S1"] == 1 and items["S2"] < 2: n.append("S2")
    return n


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=45) as r:
        ct = r.headers.get("Content-Type", ""); data = r.read(40_000_000); final = r.geturl()
    return ct, data, final


def get_pdf(urls):
    tried = []
    queue = list(urls)
    while queue and len(tried) < 10:
        u = queue.pop(0)
        if u in tried: continue
        tried.append(u)
        try:
            ct, data, final = fetch(u)
        except Exception:
            continue
        if data[:4] == b"%PDF":
            return data, u
        if "html" in ct or data[:200].lower().find(b"<html") >= 0 or data[:15].lower().startswith(b"<!doctype"):
            h = data.decode("utf-8", "ignore")
            m = re.findall(r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)', h, re.I) + \
                re.findall(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url', h, re.I)
            for x in m:
                queue.insert(0, html.unescape(x))
            if "mdpi.com" in final and not final.rstrip("/").endswith("/pdf"):
                queue.insert(0, final.rstrip("/") + "/pdf")
            for x in re.findall(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', h, re.I)[:3]:
                queue.append(urllib.parse.urljoin(final, html.unescape(x)))
    return None, None


def sentences(text):
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", text)


def main():
    import urllib.parse  # noqa
    os.makedirs("audit/snippets2", exist_ok=True)
    T = json.load(open("audit/oa_targets2.json", encoding="utf-8"))
    log = []
    for t in T:
        pid = t["id"]; n = need(t["items"])
        data, src = get_pdf(t["urls"])
        if data is None:
            log.append({"id": pid, "ok": False}); continue
        open("/tmp/x.pdf", "wb").write(data)
        try:
            txt = subprocess.run(["pdftotext", "/tmp/x.pdf", "-"], capture_output=True, text=True, timeout=120).stdout
        except Exception:
            txt = ""
        if len(txt) < 3000:
            log.append({"id": pid, "ok": False, "err": "no text"}); continue
        ss = sentences(txt)
        cut = next((i for i, s in enumerate(ss) if re.match(r"^(References|REFERENCES|Bibliography|Acknowledg)", s.strip()) and i > len(ss) * 0.5), len(ss))
        ss = [s for s in ss[:cut] if 30 < len(s) < 900]
        out = [f"# {pid} | need {','.join(n)} | sentences {len(ss)} | src {src[:80]}"]
        for k in n:
            hits = []
            for s in ss:
                if re.search(PAT[k], s, re.I) and s not in hits:
                    hits.append(s)
                if len(hits) >= CAP[k]: break
            out.append(f"## {k} ({len(hits)})")
            out += ["- " + h[:300] for h in hits]
        open(f"audit/snippets2/{pid}.txt", "w", encoding="utf-8").write("\n".join(out))
        log.append({"id": pid, "ok": True, "n_sent": len(ss), "src": src})
        time.sleep(0.5)
    json.dump(log, open("audit/snippets2/_log.json", "w"), indent=1)
    print(sum(x["ok"] for x in log), "/", len(log))


if __name__ == "__main__":
    main()
