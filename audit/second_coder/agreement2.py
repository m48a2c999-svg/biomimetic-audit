"""두 번째 판정자 결과(coder2_filled.xlsx)와 첫 번째 판정(manual_codes_all.json)의 항목별 일치도."""
import json, sys
from openpyxl import load_workbook
f = sys.argv[1] if len(sys.argv) > 1 else "audit/second_coder/coder2_filled.xlsx"
C = json.load(open("audit/manual_codes_all.json"))
ws = load_workbook(f)["판정"]; hdr = [c.value for c in ws[1]]
K = ["B1", "B2", "T1", "L", "E", "Q", "R", "S1", "S2"]
D = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    r = dict(zip(hdr, row))
    if all(r.get(k) not in (None, "") for k in K):
        D[r["id"]] = {k: (str(r[k]) if k == "L" else int(r[k])) for k in K}
def kappa(a, b):
    n = len(a); cats = sorted(set(a) | set(b), key=str)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return round(po, 3), (round((po - pe) / (1 - pe), 3) if pe < 1 else None)
out = {"n": len(D)}
for k in K:
    a = [str(C[i][k]) for i in D]; b = [str(D[i][k]) for i in D]
    po, kp = kappa(a, b); out[k] = {"agree": po, "kappa": kp, "disagree": [i for i in D if str(C[i][k]) != str(D[i][k])]}
json.dump(out, open("audit/second_coder/agreement2.json", "w"), ensure_ascii=False, indent=1)
for k in K: print(k, out[k]["agree"], out[k]["kappa"], len(out[k]["disagree"]))
