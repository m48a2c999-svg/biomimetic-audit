"""학술논문용 영문 그림 (300 dpi)."""
import json, sqlite3, statistics as st
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
OUT = "/home/claude/bio/paper/figs/"
INK, MUTE, ACC, ACC2 = "#222222", "#8a8a8a", "#1f5f8b", "#c0622b"
res = json.load(open("audit/results.json")); ft = json.load(open("audit/fulltext_compare.json"))["all"]

def box(ax, x, y, w, h, t, fc="#f4f6f8", ec="#5a6b7a", fs=8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02", fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, color=INK, fontweight="bold" if bold else "normal")
def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="#5a6b7a", lw=0.8))

# Fig 1 framework
fig, ax = plt.subplots(figsize=(6.3, 3.9)); ax.set_xlim(0, 1); ax.set_ylim(-0.04, 1.07); ax.axis("off")
axes_ = ["Epistemology\n(design vs. science)", "Performance\nevidence", "Sustainability\npromise", "Aesthetics\nand ethics"]
claims = ["C1 Derived from a\nspecific organism", "C2 Transferred a\nbiological principle", "C3 Performs well", "C4 Performs well because\nit is biomimetic", "C5 Is sustainable"]
items_ = ["B1, B2, P", "T1, B2", "E, Q", "R (= 3)", "S1, S2"]
for k, a in enumerate(axes_): box(ax, 0.02, 0.80 - k * 0.22, 0.22, 0.16, a, fc="#e6eef5", bold=True, fs=6.8)
for k, (c, it) in enumerate(zip(claims, items_)):
    y = 0.84 - k * 0.19
    box(ax, 0.38, y, 0.32, 0.13, c, fs=7.5); box(ax, 0.78, y, 0.19, 0.13, it, fc="#fbeee6", ec=ACC2, fs=8)
    arrow(ax, 0.70, y + 0.065, 0.78, y + 0.065)
for a, c in [(0, 0), (0, 1), (1, 2), (1, 3), (2, 4)]: arrow(ax, 0.24, 0.88 - a * 0.22, 0.38, 0.905 - c * 0.19)
ax.text(0.13, 0.11, "Used as an interpretive lens,\nnot audited", ha="center", va="top", fontsize=7, color=MUTE)
for x, t in [(0.13, "Critique axis"), (0.54, "Claim targeted"), (0.875, "Audit items")]: ax.text(x, 1.01, t, ha="center", fontsize=8, color=MUTE)
fig.savefig(OUT + "fig1_framework.png", bbox_inches="tight"); plt.close(fig)

# Fig 2 items
order = ["B1 생물 모델 명시", "B2≥1 기능 이상 기술", "B2=2 기제 기술", "T1 전이 절차 명시", "E≥2 시뮬레이션 이상", "E≥3 시제품·실험 이상", "E=4 실건물 측정", "Q 정량 성능", "R≥1 비교 기준 있음", "R=3 같은 기능 비생체모방 대안", "S1 지속가능성 주장", "S2=2 전과정 근거"]
lab = ["Organism named (B1)", "Function described (B2≥1)", "Mechanism described (B2=2)", "Transfer procedure (T1)", "Simulation or higher (E≥2)", "Prototype/experiment (E≥3)", "Real-building measurement (E=4)", "Quantitative performance (Q)", "Any comparison baseline (R≥1)", "Same-function alternative (R=3)", "Sustainability claimed (S1)", "Life-cycle evidence (S2=2)"]
p = [res["items"][k]["pct"] for k in order]; lo = [res["items"][k]["ci"][0] for k in order]; hi = [res["items"][k]["ci"][1] for k in order]
fig, ax = plt.subplots(figsize=(6.3, 3.6))
ax.barh(lab, p, color=[ACC2 if k in (order[2], order[9], order[11]) else ACC for k in order], height=0.6)
ax.errorbar(p, range(len(p)), xerr=[[a - b for a, b in zip(p, lo)], [b - a for a, b in zip(p, hi)]], fmt="none", ecolor=INK, lw=0.7, capsize=2)
for k, v in enumerate(p): ax.text(hi[k] + 1.2, k, f"{v:.1f}%", va="center", fontsize=7.5)
ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("Share of 193 studies (%); whiskers show 95% Wilson CI")
fig.savefig(OUT + "fig2_items.png", bbox_inches="tight"); plt.close(fig)

# Fig 3 ladder
steps = ["All", "Level ≥1\nbiological source", "Level ≥2\n+ transfer", "Level ≥3\n+ quantitative", "Level 4\n+ same-function\ncomparison"]
vals = [res["N"]] + [res["ladder_cum"][f"≥{k}"]["k"] for k in range(1, 5)]
fig, ax = plt.subplots(figsize=(6.3, 2.7))
ax.bar(range(5), vals, color=[MUTE, ACC, ACC, ACC, ACC2], width=0.62)
for k, v in enumerate(vals): ax.text(k, v + 3, f"{v}\n({100*v/res['N']:.1f}%)" if k else f"{v}", ha="center", fontsize=7.5)
ax.set_xticks(range(5)); ax.set_xticklabels(steps, fontsize=7.5); ax.set_ylabel("Number of studies"); ax.set_ylim(0, 230)
fig.savefig(OUT + "fig3_ladder.png", bbox_inches="tight"); plt.close(fig)

# Fig 4 case
db = sqlite3.connect("/home/claude/badtm/data/db/research.sqlite")
r3 = {t: e for t, e, p in db.execute("select tag,dEUI_pct,dpeak_pct from results_3bldg")}
med = {t: st.median([r[0] for r in db.execute("select dEUI_pct from results_257 where tag=?", (t,))]) for t in ["F0", "S3", "LH_F0", "LH_C", "VF_F0", "VF_C"]}
fig, axs = plt.subplots(1, 2, figsize=(6.3, 2.7))
devs = ["Blind", "Horizontal\nlouver", "Vertical\nlouver"]; fx = ["F0", "LH_F0", "VF_F0"]; cu = ["S3", "LH_C", "VF_C"]; x = np.arange(3)
axs[0].bar(x - 0.2, [r3[t] for t in fx], 0.38, color="#9fbad0", label="Fixed")
axs[0].bar(x + 0.2, [r3[t] for t in cu], 0.38, color=ACC2, label='Cut-off angle control (earlier manuscript: "pine cone–sunflower principle")')
for a, t, d in ((axs[0], "(a) Three-building block", None), (axs[1], "(b) 257 buildings, median", None)):
    a.axhline(0, color=INK, lw=0.6); a.set_xticks(x); a.set_xticklabels(devs); a.set_title(t, fontsize=8.5)
axs[0].set_ylabel("Change in annual EUI (%)")
axs[1].bar(x - 0.2, [med[t] for t in fx], 0.38, color="#9fbad0"); axs[1].bar(x + 0.2, [med[t] for t in cu], 0.38, color=ACC2)
fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, fontsize=7, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.06))
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(OUT + "fig4_case.png", bbox_inches="tight"); plt.close(fig)
print("ok")
