"""추가 분석 그림: 민감도(6-5), 리뷰 담론(7-1), 실제 건물 사례(8-1)."""
import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
for f in fm.findSystemFonts():
    if "NotoSansCJK-Regular" in f: fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
OUT = "/home/claude/bio/thesis/figs/"
INK, MUTE, ACC, ACC2 = "#222222", "#8a8a8a", "#1f5f8b", "#c0622b"
import math
def wil(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)
# ---- 그림 6-5 민감도
S = json.load(open("audit/sensitivity.json"))
rows = [("표본 범위", k, v) for k, v in S["subsets"].items()] + [("판정 규칙", k, v) for k, v in S["rules"].items() if k != "기준 규칙"] + [("판정 자료", k, v) for k, v in S["codesets"].items() if k != "재판정 후(기준)"]
fig, axs = plt.subplots(1, 2, figsize=(6.4, 5.6), sharey=True)
ys=[];cur=0;prevg=None;heads=[]
for g,name,v in rows:
    if g!=prevg:
        heads.append((g,cur)); cur+=1; prevg=g
    ys.append(cur); cur+=1
tot=cur; y=[tot-1-v for v in ys]; heads=[(g,tot-1-v) for g,v in heads]
for ax, key, title, col in [(axs[0], "≥3", "(a) 근거 수준 3 이상", ACC), (axs[1], "≥4", "(b) 근거 수준 4", ACC2)]:
    for yi, (g, name, v) in zip(y, rows):
        k = v["cum"][key]; n = v["n"]; lo, hi = wil(k, n); p = 100 * k / n
        ax.plot([lo, hi], [yi, yi], color=col, lw=1.2); ax.plot(p, yi, "o", color=col, ms=4)
        ax.text(hi + 0.6, yi, f"{k}/{n}", va="center", fontsize=7, color=MUTE)
    base = S["subsets"]["전체(기준)"]; bp = 100 * base["cum"][key] / base["n"]
    ax.axvline(bp, color=MUTE, lw=0.6, ls="--"); ax.set_title(title, fontsize=9, loc="left"); ax.set_xlabel("비율(%)와 95% 신뢰구간")
    ax.set_xlim(0, 50 if key == "≥3" else 12)
axs[0].set_yticks(y); axs[0].set_yticklabels([f"{name}" for g, name, v in rows], fontsize=7.5)
for g, yh in heads:
    axs[0].text(-0.02, yh, g, transform=axs[0].get_yaxis_transform(), fontsize=8, fontweight="bold", color=INK, ha="right", va="center")
for ax in axs: ax.set_ylim(-0.7, tot - 0.3)
fig.tight_layout(); fig.savefig(OUT + "fig6_5_sensitivity.png", bbox_inches="tight"); plt.close(fig)
# ---- 그림 7-1 리뷰 담론
RV = json.load(open("audit/review_results.json"))
lab = {"M": "체계적 방법", "SP": "지속가능성 약속", "PC": "무조건 성능 주장", "QS": "정량 종합", "CR": "근거 공백 지적"}
fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.9), gridspec_kw={"width_ratios": [1.1, 1]})
ks = ["SP", "CR", "M", "PC", "QS"]; ax = axs[0]
for j, k in enumerate(ks[::-1]):
    it = RV["items"][k]; ax.barh(j, it["pct"], color=ACC if k != "CR" else ACC2, height=0.6)
    ax.plot(it["ci"], [j, j], color=INK, lw=0.8); ax.text(it["ci"][1] + 1, j, f"{it['k']}/{RV['n']}", va="center", fontsize=7, color=MUTE)
ax.set_yticks(range(len(ks))); ax.set_yticklabels([lab[k] for k in ks[::-1]]); ax.set_xlim(0, 85); ax.set_xlabel("리뷰 비율(%)"); ax.set_title("(a) 항목별 비율(n=71)", fontsize=9, loc="left")
ax = axs[1]; per = ["2007–2018", "2019–2022", "2023–2026"]
for k, c, m in [("SP", ACC, "o"), ("CR", ACC2, "s"), ("M", INK, "^")]:
    ax.plot(range(3), [RV["by_period"][k][p]["pct"] for p in per], marker=m, color=c, label=lab[k], lw=1.1, ms=4)
ax.set_xticks(range(3)); ax.set_xticklabels([f"{p}\n(n={RV['period_n'][p]})" for p in per], fontsize=7.5); ax.set_ylim(0, 100); ax.set_ylabel("%")
ax.legend(fontsize=7, frameon=False, loc="upper left", ncol=2); ax.set_title("(b) 시기별 변화", fontsize=9, loc="left")
fig.tight_layout(); fig.savefig(OUT + "fig7_1_reviews.png", bbox_inches="tight"); plt.close(fig)
# ---- 그림 8-1 실제 건물: 생물 근거 깊이 대 환경 성능 근거
B = json.load(open("audit/buildings.json"))["cases"]
fig, ax = plt.subplots(figsize=(6.2, 3.6))
bio = lambda c: c["B1"] + c["B2"] + c["T1"]   # 0~4
perf = lambda c: (c["E"] >= 4) * 2 + c["Q"]     # 0~3: 측정 운영자료 2 + 정량 1
off = {"eastgate": (0.08, 0.12), "ch2": (0.08, -0.22), "smaxe": (-0.1, 0.18), "albahr": (0.08, 0.1), "esplanade": (0.08, 0.08),
       "oneocean": (-0.1, 0.18), "hygroskin": (0.08, -0.22), "flectofold": (0.08, 0.1), "bloom": (0.08, 0.1)}
short = {"eastgate": "Eastgate", "ch2": "CH2", "smaxe": "30 St Mary Axe", "albahr": "Al Bahr", "esplanade": "Esplanade", "oneocean": "One Ocean(여수)", "hygroskin": "HygroSkin", "flectofold": "Flectofold", "bloom": "Bloom"}
import collections
jitd = {"ch2": 0.0, "smaxe": 0.16, "esplanade": 0.0, "bloom": 0.16, "oneocean": 0.0, "hygroskin": 0.16, "flectofold": 0.32}
off = {"eastgate": (0.1, 0.0), "ch2": (-0.1, 0.0), "smaxe": (0.0, 0.28), "albahr": (0.1, 0.0), "esplanade": (-0.1, 0.0), "bloom": (0.1, 0.0),
       "oneocean": (-0.1, 0.0), "hygroskin": (0.0, -0.3), "flectofold": (0.0, 0.28)}
for c in B:
    x, yv = bio(c), perf(c); jit = jitd.get(c["id"], 0.0)
    col = ACC2 if c["claim_src"] == "secondary" else ACC
    ax.scatter(x + jit, yv, s=40, color=col, zorder=3, edgecolor="white", lw=0.5)
    dx, dy = off[c["id"]]; ax.text(x + jit + dx, yv + dy, short[c["id"]], fontsize=7.5, va="center", ha="left" if dx > 0 else ("right" if dx < 0 else "center"))
ax.set_xlim(-1.0, 4.9); ax.set_ylim(-0.5, 3.6)
ax.set_xticks(range(5)); ax.set_xticklabels(["0\n생물 출처 없음", "1", "2", "3", "4\n생물 명시·기제·전이 절차"], fontsize=7.5)
ax.set_yticks(range(4)); ax.set_yticklabels(["0 없음", "1 정량 주장만", "2 실측 자료", "3 실측 자료+정량"], fontsize=7.5)
ax.set_xlabel("생물학 근거의 깊이(B1+B2+T1)"); ax.set_ylabel("환경 성능 근거")
ax.scatter([], [], color=ACC, s=30, label="설계자 자료의 주장"); ax.scatter([], [], color=ACC2, s=30, label="2차 문헌에서 붙은 주장")
ax.legend(fontsize=7, frameon=False, loc="upper right"); ax.grid(alpha=0.25, lw=0.5)
fig.tight_layout(); fig.savefig(OUT + "fig8_1_buildings.png", bbox_inches="tight"); plt.close(fig)
print("ok")
