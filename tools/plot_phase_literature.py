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
