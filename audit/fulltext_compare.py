"""원문 표본: 초록 판정(manual_codes_all.json)과 원문 판정(fulltext_codes.json 1차 18편 + fulltext_codes2.json 2차 43편) 비교 → fulltext_compare.json.
원문은 초록을 포함하므로 원문 판정이 초록 판정보다 낮으면 초록 판정 값으로 맞춘다."""
import json, math
C = json.load(open("audit/manual_codes_all.json")); F1 = json.load(open("audit/fulltext_codes.json")); F2 = json.load(open("audit/fulltext_codes2.json"))
for F in (F1, F2):
    for rid, f in F.items():
        for k in f: f[k] = max(f[k], C[rid][k])
json.dump(F1, open("audit/fulltext_codes.json", "w"), ensure_ascii=False)
F = {**F1, **F2}
tests = {"B1": lambda c: c["B1"] == 1, "B2>=1": lambda c: c["B2"] >= 1, "B2=2": lambda c: c["B2"] == 2, "T1": lambda c: c["T1"] == 1,
         "E>=2": lambda c: c["E"] >= 2, "Q": lambda c: c["Q"] == 1, "R>=1": lambda c: c["R"] >= 1, "R=3": lambda c: c["R"] == 3, "S2=2": lambda c: c["S2"] == 2}
def lev(c):
    if not (c["B1"] == 1 and c["B2"] >= 1): return 0
    if not c["T1"]: return 1
    if not (c["E"] >= 2 and c["Q"]): return 2
    return 3 if c["R"] != 3 else 4
LV = json.load(open("audit/levels.json"))["levels"]
def summ(F, note):
    n = len(F); out = {"n": n, "note": note}
    for k, t in tests.items():
        a = sum(t(C[r]) for r in F); b = sum(t(F[r]) for r in F)
        out[k] = {"abstract": a, "fulltext": b, "abs_pct": round(100 * a / n, 1), "ft_pct": round(100 * b / n, 1),
                  "added_by_ft": sum(t(F[r]) and not t(C[r]) for r in F), "removed_by_ft": sum(t(C[r]) and not t(F[r]) for r in F)}
    out["level_abs"] = {str(k): sum(1 for r in F if LV[r] == k) for k in range(5)}
    out["level_ft"] = {str(k): sum(1 for r in F if lev(F[r]) == k) for k in range(5)}
    out["level4_ft"] = [r for r in F if lev(F[r]) == 4]
    out["level_raised"] = sum(1 for r in F if lev(F[r]) > LV[r])
    return out
M2 = json.load(open("audit/fulltext2_meta.json"))
res = {"all": summ(F, f"1차: 공개 접근 원문 46편 시도, 20편 확보, 판독 불가 2편 제외(18편). 2차: 공개 접근 후보 {M2['attempted']}편 시도, {M2['retrieved']}편 확보, 판독 불가 {len(M2['unreadable'])}편 제외({M2['coded']}편)."),
       "first": summ(F1, "1차 표본 18편(R=3 6편 전부 포함 의도 표본)"), "second": summ(F2, "2차 표본 43편(공개 접근 원문 확보분)")}
# 전체 193편에 원문 판정을 반영한 근거 수준
Call = {r: (F[r] if r in F else C[r]) for r in C}
res["corpus_with_ft"] = {"level_cum": {f">={k}": sum(1 for r in Call if lev(Call[r]) >= k) for k in range(1, 5)}, "n": len(Call)}
json.dump(res, open("audit/fulltext_compare.json", "w"), ensure_ascii=False, indent=1)
for key in ("first", "second", "all"):
    o = res[key]; print(key, o["n"], {k: (v["abstract"], v["fulltext"]) for k, v in o.items() if isinstance(v, dict) and "abstract" in v}, o["level_abs"], o["level_ft"], o["level4_ft"])
print(res["corpus_with_ft"])
