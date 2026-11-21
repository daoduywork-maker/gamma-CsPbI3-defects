#!/usr/bin/env python3
"""E_f(V_I+) against biaxial strain, from vasp/06_strain/super/ef_strain.txt -> assets/ef_strain.png (project style)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
FONT = "Inter" if any(f.name == "Inter" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.linewidth": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in"})
CM = 1 / 2.54
TXT, MUT, OR, PU = "#0B0B0B", "#52514E", "#D85A30", "#7F77DD"
rows = [l.split() for l in open("vasp/06_strain/super/ef_strain.txt") if l.strip() and not l.startswith("#")]
eps = np.array([float(r[0]) for r in rows]); ef = np.array([float(r[6]) for r in rows]); site = [r[5] for r in rows]
fig, ax = plt.subplots(figsize=(8.5 * CM, 6.2 * CM))
ax.plot(eps, ef, color=TXT, lw=1.0, zorder=2)
for x, y, s in zip(eps, ef, site):
    ax.plot(x, y, "o", ms=6, color=PU if s == "4c" else OR, zorder=3)
    if x < 0:
        ax.text(x, y + 0.004, "%.3f" % y, ha="center", va="bottom", fontsize=8, color=TXT)
    else:
        ax.text(x - 0.07, y - 0.004, "%.3f" % y, ha="right", va="top", fontsize=8, color=TXT)
ax.plot([], [], "o", color=PU, label="4c lower"); ax.plot([], [], "o", color=OR, label="8d lower")
ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.set_xlabel("Biaxial strain ε (%)"); ax.set_ylabel(r"$E_f(V_\mathrm{I}^{+})$ (eV)")
ax.set_xticks(eps); ax.set_ylim(0.585, 0.69)
ax.text(0.98, 0.95, "I-rich, $E_F$ at VBM", transform=ax.transAxes, ha="right", va="top", color=MUT, fontsize=8)
fig.tight_layout(pad=0.3)
fig.savefig("assets/ef_strain.png", dpi=500, facecolor="white")
print("written assets/ef_strain.png")
