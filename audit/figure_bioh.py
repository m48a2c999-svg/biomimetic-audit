"""그림 9-3: 원리에 충실한 솔방울 전이(습도 응답)와 고정·컷오프 제어의 비교."""
import json, glob, numpy as np, sqlite3, statistics, pickle
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in fm.findSystemFonts():
    if "NotoSansCJK-Regular" in f: fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
OUT = "/home/claude/bio/thesis/figs/"
O = json.load(open("audit/bioh_results.json"))
devs = [("블라인드", "F0c", "S3@c", "HB@c", "F0", "S3"), ("수평 루버", "LH_F0c", "LH_C@c", "HL@c", "LH_F0", "LH_C"), ("수직 루버", "VF_F0c", "VF_C@c", "HV@c", "VF_F0", "VF_C")]
C = {"고정": "#8a8a8a", "컷오프 각도 제어": "#1f5f8b", "습도 응답(솔방울 기제)": "#c0622b"}
fig = plt.figure(figsize=(6.5, 5.6)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.55, wspace=0.35)
# (a) 3개 동 블록
ax = fig.add_subplot(gs[0, 0]); x = np.arange(3); w = 0.26
for j, (lab, col) in enumerate(C.items()):
    v = [O["block3"][d[1 + j]]["dEUI_pct"] for d in devs]
    ax.bar(x + (j - 1) * w, v, w, color=col, label=lab)
    for xi, vi in zip(x, v): ax.text(xi + (j - 1) * w, vi + (0.08 if vi >= 0 else -0.08), f"{vi:+.2f}", ha="center", va="bottom" if vi >= 0 else "top", fontsize=6.3)
ax.axhline(0, color="#222", lw=0.6); ax.set_xticks(x); ax.set_xticklabels([d[0] for d in devs]); ax.set_ylabel("연간 EUI 변화(%)"); ax.set_ylim(-2.0, 2.0)
ax.set_title("(a) 상세 3개 동 블록(장치 없음 대비)", fontsize=8.5, loc="left")
# (b) 257동 중앙값
ax = fig.add_subplot(gs[0, 1])
B = O.get("b257", {})
for j, (lab, col) in enumerate(C.items()):
    v = []
    for d in devs:
        r = B.get(d[3])
        if not r: v.append(np.nan); continue
        v.append([r["median_fixed"], r["median_cutoff"], r["median"]][j])
    ax.bar(x + (j - 1) * w, v, w, color=col)
    if j == 2:
        for k, d in enumerate(devs):
            r = B.get(d[3])
            if r: ax.plot([x[k] + w, x[k] + w], [r["q25"], r["q75"]], color="#222", lw=0.8)
    for k, (xi, vi) in enumerate(zip(x, v)):
        if np.isnan(vi): continue
        top = vi
        if j == 2 and B.get(devs[k][3]): top = max(vi, B[devs[k][3]]["q75"]) if vi >= 0 else min(vi, B[devs[k][3]]["q25"])
        ax.text(xi + (j - 1) * w, (top + 0.08) if vi >= 0 else (top - 0.08), f"{vi:+.2f}", ha="center", va="bottom" if vi >= 0 else "top", fontsize=6.3)
ax.axhline(0, color="#222", lw=0.6); ax.set_xticks(x); ax.set_xticklabels([d[0] for d in devs]); ax.set_ylim(-2.0, 5.2)
n = min((r["n"] for r in B.values()), default=0)
ax.set_title(f"(b) 257동 건물별 변화의 중앙값(n={n})", fontsize=8.5, loc="left")
fig.legend(*fig.axes[0].get_legend_handles_labels(), loc="upper center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 1.0))
# (c) 습도 응답의 닫힘 정도와 일사의 관계
ax = fig.add_subplot(gs[1, 0])
f = glob.glob("sim/sb/data/tmyx2011_2025/*.epw")[0]
L = [l.split(",") for l in open(f).read().splitlines()[8:]]
RH = np.array([float(q[8]) for q in L]); GHI = np.array([float(q[13]) for q in L]); hr = np.array([int(q[3]) for q in L])
Ft = np.clip((RH - 40) / 45, 0, 1); F = np.zeros_like(Ft); a = 1 - (5 / 6) ** 6
for i in range(1, len(F)): F[i] = F[i - 1] + a * (Ft[i] - F[i - 1])
occ = (hr >= 9) & (hr <= 18)
bins = [0, 150, 300, 450, 600, 750, 1100]; mid = []; mv = []
for lo, hi in zip(bins[:-1], bins[1:]):
    s = occ & (GHI >= lo) & (GHI < hi); mid.append(f"{lo}–\n{hi}" if hi < 1100 else f"{lo}+"); mv.append(100 * F[s].mean())
ax.bar(range(len(mv)), mv, color="#c0622b", width=0.65)
for k, v in enumerate(mv): ax.text(k, v + 1, f"{v:.0f}", ha="center", fontsize=6.5)
ax.set_xticks(range(len(mv))); ax.set_xticklabels(mid, fontsize=6.5, rotation=0); ax.set_xlabel("수평면 전일사(W/m²), 재실 시간 9–18시"); ax.set_ylabel("평균 닫힘 정도(%)"); ax.set_ylim(0, 80)
r = np.corrcoef(F[occ], GHI[occ])[0, 1]
ax.set_title(f"(c) 습도 응답 제어의 닫힘 정도(r={r:.2f})", fontsize=8.5, loc="left")
# (d) 블록: 최대 전력·주광(UDI) 변화
ax = fig.add_subplot(gs[1, 1])
for j, (lab, col) in enumerate(C.items()):
    pk = [O["block3"][d[1 + j]]["dpeak_pct"] for d in devs]
    ud = [np.mean(list(O["block3"][d[1 + j]]["dUDI_pp"].values())) for d in devs]
    for k, mk in enumerate(["o", "s", "^"]): ax.scatter(ud[k], pk[k], color=col, s=30, marker=mk, zorder=3, edgecolor="white", lw=0.4)
for k, mk in enumerate(["o", "s", "^"]): ax.scatter([], [], color="#555", marker=mk, s=22, label=devs[k][0])
ax.legend(fontsize=6.5, frameon=False, loc="upper right")
ax.axhline(0, color="#222", lw=0.5); ax.axvline(0, color="#222", lw=0.5)
ax.set_xlabel("주광 유효 시간(UDI) 변화, 3개 동 평균(%p)"); ax.set_ylabel("블록 최대 전력 변화(%)")
ax.set_title("(d) 3개 동 블록의 최대 전력과 주광", fontsize=8.5, loc="left")
fig.savefig(OUT + "fig9_3_faithful.png", bbox_inches="tight"); plt.close(fig)
print("ok", round(r, 2), [round(v, 1) for v in mv])
