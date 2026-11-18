#!/usr/bin/env python3
"""
Two literature figures for the CsPbI3 phase-diagram slides (project figure style).
  assets/phase_ladder.png        transition temperatures: experiment vs MLP (NEP3, vdW-DF-cx)
  assets/phase_delta_functional.png  delta-cubic transition temperature by functional (NEP3) vs experiment
Data: Marronnier et al., ACS Nano 12, 3477 (2018) (powder, cooling 2.5 C/min);
Holley, Burlingame, Loo, J. Mater. Chem. C (2025) (DSC, delta -> alpha 326 C; Ke et al. 320 C);
Fransson, Wiktor, Erhart, J. Phys. Chem. C 127, 13773 (2023) (NEP3/GPUMD; heating values; Table I);
Braeckevelt et al., arXiv:2602.20058 (2026) (experimental delta -> gamma range 548-599 K).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

FONT = "Inter" if any(f.name == "Inter" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.linewidth": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in",
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6})
CM = 1 / 2.54
TXT, MUT, OR, PU = "#0B0B0B", "#52514E", "#D85A30", "#7F77DD"

# ---- figure 1: temperature ladder ----
fig, ax = plt.subplots(figsize=(8.5 * CM, 7.0 * CM))
cols = {"Experiment": 0, "MLP (NEP3,\nvdW-DF-cx)": 1}
lines = [  # (column, T in K, label, colour, style)
    (0, 554, r"$\alpha\rightarrow\beta$  554 K (281 °C)", TXT, "-"),
    (0, 457, r"$\beta\rightarrow\gamma$  457 K (184 °C)", TXT, "-"),
    (0, 596, r"$\delta\rightarrow\alpha$  593–599 K (heating)", OR, "--"),
    (1, 487, r"tet.$\rightarrow$cubic  487 K", PU, "-"),
    (1, 340, r"orth.$\rightarrow$tet.  340 K", PU, "-"),
    (1, 635, r"$\delta$–cubic  635 K (free energy)", OR, "--"),
]
for c, T, lab, col, ls in lines:
    ax.plot([c - 0.38, c + 0.38], [T, T], color=col, lw=1.4, ls=ls)
    ax.text(c, T + 7, lab, ha="center", va="bottom", fontsize=7.5, color=col)
ax.axhline(300, color=MUT, lw=0.5, ls=":")
ax.text(1.45, 302, "room temperature", ha="right", va="bottom", fontsize=7, color=MUT)
ax.set_xlim(-0.55, 1.5)
ax.set_ylim(270, 690)
ax.set_xticks(list(cols.values()))
ax.set_xticklabels(list(cols.keys()))
ax.set_ylabel("Temperature (K)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(pad=0.3)
fig.savefig("assets/phase_ladder.png", dpi=600, facecolor="white")

# ---- figure 2: delta-cubic transition by functional ----
fig, ax = plt.subplots(figsize=(8.5 * CM, 5.5 * CM))
data = [("PBE", 310), ("PBEsol", 380), ("SCAN", 432), ("vdW-DF-cx", 635)]
y = range(len(data))
ax.axvspan(548, 599, color=OR, alpha=0.15, lw=0, zorder=0)
ax.text(573, len(data) - 0.5, "experiment 548–599 K", ha="center", va="bottom", fontsize=7.5, color=OR)
ax.set_ylim(-0.5, len(data) - 0.05)
for k, (name, T) in zip(y, data):
    col = PU if name == "PBEsol" else MUT
    ax.barh(k, T, height=0.55, color=col, zorder=2)
    ax.text(T + 8, k, "%d K" % T, va="center", fontsize=7.5, color=TXT)
ax.set_yticks(list(y))
ax.set_yticklabels([d[0] for d in data])
ax.set_xlim(0, 720)
ax.set_xlabel(r"$\delta$–cubic transition temperature (K)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(pad=0.3)
fig.savefig("assets/phase_delta_functional.png", dpi=600, facecolor="white")
print("written assets/phase_ladder.png, assets/phase_delta_functional.png")

# ---- figure 3: CsI-PbI2 pseudo-binary (van Hattem et al., J. Phys. Chem. C 127, 17482 (2023)) ----
# Measured invariant points (DSC); liquidus drawn as a schematic between them. The liquid
# composition at the Cs4PbI6 peritectic is not reported there: x = 0.30 is a placeholder.
fig, ax = plt.subplots(figsize=(10.0 * CM, 7.0 * CM))
xp = 0.30
liq = [(0.0, 904), (xp, 754), (0.38, 718), (0.50, 758), (0.80, 618), (1.0, 687)]
ax.plot([p[0] for p in liq], [p[1] for p in liq], color=TXT, lw=1.0, ls=(0, (4, 2)))
for x, T in liq:
    ax.plot(x, T, "o", ms=3.2, color=TXT)
# invariant lines
ax.plot([0.0, xp], [754, 754], color=TXT, lw=0.9)                 # peritectic
ax.plot([0.20, 0.50], [718, 718], color=TXT, lw=0.9)              # eutectic 1
ax.plot([0.50, 1.00], [618, 618], color=TXT, lw=0.9)              # eutectic 2
# compounds
ax.plot([0.20, 0.20], [300, 754], color=PU, lw=1.4)
ax.plot([0.50, 0.50], [300, 758], color=PU, lw=1.4)
ax.plot([0.20, 1.00], [599, 599], color=OR, lw=0.9)   # delta -> alpha of CsPbI3 crosses both two-phase fields
ax.text(0.62, 592, r"$\delta\rightarrow\alpha$ 599 K", fontsize=7, color=OR, va="top")
ax.text(0.20, 305, r"Cs$_4$PbI$_6$", fontsize=7.5, color=PU, ha="center", va="bottom",
        bbox=dict(fc="white", ec="none", pad=0.5))
ax.text(0.50, 305, r"CsPbI$_3$", fontsize=7.5, color=PU, ha="center", va="bottom",
        bbox=dict(fc="white", ec="none", pad=0.5))
lab = dict(fontsize=7, color=MUT, ha="center", va="center")
ax.text(0.62, 840, "liquid", **lab)
ax.text(0.10, 520, "CsI +\n" r"Cs$_4$PbI$_6$", **lab)
ax.text(0.35, 640, r"Cs$_4$PbI$_6$ +" "\n" r"$\alpha$-CsPbI$_3$", **lab)
ax.text(0.35, 450, r"Cs$_4$PbI$_6$ +" "\n" r"$\delta$-CsPbI$_3$", **lab)
ax.text(0.75, 450, r"$\delta$-CsPbI$_3$ + PbI$_2$", **lab)
ax.text(0.02, 912, "CsI 904 K", fontsize=7, color=TXT, va="bottom")
ax.text(0.98, 695, "PbI$_2$ 687 K", fontsize=7, color=TXT, ha="right", va="bottom")
ax.text(0.50, 766, "758 K", fontsize=7, color=TXT, ha="center", va="bottom")
ax.text(0.38, 708, "718 K", fontsize=7, color=TXT, ha="center", va="top")
ax.text(0.80, 628, "618 K", fontsize=7, color=TXT, ha="center", va="bottom")
ax.text(0.15, 762, "754 K", fontsize=7, color=TXT, ha="center", va="bottom")
ax.axhline(300, color=MUT, lw=0.5, ls=":")
ax.set_xlim(0, 1)
ax.set_ylim(290, 960)
ax.set_xlabel(r"Mole fraction PbI$_2$")
ax.set_ylabel("Temperature (K)")
ax.set_xticks([0, 0.2, 0.5, 0.8, 1.0])
ax.set_xticklabels(["CsI", "0.2", "0.5", "0.8", r"PbI$_2$"])
fig.tight_layout(pad=0.3)
fig.savefig("assets/phase_CsI_PbI2.png", dpi=600, facecolor="white")
print("written assets/phase_CsI_PbI2.png")
