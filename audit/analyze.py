"""판정 결과 집계: 항목별 비율(윌슨 95% 신뢰구간), 시기별 추세, 주장–근거 위계, 교차표."""
import json, math, collections, re
from scipy import stats

R = {json.loads(l)["id"]: json.loads(l) for l in open("audit/corpus.jsonl", encoding="utf-8")}
C = json.load(open("audit/manual_codes_all.json"))
S = json.load(open("audit/screening.json"))
rule = json.load(open("audit/rule_codes.json"))

def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))

def per(y): return "2007–2018" if y <= 2018 else ("2019–2022" if y <= 2022 else "2023–2026")
ids = sorted(C)
N = len(ids)
out = {"N": N, "screening": dict(collections.Counter(s["decision"] for s in S))}
def share(f, sub=None):
    sub = sub or ids
    k = sum(1 for i in sub if f(C[i])); n = len(sub)
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci": wilson(k, n)}

items = {
    "B1 생물 모델 명시": lambda c: c["B1"] == 1,
    "B2≥1 기능 이상 기술": lambda c: c["B2"] >= 1,
    "B2=2 기제 기술": lambda c: c["B2"] == 2,
    "T1 전이 절차 명시": lambda c: c["T1"] == 1,
    "E≥2 시뮬레이션 이상": lambda c: c["E"] >= 2,
    "E≥3 시제품·실험 이상": lambda c: c["E"] >= 3,
    "E=4 실건물 측정": lambda c: c["E"] == 4,
    "Q 정량 성능": lambda c: c["Q"] == 1,
    "R≥1 비교 기준 있음": lambda c: c["R"] >= 1,
    "R=3 같은 기능 비생체모방 대안": lambda c: c["R"] == 3,
    "S1 지속가능성 주장": lambda c: c["S1"] == 1,
    "S2=2 전과정 근거": lambda c: c["S2"] == 2,
}
out["items"] = {k: share(f) for k, f in items.items()}
out["dist"] = {k: dict(sorted(collections.Counter(str(C[i][k]) for i in ids).items())) for k in ["B2", "L", "E", "R", "S2"]}
# 시기별
periods = collections.defaultdict(list)
for i in ids: periods[per(R[i]["year"])].append(i)
out["period_n"] = {p: len(v) for p, v in sorted(periods.items())}
out["by_period"] = {k: {p: share(f, v) for p, v in sorted(periods.items())} for k, f in items.items()}
# 추세: 연도를 설명변수로 한 로지스틱 회귀 대신 Cochran–Armitage(시기 순서 1,2,3)
def ca_trend(f):
    order = ["2007–2018", "2019–2022", "2023–2026"]
    ks = [sum(1 for i in periods[p] if f(C[i])) for p in order]; ns = [len(periods[p]) for p in order]
    t = [1, 2, 3]; Nn = sum(ns); K = sum(ks); pbar = K / Nn
    T = sum(ki * ti for ki, ti in zip(ks, t)) - pbar * sum(ni * ti for ni, ti in zip(ns, t))
    V = pbar * (1 - pbar) * (sum(ni * ti * ti for ni, ti in zip(ns, t)) - sum(ni * ti for ni, ti in zip(ns, t)) ** 2 / Nn)
    z = T / math.sqrt(V) if V > 0 else 0
    return {"z": round(z, 2), "p": round(2 * (1 - stats.norm.cdf(abs(z))), 4)}
out["trend"] = {k: ca_trend(f) for k, f in items.items()}
# 주장–근거 위계(누적)
lvl = {}
for i in ids:
    c = C[i]
    L0 = True
    L1 = c["B1"] == 1 and c["B2"] >= 1                 # C1 생물 출처 근거
    L2 = L1 and c["T1"] == 1                            # C2 절차
    L3 = L2 and c["E"] >= 2 and c["Q"] == 1             # C3 성능(정량)
    L4 = L3 and c["R"] == 3                             # C4 공정 비교
    lvl[i] = 4 if L4 else 3 if L3 else 2 if L2 else 1 if L1 else 0
out["ladder"] = {str(k): v for k, v in sorted(collections.Counter(lvl.values()).items())}
out["ladder_cum"] = {f"≥{k}": share(lambda c, k=k: True, [i for i in ids if lvl[i] >= k]) for k in range(1, 5)}
for k in range(1, 5):
    out["ladder_cum"][f"≥{k}"] = {"k": sum(1 for i in ids if lvl[i] >= k), "n": N, "pct": round(100 * sum(1 for i in ids if lvl[i] >= k) / N, 1), "ci": wilson(sum(1 for i in ids if lvl[i] >= k), N)}
# 비위계 기준: 독립적으로 C3·C4 충족
out["perf_claim"] = {
    "Q=1 중 R=3": share(lambda c: c["R"] == 3, [i for i in ids if C[i]["Q"] == 1]),
    "Q=1 중 R=0": share(lambda c: c["R"] == 0, [i for i in ids if C[i]["Q"] == 1]),
    "E≥2 중 R=3": share(lambda c: c["R"] == 3, [i for i in ids if C[i]["E"] >= 2]),
    "S1=1 중 S2=2": share(lambda c: c["S2"] == 2, [i for i in ids if C[i]["S1"] == 1]),
    "S1=1 중 S2=0": share(lambda c: c["S2"] == 0, [i for i in ids if C[i]["S1"] == 1]),
    "B1=1 중 B2=2": share(lambda c: c["B2"] == 2, [i for i in ids if C[i]["B1"] == 1]),
}
# 교차: 모방 수준 × 근거
out["L_x_E"] = {L: dict(sorted(collections.Counter(C[i]["E"] for i in ids if C[i]["L"] == L).items())) for L in ["form", "material", "process", "ecosystem", "unclear"]}
out["L_x_B2"] = {L: dict(sorted(collections.Counter(C[i]["B2"] for i in ids if C[i]["L"] == L).items())) for L in ["form", "material", "process", "ecosystem", "unclear"]}
out["L_x_T1"] = {L: share(lambda c: c["T1"] == 1, [i for i in ids if C[i]["L"] == L]) for L in ["form", "material", "process", "ecosystem", "unclear"]}
out["L_x_R"] = {L: dict(sorted(collections.Counter(C[i]["R"] for i in ids if C[i]["L"] == L).items())) for L in ["form", "material", "process", "ecosystem", "unclear"]}
# 생물학 소속 저자(OpenAlex 소속 원문 기준, 자동)
BIO = re.compile(r"biolog|botan|zoolog|plant (science|biology|biomechanics)|life sciences?|ecolog|evolution|biosciences?|botanic garden|natural history|entomolog|marine science|forest", re.I)
haveaff = [i for i in ids if R[i].get("affiliations")]
out["P_bio_affil"] = share(lambda c: True, [i for i in haveaff if BIO.search(" ".join(R[i]["affiliations"]))])
out["P_bio_affil"]["n_with_affil"] = len(haveaff); out["P_bio_affil"]["pct_of_affil"] = round(100 * out["P_bio_affil"]["k"] / len(haveaff), 1)
pb = [i for i in haveaff if BIO.search(" ".join(R[i]["affiliations"]))]
out["P_vs_B2mech"] = {"bio_affil": share(lambda c: c["B2"] == 2, pb), "no_bio_affil": share(lambda c: c["B2"] == 2, [i for i in haveaff if i not in pb])}
f_ = stats.fisher_exact([[sum(C[i]["B2"] == 2 for i in pb), sum(C[i]["B2"] != 2 for i in pb)],
                         [sum(C[i]["B2"] == 2 for i in haveaff if i not in pb), sum(C[i]["B2"] != 2 for i in haveaff if i not in pb)]])
out["P_vs_B2mech"]["fisher_p"] = round(f_[1], 4); out["P_vs_B2mech"]["OR"] = round(f_[0], 2) if f_[0] != float("inf") else None
# 피인용과 근거 수준
cit = [(R[i].get("cited") or 0, lvl[i], R[i]["year"]) for i in ids]
rho = stats.spearmanr([c for c, l, y in cit], [l for c, l, y in cit])
out["cited_vs_ladder"] = {"spearman_rho": round(rho.correlation, 3), "p": round(rho.pvalue, 4)}
# 유형
out["types"] = dict(collections.Counter(R[i]["type"] or "?" for i in ids))
# 초록 없는 적격 문헌의 연도 분포(편향 점검)
Nids = [s["id"] for s in S if s["decision"] == "N"]
out["no_abstract_period"] = dict(collections.Counter(per(R[i]["year"]) for i in Nids))
out["coded_period"] = out["period_n"]
chi = stats.chi2_contingency([[out["no_abstract_period"].get(p, 0) for p in ["2007–2018", "2019–2022", "2023–2026"]],
                              [out["period_n"].get(p, 0) for p in ["2007–2018", "2019–2022", "2023–2026"]]])
out["no_abstract_vs_coded_chi2_p"] = round(chi[1], 5)
# 규칙 판정의 전수 비율(참고)
out["rule_prev_all"] = {k: round(100 * sum(1 for i in ids if (rule[i][k] == 3 if k == "R3" else False)) / N, 1) for k in []}
json.dump({"levels": lvl}, open("audit/levels.json", "w"))
json.dump(out, open("audit/results.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:9000])
