"""원문 표본 18편: 초록 판정(manual_codes_all.json)과 원문 판정(fulltext_codes.json) 비교 → fulltext_compare.json.
원문은 초록을 포함하므로 원문 판정이 초록 판정보다 낮으면 초록 판정 값으로 맞춘다."""
import json
C = json.load(open("audit/manual_codes_all.json")); F = json.load(open("audit/fulltext_codes.json"))
for rid, f in F.items():
    for k in f:
        f[k] = max(f[k], C[rid][k])
json.dump(F, open("audit/fulltext_codes.json", "w"), ensure_ascii=False)
tests = {"B1": lambda c: c["B1"] == 1, "B2>=1": lambda c: c["B2"] >= 1, "B2=2": lambda c: c["B2"] == 2, "T1": lambda c: c["T1"] == 1,
         "E>=2": lambda c: c["E"] >= 2, "Q": lambda c: c["Q"] == 1, "R>=1": lambda c: c["R"] >= 1, "R=3": lambda c: c["R"] == 3, "S2=2": lambda c: c["S2"] == 2}
n = len(F); out = {"n": n, "note": "공개 접근 원문 46편 시도, 20편 확보, 판독 불가 2편 제외"}
for k, t in tests.items():
    a = sum(t(C[r]) for r in F); b = sum(t(F[r]) for r in F)
    out[k] = {"abstract": a, "fulltext": b, "abs_pct": round(100 * a / n, 1), "ft_pct": round(100 * b / n, 1),
              "added_by_ft": sum(t(F[r]) and not t(C[r]) for r in F), "removed_by_ft": sum(t(C[r]) and not t(F[r]) for r in F)}
json.dump(out, open("audit/fulltext_compare.json", "w"), ensure_ascii=False, indent=1)
def lev(c):
    if not (c["B1"] == 1 and c["B2"] >= 1): return 0
    if not c["T1"]: return 1
    if not (c["E"] >= 2 and c["Q"]): return 2
    return 3 if c["R"] != 3 else 4
print({k: (v["abstract"], v["fulltext"]) for k, v in out.items() if isinstance(v, dict)}, "max ft level", max(lev(f) for f in F.values()))
