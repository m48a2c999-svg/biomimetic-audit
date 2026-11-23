"""민감도 분석: 표본 범위·자료원·판정 규칙·재판정 여부를 바꿔도 핵심 결과(수준 4 부재, 수준 ≥3 비율, 주요 항목 비율)가 유지되는지 확인."""
import json, math, collections
R = {json.loads(l)["id"]: json.loads(l) for l in open("audit/corpus.jsonl", encoding="utf-8")}
C = json.load(open("audit/manual_codes_all.json"))
C0 = json.load(open("audit/manual_codes_before_recheck.json"))
F = json.load(open("audit/fulltext_codes.json"))
def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))
def lv_base(c):
    L1 = c["B1"] == 1 and c["B2"] >= 1; L2 = L1 and c["T1"] == 1; L3 = L2 and c["E"] >= 2 and c["Q"] == 1; L4 = L3 and c["R"] == 3
    return 4 if L4 else 3 if L3 else 2 if L2 else 1 if L1 else 0
def lv_mech(c):  # 생물 근거를 기제 기술(B2=2)로 강화
    L1 = c["B1"] == 1 and c["B2"] == 2; L2 = L1 and c["T1"] == 1; L3 = L2 and c["E"] >= 2 and c["Q"] == 1; L4 = L3 and c["R"] == 3
    return 4 if L4 else 3 if L3 else 2 if L2 else 1 if L1 else 0
def lv_noT1(c):  # 전이 절차 요건 제외
    L1 = c["B1"] == 1 and c["B2"] >= 1; L2 = L1; L3 = L2 and c["E"] >= 2 and c["Q"] == 1; L4 = L3 and c["R"] == 3
    return 4 if L4 else 3 if L3 else 2 if L2 else 1 if L1 else 0
def lv_noQ(c):  # 성능 근거에서 정량 요건 제외
    L1 = c["B1"] == 1 and c["B2"] >= 1; L2 = L1 and c["T1"] == 1; L3 = L2 and c["E"] >= 2; L4 = L3 and c["R"] == 3
    return 4 if L4 else 3 if L3 else 2 if L2 else 1 if L1 else 0
def lv_R2(c):  # 정적 일반 장치(R=2)도 공정 비교로 인정
    L1 = c["B1"] == 1 and c["B2"] >= 1; L2 = L1 and c["T1"] == 1; L3 = L2 and c["E"] >= 2 and c["Q"] == 1; L4 = L3 and c["R"] >= 2
    return 4 if L4 else 3 if L3 else 2 if L2 else 1 if L1 else 0
def lv_loose(c):  # 가장 느슨한 규칙: T1·Q 요건 제외, R≥2 인정
    L1 = c["B1"] == 1 and c["B2"] >= 1; L3 = L1 and c["E"] >= 2; L4 = L3 and c["R"] >= 2
    return 4 if L4 else 3 if L3 else 1 if L1 else 0
def nonhier_C4(c): return c["E"] >= 2 and c["Q"] == 1 and c["R"] == 3  # 생물 근거와 무관한 공정 비교
ids = sorted(C)
def T(i): return R[i]["type"] or ""
subsets = {
    "전체(기준)": ids,
    "학술대회 논문 제외": [i for i in ids if "Conference" not in T(i)],
    "학술지 논문만": [i for i in ids if T(i) in ("article", "JournalArticle")],
    "OpenAlex 수록 문헌만": [i for i in ids if "openalex" in R[i]["sources"]],
    "Semantic Scholar 수록 문헌만": [i for i in ids if "s2" in R[i]["sources"]],
    "두 자료원 공통 문헌만": [i for i in ids if set(R[i]["sources"]) == {"openalex", "s2"}],
    "2019년 이후": [i for i in ids if R[i]["year"] >= 2019],
    "피인용 상위 절반": sorted(ids, key=lambda i: -(R[i].get("cited") or 0))[:len(ids) // 2],
}
rules = {"기준 규칙": lv_base, "B2=2 요구": lv_mech, "T1 요건 제외": lv_noT1, "Q 요건 제외": lv_noQ, "R≥2 인정": lv_R2, "최소 요건(T1·Q 제외, R≥2)": lv_loose}
codesets = {"재판정 후(기준)": C, "재판정 전": C0, "원문 재판정 반영": {i: ({**C[i], **{k: max(C[i][k], F[i][k]) if isinstance(C[i][k], int) else C[i][k] for k in F[i]}} if i in F else C[i]) for i in C}}
def summ(sub, rule, cs):
    L = [rule(cs[i]) for i in sub]; n = len(L)
    cum = {f"≥{k}": sum(1 for x in L if x >= k) for k in range(1, 5)}
    return {"n": n, "cum": cum, "pct": {k: round(100 * v / n, 1) for k, v in cum.items()}, "ci4": wilson(cum["≥4"], n), "ci3": wilson(cum["≥3"], n),
            "C4_nonhier": sum(1 for i in sub if nonhier_C4(cs[i]))}
out = {"subsets": {k: summ(v, lv_base, C) for k, v in subsets.items()},
       "rules": {k: summ(ids, f, C) for k, f in rules.items()},
       "codesets": {k: summ(ids, lv_base, cs) for k, cs in codesets.items()}}
# 항목 비율의 범위(부분 표본 간)
items = {"B2=2": lambda c: c["B2"] == 2, "T1": lambda c: c["T1"] == 1, "E≥2": lambda c: c["E"] >= 2, "R=3": lambda c: c["R"] == 3, "S2=2": lambda c: c["S2"] == 2, "S1": lambda c: c["S1"] == 1}
out["items_by_subset"] = {s: {k: round(100 * sum(1 for i in sub if f(C[i])) / len(sub), 1) for k, f in items.items()} for s, sub in subsets.items()}
# 표본 크기 기준: 수준 4가 0편일 때 95% 상한(3의 규칙과 윌슨)
out["zero_upper"] = {s: {"rule_of_three": round(300 / len(sub), 1), "wilson_hi": wilson(0, len(sub))[1]} for s, sub in subsets.items()}
# 수준 4를 만드는 데 무엇이 모자라는가: 수준 3 문헌의 R 분포, R=3 문헌의 수준 분포
lv = {i: lv_base(C[i]) for i in ids}
out["L3_R_dist"] = dict(collections.Counter(C[i]["R"] for i in ids if lv[i] == 3))
out["R3_level_dist"] = dict(collections.Counter(lv[i] for i in ids if C[i]["R"] == 3))
out["R3_missing"] = {i: {k: C[i][k] for k in ["B1", "B2", "T1", "E", "Q"]} for i in ids if C[i]["R"] == 3}
json.dump(out, open("audit/sensitivity.json", "w"), ensure_ascii=False, indent=1)
for sec in ["subsets", "rules", "codesets"]:
    print("==", sec)
    for k, v in out[sec].items(): print(f"{k:28s} n={v['n']:3d} ≥1 {v['pct']['≥1']:5.1f} ≥2 {v['pct']['≥2']:5.1f} ≥3 {v['pct']['≥3']:5.1f} ≥4 {v['cum']['≥4']} ({v['pct']['≥4']}) CI4 {v['ci4']} C4nh {v['C4_nonhier']}")
print(json.dumps(out["items_by_subset"], ensure_ascii=False, indent=0))
print(out["zero_upper"]["전체(기준)"], out["L3_R_dist"], out["R3_level_dist"], out["R3_missing"])
