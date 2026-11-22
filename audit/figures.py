import json, collections, sqlite3
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
for f in fm.findSystemFonts():
    if "NotoSansCJK-Regular" in f: fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
OUT = "/home/claude/bio/thesis/figs/"
INK, MUTE, ACC, ACC2 = "#222222", "#8a8a8a", "#1f5f8b", "#c0622b"
R = {json.loads(l)["id"]: json.loads(l) for l in open("audit/corpus.jsonl")}
S = json.load(open("audit/screening.json")); C = json.load(open("audit/manual_codes_all.json"))
res = json.load(open("audit/results.json")); ft = json.load(open("audit/fulltext_compare.json"))
lv = json.load(open("audit/levels.json"))["levels"]

def box(ax, x, y, w, h, t, fc="#f4f6f8", ec="#5a6b7a", fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02", fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, color=INK, fontweight="bold" if bold else "normal", wrap=True)
def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="#5a6b7a", lw=0.8))

# 그림 1-1 연구 흐름
fig, ax = plt.subplots(figsize=(6.3, 3.4)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
cols = [("비판 문헌 고찰\n(제3장)", "인식론·성능·지속가능성\n·미학·윤리 4축\n→ 주장 C1~C5\n→ 판정 항목 10개"),
        ("체계적 문헌 판정\n(제4~6장)", "OpenAlex·Semantic Scholar\n수집 530건 → 선별\n→ 1차 연구 193편 정독 판정\n→ 원문 표본 재판정"),
        ("사례 분석\n(제7장)", "이전 연구의 생물 원리\n네 가지를 입력·상태·출력\n으로 재정의 → 일반 제어와\n대응·결과 재해석")]
for k, (h, b) in enumerate(cols):
    x = 0.03 + k * 0.33
    box(ax, x, 0.66, 0.28, 0.22, h, fc="#e6eef5", bold=True)
    box(ax, x, 0.24, 0.28, 0.36, b, fs=7.8)
    if k < 2: arrow(ax, x + 0.285, 0.77, x + 0.325, 0.77)
box(ax, 0.18, 0.02, 0.64, 0.15, "논의·결론(제8~9장): 주장 종류별 근거 조건과 보고 점검표", fc="#fbeee6", ec=ACC2, bold=True)
for k in range(3): arrow(ax, 0.17 + k * 0.33, 0.24, 0.5, 0.17)
fig.savefig(OUT + "fig1_1_flow.png", bbox_inches="tight"); plt.close(fig)

# 그림 3-1 비판 축 → 주장 → 판정 항목
fig, ax = plt.subplots(figsize=(6.3, 3.9)); ax.set_xlim(0, 1); ax.set_ylim(-0.04, 1.07); ax.axis("off")
axes_ = ["인식론\n(설계 대 과학)", "성능 근거", "지속가능성 약속", "미학·윤리"]
claims = ["C1 특정 생물에서 왔다", "C2 생물 원리를 옮겼다", "C3 성능이 좋다", "C4 생체모방이라서 좋다", "C5 지속가능하다"]
items_ = ["B1·B2·P", "T1·B2", "E·Q", "R(=3)", "S1·S2"]
for k, a in enumerate(axes_):
    box(ax, 0.02, 0.80 - k * 0.22, 0.22, 0.16, a, fc="#e6eef5", bold=True)
for k, (c, it) in enumerate(zip(claims, items_)):
    y = 0.84 - k * 0.19
    box(ax, 0.38, y, 0.32, 0.13, c, fs=8)
    box(ax, 0.78, y, 0.19, 0.13, it, fc="#fbeee6", ec=ACC2, fs=8)
    arrow(ax, 0.70, y + 0.065, 0.78, y + 0.065)
links = [(0, 0), (0, 1), (1, 2), (1, 3), (2, 4)]
for a, c in links:
    arrow(ax, 0.24, 0.88 - a * 0.22, 0.38, 0.905 - c * 0.19)
ax.text(0.13, 0.11, "미학·윤리 축은 판정하지 않고\n해석의 틀로 사용(제8장)", ha="center", va="top", fontsize=7.5, color=MUTE)
ax.text(0.13, 1.01, "비판의 축", ha="center", fontsize=8, color=MUTE); ax.text(0.54, 1.01, "비판이 겨누는 주장", ha="center", fontsize=8, color=MUTE); ax.text(0.875, 1.01, "판정 항목", ha="center", fontsize=8, color=MUTE)
fig.savefig(OUT + "fig3_1_framework.png", bbox_inches="tight"); plt.close(fig)

# 그림 4-1 PRISMA 흐름
sc = collections.Counter(s["decision"] for s in S)
oa_n = sum(1 for l in open("audit/raw/openalex.jsonl")); s2_n = sum(1 for l in open("audit/raw/s2_search.jsonl"))
fig, ax = plt.subplots(figsize=(6.0, 4.5)); ax.set_xlim(0, 1); ax.set_ylim(-0.1, 1.0); ax.axis("off")
box(ax, 0.03, 0.84, 0.42, 0.12, f"OpenAlex 검색\n{oa_n}건")
box(ax, 0.55, 0.84, 0.42, 0.12, f"Semantic Scholar 검색\n{s2_n}건")
box(ax, 0.25, 0.64, 0.50, 0.11, f"중복 제거 후 후보\n{len(S)}건")
arrow(ax, 0.24, 0.84, 0.40, 0.75); arrow(ax, 0.76, 0.84, 0.60, 0.75)
box(ax, 0.25, 0.44, 0.50, 0.11, f"제목·초록 선별")
arrow(ax, 0.5, 0.64, 0.5, 0.55)
box(ax, 0.79, 0.40, 0.20, 0.20, f"제외\n대상 아님 {sc['E1']}\n비영어 {sc['E2']}\n중복 {sc['X']}", fc="#f7f7f7", fs=7.5)
arrow(ax, 0.75, 0.495, 0.79, 0.495)
box(ax, 0.02, 0.12, 0.30, 0.18, f"초록 없음(적격)\n{sc['N']}편\n— 판정 불가, 시기 비교", fc="#f7f7f7", fs=7.5)
box(ax, 0.35, 0.12, 0.30, 0.18, f"1차 연구\n{sc['I']}편\n— 전수 정독 판정", fc="#e6eef5", bold=True)
box(ax, 0.68, 0.12, 0.30, 0.18, f"리뷰·개관\n{sc['R']}편\n— 담론 참고", fc="#f7f7f7", fs=7.5)
for x in (0.17, 0.5, 0.83): arrow(ax, 0.5, 0.44, x, 0.30)
box(ax, 0.35, -0.08, 0.30, 0.09, f"원문 표본 재판정 {ft['n']}편", fc="#fbeee6", ec=ACC2, fs=7.5)
arrow(ax, 0.5, 0.12, 0.5, 0.01)
fig.savefig(OUT + "fig4_1_prisma.png", bbox_inches="tight"); plt.close(fig)

# 그림 5-1 연도별
years = list(range(2007, 2027))
def yc(dec): 
    c = collections.Counter(R[s["id"]]["year"] for s in S if s["decision"] == dec); return [c.get(y, 0) for y in years]
fig, ax = plt.subplots(figsize=(6.3, 2.8))
b1 = yc("I"); b2 = yc("R"); b3 = yc("N")
ax.bar(years, b1, color=ACC, label="1차 연구(판정)")
ax.bar(years, b2, bottom=b1, color="#9fbad0", label="리뷰·개관")
ax.bar(years, b3, bottom=[a + b for a, b in zip(b1, b2)], color="#d9d9d9", label="초록 없음(적격)")
ax.set_xticks(years[::2]); ax.set_ylabel("편수"); ax.legend(frameon=False, fontsize=7.5, loc="upper left", title="2026년은 11월 22일까지", title_fontsize=7)
fig.savefig(OUT + "fig5_1_years.png", bbox_inches="tight"); plt.close(fig)

# 그림 5-2 모방 수준 × 근거 유형
Ls = ["form", "material", "process", "ecosystem", "unclear"]; Lk = ["형태", "구조·재료", "과정·행동", "생태계", "불명"]
Es = [0, 1, 2, 3, 4]; Ek = ["개념", "설계안", "시뮬레이션", "시제품·실험", "실건물 측정"]
cols_ = ["#e3e3e3", "#c9d6e2", "#8fb0cb", ACC, "#0f3550"]
fig, ax = plt.subplots(figsize=(6.3, 2.6)); left = [0] * 5
for e, lab, col in zip(Es, Ek, cols_):
    v = [sum(1 for c in C.values() if c["L"] == L and c["E"] == e) for L in Ls]
    ax.barh(Lk, v, left=left, color=col, label=lab); left = [a + b for a, b in zip(left, v)]
for k, t in enumerate(left): ax.text(t + 1, k, str(t), va="center", fontsize=7.5)
ax.invert_yaxis(); ax.set_xlabel("편수"); ax.legend(frameon=False, fontsize=7, ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.0))
fig.savefig(OUT + "fig5_2_level_evidence.png", bbox_inches="tight"); plt.close(fig)

# 그림 6-1 항목별 비율과 신뢰구간
order = ["B1 생물 모델 명시", "B2≥1 기능 이상 기술", "B2=2 기제 기술", "T1 전이 절차 명시", "E≥2 시뮬레이션 이상", "E≥3 시제품·실험 이상", "E=4 실건물 측정", "Q 정량 성능", "R≥1 비교 기준 있음", "R=3 같은 기능 비생체모방 대안", "S1 지속가능성 주장", "S2=2 전과정 근거"]
lab = ["특정 생물 명시(B1)", "생물 기능 이상 기술(B2≥1)", "생물 기제 기술(B2=2)", "전이 절차 명시(T1)", "시뮬레이션 이상(E≥2)", "시제품·실험 이상(E≥3)", "실건물 측정(E=4)", "정량 성능 보고(Q)", "비교 기준 있음(R≥1)", "같은 기능 대안과 비교(R=3)", "지속가능성 주장(S1)", "전과정 근거(S2=2)"]
p = [res["items"][k]["pct"] for k in order]; lo = [res["items"][k]["ci"][0] for k in order]; hi = [res["items"][k]["ci"][1] for k in order]
fig, ax = plt.subplots(figsize=(6.3, 3.6))
colors = [ACC2 if k in ("R=3 같은 기능 비생체모방 대안", "S2=2 전과정 근거", "B2=2 기제 기술") else ACC for k in order]
ax.barh(lab, p, color=colors, height=0.6)
ax.errorbar(p, range(len(p)), xerr=[[a - b for a, b in zip(p, lo)], [b - a for a, b in zip(p, hi)]], fmt="none", ecolor=INK, lw=0.7, capsize=2)
for k, v in enumerate(p): ax.text(hi[k] + 1.2, k, f"{v:.1f}%", va="center", fontsize=7.5)
ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel(f"193편 중 비율(%), 막대 끝선은 95% 신뢰구간")
fig.savefig(OUT + "fig6_1_items.png", bbox_inches="tight"); plt.close(fig)

# 그림 6-2 근거 사다리
steps = ["전체", "① 생물 출처 근거\n(B1·B2≥1)", "② + 전이 절차\n(T1)", "③ + 정량 성능\n(E≥2·Q)", "④ + 같은 기능 대안과\n비교(R=3)"]
vals = [res["N"]] + [res["ladder_cum"][f"≥{k}"]["k"] for k in range(1, 5)]
fig, ax = plt.subplots(figsize=(6.3, 2.7))
ax.bar(range(5), vals, color=[MUTE, ACC, ACC, ACC, ACC2], width=0.62)
for k, v in enumerate(vals): ax.text(k, v + 3, f"{v}편\n({100*v/res['N']:.1f}%)" if k else f"{v}편", ha="center", fontsize=7.5)
ax.set_xticks(range(5)); ax.set_xticklabels(steps, fontsize=7.5); ax.set_ylabel("편수"); ax.set_ylim(0, 230)
fig.savefig(OUT + "fig6_2_ladder.png", bbox_inches="tight"); plt.close(fig)

# 그림 6-3 시기별
keys = [("B2=2 기제 기술", "생물 기제 기술"), ("T1 전이 절차 명시", "전이 절차"), ("Q 정량 성능", "정량 성능"), ("R=3 같은 기능 비생체모방 대안", "같은 기능 대안과 비교"), ("S1 지속가능성 주장", "지속가능성 주장")]
pers = ["2007–2018", "2019–2022", "2023–2026"]
fig, ax = plt.subplots(figsize=(6.3, 2.8))
for (k, l), m in zip(keys, ["o", "s", "^", "D", "v"]):
    y = [res["by_period"][k][q]["pct"] for q in pers]
    ax.plot(pers, y, marker=m, lw=1, ms=4, label=f"{l} (p={res['trend'][k]['p']:.2f})")
ax.set_ylabel("비율(%)"); ax.set_ylim(0, 42); ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
ax.set_xticks(range(3)); ax.set_xticklabels([f"{q}\n(n={res['period_n'][q]})" for q in pers])
fig.savefig(OUT + "fig6_3_period.png", bbox_inches="tight"); plt.close(fig)

# 그림 6-4 초록 대 원문
ks = [("B1", "생물 명시"), ("B2>=1", "기능 이상"), ("B2=2", "기제"), ("T1", "전이 절차"), ("Q", "정량 성능"), ("R>=1", "비교 기준"), ("R=3", "같은 기능\n대안"), ("S2=2", "전과정\n근거")]
fig, ax = plt.subplots(figsize=(6.3, 2.6)); import numpy as np
x = np.arange(len(ks)); w = 0.38
ax.bar(x - w / 2, [ft[k]["abs_pct"] for k, _ in ks], w, color="#9fbad0", label="초록 판정")
ax.bar(x + w / 2, [ft[k]["ft_pct"] for k, _ in ks], w, color=ACC, label="원문 판정")
ax.set_xticks(x); ax.set_xticklabels([l for _, l in ks], fontsize=7.5); ax.set_ylabel(f"원문 표본 {ft['n']}편 중 비율(%)"); ax.legend(frameon=False, fontsize=7.5)
fig.savefig(OUT + "fig6_4_fulltext.png", bbox_inches="tight"); plt.close(fig)

# 그림 7-1 사례: 고정 대 컷오프(= '해바라기·솔방울' 이름), 꿀벌 대 시차
db = sqlite3.connect("/home/claude/badtm/data/db/research.sqlite")
r3 = {t: (e, p) for t, e, p in db.execute("select tag,dEUI_pct,dpeak_pct from results_3bldg")}
import statistics as st
med = {t: st.median([r[0] for r in db.execute("select dEUI_pct from results_257 where tag=?", (t,))]) for t in ["F0", "S3", "LH_F0", "LH_C", "VF_F0", "VF_C"]}
fig, axs = plt.subplots(1, 2, figsize=(6.3, 2.7))
devs = ["블라인드", "수평 루버", "수직 루버"]; fx = ["F0", "LH_F0", "VF_F0"]; cu = ["S3", "LH_C", "VF_C"]
x = np.arange(3)
axs[0].bar(x - 0.2, [r3[t][0] for t in fx], 0.38, color="#9fbad0", label="고정")
axs[0].bar(x + 0.2, [r3[t][0] for t in cu], 0.38, color=ACC2, label="컷오프 각도 제어\n(이전 원고: 해바라기·솔방울 원리)")
axs[0].axhline(0, color=INK, lw=0.6); axs[0].set_xticks(x); axs[0].set_xticklabels(devs); axs[0].set_ylabel("연간 EUI 변화(%)"); axs[0].set_title("(a) 상세 3개 동 블록", fontsize=8.5)
fig.legend(*axs[0].get_legend_handles_labels(), frameon=False, fontsize=7, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.08))
axs[1].bar(x - 0.2, [med[t] for t in fx], 0.38, color="#9fbad0"); axs[1].bar(x + 0.2, [med[t] for t in cu], 0.38, color=ACC2)
axs[1].axhline(0, color=INK, lw=0.6); axs[1].set_xticks(x); axs[1].set_xticklabels(devs); axs[1].set_title("(b) 257동 건물별 중앙값", fontsize=8.5)
fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(OUT + "fig7_1_case_p2.png", bbox_inches="tight"); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.3, 2.4))
labs = ["꿀벌 원리: 작동 역치 분산\n(3개 동, 125가지 배정, 균일 대비)", "일반 운영: 운전 시차 ±2시간\n(3개 동, 장치 없음)", "일반 운영: 운전 시차 ±1시간\n(257동, 장치 없음)", "일반 운영: 운전 시차 ±2시간\n(257동, 장치 없음)"]
lo_ = [-0.09, -4.54, -2.181, -3.307]; hi_ = [0.20, -4.54, -2.181, -3.307]
for k, (a, b) in enumerate(zip(lo_, hi_)):
    if a == b: ax.plot([a], [k], "o", color=ACC if k else ACC2)
    else: ax.plot([a, b], [k, k], lw=5, color=ACC2, solid_capstyle="butt")
    ax.text(min(a, b) - 0.15, k, (f"{a:+.2f}%" if a == b else f"{a:+.2f}~{b:+.2f}%").replace("-", "−"), ha="right", va="center", fontsize=7.5)
ax.axvline(0, color=INK, lw=0.6); ax.set_yticks(range(4)); ax.set_yticklabels(labs, fontsize=7.5); ax.set_xlim(-6, 1); ax.invert_yaxis()
ax.set_xlabel("블록 최대 전력 변화(%)")
fig.savefig(OUT + "fig7_2_case_p4.png", bbox_inches="tight"); plt.close(fig)
print("ok")
