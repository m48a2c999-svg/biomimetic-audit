"""원리에 충실한 솔방울 전이(습도 응답 수동 제어) 계산 결과 집계.
입력: sim/sb/mb/res_sb10/*.pkl(로컬 계산), /tmp/bioh/bioh_*.json·*_hourly.npz(Actions 계산), research.sqlite(이전 원고 저장 결과)
출력: audit/bioh_results.json"""
import json, glob, pickle, os, sqlite3, statistics, numpy as np
DB = "/home/claude/badtm/data/db/research.sqlite"
con = sqlite3.connect(DB)
runs = {}; hourly = {}
for f in glob.glob("sim/sb/mb/res_sb10/*.pkl"):
    R = pickle.load(open(f, "rb")); k = (R["name"], R["tag"])
    if R.get("EUI") is None: continue
    runs[k] = {x: R.get(x) for x in ("EUI", "area", "peak_kW", "UDI", "PMV_ok", "Cooling:Electricity", "Heating:NaturalGas", "InteriorLights:Electricity")}
    hourly[k] = np.asarray(R["hourly_kW"], dtype=float)
for f in glob.glob("/tmp/bioh/bioh_*.json") + glob.glob("sim/sb/results_bioh/bioh_*.json"):
    D = json.load(open(f))
    for key, d in D.items():
        if d.get("EUI") is None: continue
        n, t = key.split("_", 1)
        runs.setdefault((n, t), d)
    z = f.replace(".json", "_hourly.npz")
    if os.path.exists(z):
        Z = np.load(z, allow_pickle=True)
        for key, v in zip(Z["keys"], Z["kw"]):
            n, t = str(key).split("_", 1); hourly.setdefault((n, t), np.asarray(v, dtype=float))
out = {}
# ---- 상세 3개 동 블록
B3 = ["ARK", "GFC", "GST"]
tags3 = ["S1c", "F0c", "S3@c", "LH_F0c", "LH_C@c", "VF_F0c", "VF_C@c", "HB@c", "HL@c", "HV@c", "HBN@c", "HB2@c"]
def blk(tag):
    if not all((b, tag) in runs for b in B3): return None
    A = sum(runs[(b, tag)]["area"] for b in B3); E = sum(runs[(b, tag)]["EUI"] * runs[(b, tag)]["area"] for b in B3) / A
    pk = max(sum(hourly[(b, tag)] for b in B3)) if all((b, tag) in hourly for b in B3) else None
    comp = {c: sum(runs[(b, tag)][c] * runs[(b, tag)]["area"] for b in B3) / A for c in ("Cooling:Electricity", "Heating:NaturalGas", "InteriorLights:Electricity")}
    return {"EUI": E, "peak": pk, "UDI": {b: runs[(b, tag)]["UDI"] for b in B3}, "PMV": {b: runs[(b, tag)]["PMV_ok"] for b in B3}, **comp}
base = blk("S1c"); out["block3"] = {}
if base:
    for t in tags3:
        r = blk(t)
        if not r: continue
        out["block3"][t] = {"EUI": round(r["EUI"], 2), "dEUI_pct": round(100 * (r["EUI"] / base["EUI"] - 1), 2),
                            "dpeak_pct": round(100 * (r["peak"] / base["peak"] - 1), 2) if r["peak"] and base["peak"] else None,
                            "dUDI_pp": {b: round(r["UDI"][b] - base["UDI"][b], 2) for b in B3}, "dPMV_pp": {b: round(r["PMV"][b] - base["PMV"][b], 2) for b in B3},
                            "dCool": round(r["Cooling:Electricity"] - base["Cooling:Electricity"], 2), "dHeat": round(r["Heating:NaturalGas"] - base["Heating:NaturalGas"], 2), "dLight": round(r["InteriorLights:Electricity"] - base["InteriorLights:Electricity"], 2)}
    st = {r[0]: r for r in con.execute("select tag,dEUI_pct,dpeak_pct from results_3bldg")}
    out["block3_reproduction"] = {t: {"new": out["block3"].get(t + ("c" if t in ("F0", "LH_F0", "VF_F0") else "@c"), {}).get("dEUI_pct"), "stored": round(st[t][1], 2)} for t in ("F0", "S3", "LH_F0", "LH_C", "VF_F0", "VF_C") if t in st}
    out["block3_base_EUI"] = round(base["EUI"], 2)
# ---- 257동(3개 동 포함)
stored = {}
for n, t, e in con.execute("select sim_name, tag, EUI from results_257"):
    stored[(n, t)] = e
names = sorted({n for (n, t) in stored})
out["n257_total"] = len(names)
s1rep = [100 * (runs[(n, "S1c")]["EUI"] / stored[(n, "S1")] - 1) for n in names if (n, "S1c") in runs and (n, "S1") in stored]
out["S1c_vs_stored_S1"] = {"n": len(s1rep), "max_abs_pct": round(max(map(abs, s1rep)), 4) if s1rep else None}
def d(n, t):
    if (n, t) in runs and (n, "S1c") in runs: return 100 * (runs[(n, t)]["EUI"] / runs[(n, "S1c")]["EUI"] - 1)
    return None
def ds(n, t):  # 저장 결과(이전 원고)
    if (n, t) in stored and (n, "S1") in stored: return 100 * (stored[(n, t)] / stored[(n, "S1")] - 1)
    return None
pairs = {"HB@c": ("F0", "S3"), "HL@c": ("LH_F0", "LH_C"), "HV@c": ("VF_F0", "VF_C")}
out["b257"] = {}
for t, (fx, co) in pairs.items():
    ok = [n for n in names if d(n, t) is not None]
    if not ok: continue
    v = [d(n, t) for n in ok]; vf = [ds(n, fx) for n in ok]; vc = [ds(n, co) for n in ok]
    q = np.percentile(v, [25, 50, 75])
    out["b257"][t] = {"n": len(ok), "median": round(float(q[1]), 2), "q25": round(float(q[0]), 2), "q75": round(float(q[2]), 2),
                      "median_fixed": round(statistics.median(vf), 2), "median_cutoff": round(statistics.median(vc), 2),
                      "share_better_than_fixed": round(100 * sum(a < b for a, b in zip(v, vf)) / len(ok), 1),
                      "share_better_than_cutoff": round(100 * sum(a < b for a, b in zip(v, vc)) / len(ok), 1),
                      "median_diff_vs_fixed": round(statistics.median([a - b for a, b in zip(v, vf)]), 2),
                      "median_diff_vs_cutoff": round(statistics.median([a - b for a, b in zip(v, vc)]), 2)}
# 257동 블록 최대 전력(전 건물 시간별 합)
blk257 = {r[0]: r for r in con.execute("select scenario,label,tag,peak_kW,dpeak_pct,CF,LF,peak_hour,dEUI_pct from block_257")}
for t in ("S1c", "HB@c", "HL@c", "HV@c"):
    if all((n, t) in hourly for n in names):
        out.setdefault("block257", {})[t] = round(float(max(sum(hourly[(n, t)] for n in names))), 1)
if "block257" in out and "S1c" in out["block257"]:
    b0 = out["block257"]["S1c"]; out["block257_stored_S1"] = blk257["S1"][3]
    out["block257_dpeak"] = {t: round(100 * (v / b0 - 1), 2) for t, v in out["block257"].items()}
    out["block257_dpeak_stored"] = {k: round(blk257[k][4], 2) for k in ("F0", "S3", "LH_F0", "LH_C", "VF_F0", "VF_C") if k in blk257}
json.dump(out, open("audit/bioh_results.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
