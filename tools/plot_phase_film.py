#!/usr/bin/env python3
"""CsI-PbI2 phase diagram (van Hattem et al. 2023 data) with the CsPbI3 phases marked: stable alpha and delta, quench path through beta (533 K) and gamma (448 K) from Marronnier et al. 2018. Output: assets/phase_CsI_PbI2_phases.png"""
import matplotlib, warnings; matplotlib.use("Agg"); warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
from matplotlib import font_manager
FONT = "Inter" if any(f.name == "Inter" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.linewidth": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in"})
CM = 1/2.54; TXT, MUT, OR, PU = "#0B0B0B", "#52514E", "#D85A30", "#7F77DD"
XP = 0.30   # liquid at the peritectic: not reported, placeholder
LIQ = [(0, 904), (XP, 754), (0.38, 718), (0.50, 758), (0.80, 618), (1.0, 687)]
def liquidus(x):
    for (x1, T1), (x2, T2) in zip(LIQ, LIQ[1:]):
        if x1 <= x <= x2: return T1 + (T2 - T1) * (x - x1) / (x2 - x1)
def base(ax, fields=True, temps=True):
    ax.plot(*zip(*LIQ), color=TXT, lw=1.1)
    ax.plot([0, XP], [754, 754], color=TXT, lw=0.9); ax.plot([0.20, 0.50], [718, 718], color=TXT, lw=0.9)
    ax.plot([0.50, 1.0], [618, 618], color=TXT, lw=0.9); ax.plot([0.20, 1.0], [599, 599], color=OR, lw=0.9)
    ax.plot([0.20, 0.20], [300, 754], color=PU, lw=1.6); ax.plot([0.50, 0.50], [300, 758], color=PU, lw=1.6)
    for x, T in LIQ: ax.plot(x, T, "o", ms=3, color=TXT, zorder=5)
    ax.set_xlim(0, 1); ax.set_ylim(290, 960)
    ax.set_xticks([0, 0.2, 0.38, 0.5, 0.8, 1.0]); ax.set_xticklabels(["CsI", "0.2", "0.38", "0.5", "0.8", r"PbI$_2$"])
    ax.set_xlabel(r"Mole fraction PbI$_2$"); ax.set_ylabel("Temperature (K)")
    ax.text(0.20, 300, r"Cs$_4$PbI$_6$", fontsize=7.5, color=PU, ha="center", va="bottom", bbox=dict(fc="white", ec="none", pad=0.5))
    ax.text(0.50, 300, r"CsPbI$_3$", fontsize=7.5, color=PU, ha="center", va="bottom", bbox=dict(fc="white", ec="none", pad=0.5))
    if temps:
        for x, T, s, ha, va in ((0.01, 912, "904 K", "left", "bottom"), (0.13, 760, "754 K (P)", "center", "bottom"),
                                (0.38, 710, "718 K (E1)", "center", "top"), (0.50, 766, "758 K (C)", "center", "bottom"),
                                (0.80, 588, "618 K (E2)", "center", "top"), (0.99, 695, "687 K", "right", "bottom")):
            ax.text(x, T, s, fontsize=7, ha=ha, va=va, color=TXT)
        ax.text(0.60, 592, "599 K", fontsize=7, color=OR, va="top")
    if fields:
        L = dict(fontsize=7, color=MUT, ha="center", va="center")
        ax.text(0.65, 880, "L (liquid)", **L)
        ax.text(0.09, 800, "L + CsI", **L)
        ax.annotate(r"L + Cs$_4$PbI$_6$", (0.29, 742), xytext=(0.33, 830), fontsize=6.5, color=MUT, ha="center",
                    arrowprops=dict(arrowstyle="-", color=MUT, lw=0.5))
        ax.annotate(r"L + $\alpha$", (0.45, 735), xytext=(0.47, 800), fontsize=6.5, color=MUT, ha="center",
                    arrowprops=dict(arrowstyle="-", color=MUT, lw=0.5))
        ax.text(0.62, 680, r"L + $\alpha$", **L)
        ax.text(0.92, 636, r"L + PbI$_2$", fontsize=6.5, color=MUT, ha="center")
        ax.text(0.10, 520, "CsI +\n" r"Cs$_4$PbI$_6$", **L)
        ax.text(0.35, 655, r"Cs$_4$PbI$_6$ + $\alpha$", **L)
        ax.text(0.35, 450, r"Cs$_4$PbI$_6$ + $\delta$", **L)
        ax.text(0.75, 450, r"$\delta$ + PbI$_2$", **L)
from matplotlib.patches import Polygon
fig, ax = plt.subplots(figsize=(11*CM, 8.6*CM))
base(ax, fields=False, temps=False)
ax.set_ylim(270, 960)
# stable phases of CsPbI3 (x = 0.5)
ax.add_patch(Polygon([(0.47, 599), (0.53, 599), (0.53, 752), (0.47, 752)], closed=True, fc="#FFE9A8", ec=OR, lw=0.8, zorder=1))
ax.text(0.445, 683, r"$\alpha$", fontsize=11, fontweight="bold", color="#8A2D10", ha="right", va="center")
ax.text(0.445, 660, "stable\n599–758 K", fontsize=6.5, color="#8A2D10", ha="right", va="top")
ax.plot([0.5, 0.5], [345, 599], color=PU, lw=4.0, zorder=3)
ax.text(0.445, 470, r"$\delta$", fontsize=11, fontweight="bold", color=PU, ha="right", va="center")
ax.text(0.445, 440, "stable\nbelow 599 K", fontsize=6.5, color=PU, ha="right", va="top")
# quench path (metastable, not on the equilibrium diagram)
xq = 0.60
ax.annotate("", xy=(xq, 305), xytext=(xq, 690), arrowprops=dict(arrowstyle="->", color=TXT, lw=1.1, ls=(0, (3, 2))))
ax.plot([0.53, xq], [690, 690], color=TXT, lw=0.6, ls=(0, (1, 1.5)))
for T, s, c in ((533, r"$\beta$ below 533 K", OR), (448, r"$\gamma$ below 448 K", OR)):
    ax.plot(xq, T, "s", ms=4.5, color=c, zorder=6)
    ax.text(xq + 0.025, T, s, fontsize=8, fontweight="bold", color=c, va="center",
            bbox=dict(fc="white", ec="none", pad=0.5))
ax.text(xq + 0.025, 578, "fast cooling (metastable)", fontsize=6.5, color=TXT, va="center",
        bbox=dict(fc="white", ec="none", pad=0.5))
ax.text(xq + 0.025, 340, r"$\gamma$ kept at room T", fontsize=6.5, color=TXT, va="center",
        bbox=dict(fc="white", ec="none", pad=0.5))
ax.text(0.65, 880, "liquid", fontsize=7, color=MUT, ha="center")
fig.tight_layout(pad=0.3); fig.savefig("assets/phase_CsI_PbI2_phases.png", dpi=500, facecolor="white")

