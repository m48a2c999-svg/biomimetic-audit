"""정독 판정(기준)과 사전어 규칙 판정의 일치도: 항목별 일치율, Cohen kappa, 민감도·특이도(이진화)."""
import json, collections
from sklearn.metrics import cohen_kappa_score
ids = json.load(open("audit/manual_sample_ids.json"))
rule = json.load(open("audit/rule_codes.json"))
Lmap = {"f": "form", "m": "material", "p": "process", "e": "ecosystem", "u": "unclear"}
man = {}
for l in open("audit/manual_codes.txt"):
    if l.startswith("#") or not l.strip():
        continue
    x = l.split()
    i = int(x[0])
    man[ids[i]] = dict(B1=int(x[1]), B2=int(x[2]), T1=int(x[3]), L=Lmap[x[4]], E=int(x[5]), Q=int(x[6]), R=int(x[7]), S1=int(x[8]), S2=int(x[9]))
json.dump(man, open("audit/manual_codes.json", "w"), indent=0)
out = {}
for k in ["B1", "B2", "T1", "L", "E", "Q", "R", "S1", "S2"]:
    a = [str(man[i][k]) for i in man]; b = [str(rule[i][k]) for i in man]
    agree = sum(x == y for x, y in zip(a, b)) / len(a)
    kap = cohen_kappa_score(a, b)
    out[k] = {"n": len(a), "agree": round(agree, 3), "kappa": round(kap, 3)}
# 이진 지표: 기준(정독) 대비 규칙의 민감도·특이도
def binarize(k, v):
    return {"B2": v >= 1, "R": v >= 1, "E": v >= 2, "S2": v >= 1}.get(k, v == 1) if k != "R3" else v == 3
bins = {"B1": lambda v: v == 1, "B2_mech": lambda v: v == 2, "T1": lambda v: v == 1, "Q": lambda v: v == 1,
        "R_any": lambda v: v >= 1, "R3": lambda v: v == 3, "S1": lambda v: v == 1, "S2_lca": lambda v: v == 2,
        "E_sim+": lambda v: v >= 2, "E_proto+": lambda v: v >= 3}
src = {"B1": "B1", "B2_mech": "B2", "T1": "T1", "Q": "Q", "R_any": "R", "R3": "R", "S1": "S1", "S2_lca": "S2", "E_sim+": "E", "E_proto+": "E"}
for name, f in bins.items():
    k = src[name]
    tp = sum(1 for i in man if f(man[i][k]) and f(rule[i][k])); fn = sum(1 for i in man if f(man[i][k]) and not f(rule[i][k]))
    tn = sum(1 for i in man if not f(man[i][k]) and not f(rule[i][k])); fp = sum(1 for i in man if not f(man[i][k]) and f(rule[i][k]))
    se = tp / (tp + fn) if tp + fn else None; sp = tn / (tn + fp) if tn + fp else None
    out[name] = dict(tp=tp, fn=fn, tn=tn, fp=fp, sens=None if se is None else round(se, 3), spec=None if sp is None else round(sp, 3),
                     manual_prev=round((tp + fn) / len(man), 3), rule_prev=round((tp + fp) / len(man), 3))
json.dump(out, open("audit/agreement.json", "w"), indent=1)
for k, v in out.items():
    print(k, v)
