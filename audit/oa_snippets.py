"""공개 접근(OA) 원문 표본의 판정용 발췌 추출. GitHub Actions에서 실행한다.

입력: audit/oa_targets.json [{id, pdf_url}]
출력: audit/snippets/<id>.txt — 판정 항목(비교 기준·생물학 근거·전이 절차·지속가능성 근거)에 해당하는
      핵심어 주변 문장만 모은 발췌. 원문 전체는 저장하지 않으며, 발췌는 저장소에 커밋하지 않고
      7일 보관 산출물(artifact)로만 남긴다.
"""
import json, os, re, subprocess, urllib.request, time

UA = "Mozilla/5.0 (biomimetic-audit/1.0)"
KEYS = {
    "baseline": r"(baseline|reference case|base case|compared (with|to)|comparison|conventional|static shading|fixed shading|benchmark|without shading|unshaded|venetian|roller)",
    "biology": r"(biolog|organism|species|plant|animal|mechanism|stomat|pine ?cone|leaf|skin|termite|cactus|botan|zoolog)",
    "transfer": r"(ISO 18458|abstraction|transfer|top-down|bottom-up|problem-driven|solution-driven|BioTRIZ|design spiral|analogy)",
    "sustain": r"(life ?cycle|LCA|embodied|carbon|sustainab|environmental impact|cost)",
    "result": r"(\d+(\.\d+)?\s?%|kWh|reduc|sav)",
}


def sentences(text):
    text = re.sub(r"\s+", " ", text)
    return re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)


def main():
    os.makedirs("audit/snippets", exist_ok=True)
    targets = json.load(open("audit/oa_targets.json", encoding="utf-8"))
    log = []
    for t in targets:
        pid, url = t["id"], t["pdf_url"]
        pdf = f"/tmp/{pid}.pdf"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r, open(pdf, "wb") as f:
                f.write(r.read())
            txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, timeout=120).stdout
        except Exception as e:  # noqa
            log.append({"id": pid, "ok": False, "err": str(e)[:200]})
            continue
        if len(txt) < 2000:
            log.append({"id": pid, "ok": False, "err": "no text"})
            continue
        ss = sentences(txt)
        # 참고문헌 이후는 제외
        cut = next((i for i, s in enumerate(ss) if re.match(r"^(References|REFERENCES|Bibliography)\b", s.strip())), len(ss))
        ss = ss[:cut]
        out = [f"# {pid}  chars={len(txt)}  sentences={len(ss)}"]
        for k, pat in KEYS.items():
            hits = [s for s in ss if re.search(pat, s, re.I)][:25]
            out.append(f"\n## {k} ({len(hits)})")
            out += ["- " + s[:400] for s in hits]
        open(f"audit/snippets/{pid}.txt", "w", encoding="utf-8").write("\n".join(out))
        log.append({"id": pid, "ok": True, "n_sent": len(ss)})
        time.sleep(1)
    json.dump(log, open("audit/snippets/_log.json", "w"), indent=1)
    print(sum(x["ok"] for x in log), "/", len(log))


if __name__ == "__main__":
    main()
