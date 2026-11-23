"""리뷰 담론 분석: 합의 판정(final) 기준 항목 비율, 시기 변화, 방법 유형별 차이, 사례 건물 언급, 1차 연구 근거 수준과의 대조."""
import json, math, re, collections, statistics
from scipy import stats
D = json.load(open("audit/review_codes.json")); F = D["final"]
R = {json.loads(l)["id"]: json.loads(l) for l in open("audit/corpus.jsonl", encoding="utf-8")}
C = json.load(open("audit/manual_codes_all.json")); LV = json.load(open("audit/levels.json"))["levels"]
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]
def per(y): return "2007–2018" if y <= 2018 else ("2019–2022" if y <= 2022 else "2023–2026")
ids = sorted(F); n = len(ids); K = ["M", "SP", "PC", "QS", "CR"]
out = {"n": n, "excluded_no_abstract": len(D["excluded_no_abstract"]), "kappa_initial": D["kappa_initial"]}
out["items"] = {k: {"k": sum(F[i][k] for i in ids), "pct": round(100 * sum(F[i][k] for i in ids) / n, 1), "ci": wilson(sum(F[i][k] for i in ids), n)} for k in K}
P = collections.defaultdict(list)
for i in ids: P[per(R[i]["year"])].append(i)
out["period_n"] = {p: len(v) for p, v in sorted(P.items())}
out["by_period"] = {k: {p: {"k": sum(F[i][k] for i in v), "pct": round(100 * sum(F[i][k] for i in v) / len(v), 1)} for p, v in sorted(P.items())} for k in K}
def ca(k):
    order = ["2007–2018", "2019–2022", "2023–2026"]; ks = [sum(F[i][k] for i in P[p]) for p in order]; ns = [len(P[p]) for p in order]
    t = [1, 2, 3]; N = sum(ns); pb = sum(ks) / N
    T = sum(a * b for a, b in zip(ks, t)) - pb * sum(a * b for a, b in zip(ns, t))
    V = pb * (1 - pb) * (sum(a * b * b for a, b in zip(ns, t)) - sum(a * b for a, b in zip(ns, t)) ** 2 / N)
    z = T / math.sqrt(V) if V > 0 else 0; return {"z": round(z, 2), "p": round(2 * (1 - stats.norm.cdf(abs(z))), 4)}
out["trend"] = {k: ca(k) for k in K}
def fx(f, g):
    t = [[sum(1 for i in ids if f(F[i]) and g(F[i])), sum(1 for i in ids if f(F[i]) and not g(F[i]))],
         [sum(1 for i in ids if not f(F[i]) and g(F[i])), sum(1 for i in ids if not f(F[i]) and not g(F[i]))]]
    r = stats.fisher_exact(t); return {"table": t, "OR": round(r[0], 2) if r[0] not in (0, float("inf")) else r[0], "p": round(r[1], 4)}
out["by_method"] = {m: {k: sum(F[i][k] for i in ids if F[i]["M"] == m) for k in K} | {"n": sum(1 for i in ids if F[i]["M"] == m)} for m in (0, 1)}
out["tests"] = {"CR~M": fx(lambda c: c["M"] == 1, lambda c: c["CR"] == 1), "SP~M": fx(lambda c: c["M"] == 1, lambda c: c["SP"] == 1),
                "PC~M": fx(lambda c: c["M"] == 1, lambda c: c["PC"] == 1), "PC~SP": fx(lambda c: c["SP"] == 1, lambda c: c["PC"] == 1),
                "CR~SP": fx(lambda c: c["SP"] == 1, lambda c: c["CR"] == 1), "CR~PC": fx(lambda c: c["PC"] == 1, lambda c: c["CR"] == 1)}
out["combos"] = {"SP_only_noCR": sum(1 for i in ids if F[i]["SP"] and not F[i]["CR"]), "SP_and_CR": sum(1 for i in ids if F[i]["SP"] and F[i]["CR"]),
                 "PC_and_CR": sum(1 for i in ids if F[i]["PC"] and F[i]["CR"]), "none": sum(1 for i in ids if not any(F[i][k] for k in K))}
cit = lambda f: [R[i].get("cited") or 0 for i in ids if f(F[i])]
out["cited_median"] = {"CR1": statistics.median(cit(lambda c: c["CR"])), "CR0": statistics.median(cit(lambda c: not c["CR"])),
                       "SP1": statistics.median(cit(lambda c: c["SP"])), "SP0": statistics.median(cit(lambda c: not c["SP"]))}
out["cited_MWU_CR"] = round(stats.mannwhitneyu(cit(lambda c: c["CR"]), cit(lambda c: not c["CR"])).pvalue, 4)
# 상투어·사례 건물 언급
pats = {"3.8 billion": r"3\.8 billion", "Eastgate": r"eastgate", "CH2/Council House": r"council house|\bch2\b", "Esplanade": r"esplanade", "Al Bahr": r"al[ -]?bah[a]?r", "termite": r"termite"}
out["mentions"] = {k: sum(1 for i in ids if re.search(p, (R[i]["abstract"] or ""), re.I)) for k, p in pats.items()}
# 1차 연구와 대조: 같은 시기 1차 연구의 수준≥3 비율, R=3 비율
prim = collections.defaultdict(list)
for i in C: prim[per(R[i]["year"])].append(i)
out["primary_by_period"] = {p: {"n": len(v), "lvl3": round(100 * sum(1 for i in v if LV[i] >= 3) / len(v), 1), "R3": round(100 * sum(1 for i in v if C[i]["R"] == 3) / len(v), 1)} for p, v in sorted(prim.items())}
out["review_to_primary_ratio"] = {p: round(len(P[p]) / len(prim[p]), 2) for p in sorted(P)}
json.dump(out, open("audit/review_results.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
