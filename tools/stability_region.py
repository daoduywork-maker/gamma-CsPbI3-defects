#!/usr/bin/env python3
"""
Chemical-potential stability region of gamma-CsPbI3 from the VASP energies (step 5).

Formation enthalpies (eV per formula unit) from the VASP reference phases (job 217911)
and the relaxed gamma unit cell / 4 (job 217910); elements bcc Cs, fcc Pb, solid I2.

Conditions (Delta mu_i = mu_i - mu_i(element)):
    Delta mu_Cs + Delta mu_Pb + 3 Delta mu_I = DH(CsPbI3)      (CsPbI3 forms)
    every Delta mu_i <= 0                                      (no element precipitates)
    Delta mu_Cs + Delta mu_I   <= DH(CsI)                      (no CsI)
    Delta mu_Pb + 2 Delta mu_I <= DH(PbI2)                     (no PbI2)
delta-CsPbI3 has the same composition, so it cannot be a boundary: it either leaves the
region unchanged (if above gamma) or removes it (if below), and gamma is then treated as
metastable, as is usual for the perovskite phases.

Writes assets/stability_region.png and vasp/05_reference_phases/stability_region.txt.
Run from the project root:  python3 tools/stability_region.py
"""

import itertools
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Polygon

DH_VASP = {"CsI": -3.079, "PbI2": -1.827, "CsPbI3": -4.985}   # eV per formula unit

# ---- figure style (same as the other project figures) ---------------------------
FONT = "Inter" if any(f.name == "Inter" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in"})
CM = 1 / 2.54
TXT, MUT, ORANGE, PURPLE, FILL = "#0B0B0B", "#52514E", "#D85A30", "#7F77DD", "#DCD9F5"
# ------------------------------------------------------------------------------


def load():
    return dict(DH_VASP)


def region(dh):
    """Vertices of {A x <= b} in x = (dmu_Pb, dmu_I)."""
    H = dh["CsPbI3"]
    A = np.array([[1, 0], [0, 1],            # dmu_Pb <= 0, dmu_I <= 0
                  [-1, -3],                  # dmu_Cs <= 0
                  [-1, -2],                  # no CsI
                  [1, 2]])                   # no PbI2
    b = np.array([0, 0, -H, -(H - dh["CsI"]), dh["PbI2"]])
    pts = []
    for i, j in itertools.combinations(range(len(A)), 2):
        M = A[[i, j]]
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        x = np.linalg.solve(M, b[[i, j]])
        if np.all(A @ x <= b + 1e-9):
            pts.append(x)
    pts = np.unique(np.round(pts, 6), axis=0)
    c = pts.mean(axis=0)
    return pts[np.argsort(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))]


def main():
    dh = load()
    H = dh["CsPbI3"]
    V = region(dh)
    names = {}
    # label the corners: I-rich end (dmu_I = 0) and I-poor end (dmu_Pb = 0)
    for v in V:
        if abs(v[1]) < 1e-6:
            names[tuple(v)] = "A" if v[0] < V[:, 0][np.abs(V[:, 1]) < 1e-6].max() else "B"
        elif abs(v[0]) < 1e-6:
            names[tuple(v)] = "C" if v[1] > V[:, 1][np.abs(V[:, 0]) < 1e-6].min() else "D"

    fig, ax = plt.subplots(figsize=(8.5 * CM, 7.0 * CM))
    xs = np.linspace(-2.4, 0.3, 50)
    ax.plot(xs, (dh["PbI2"] - xs) / 2, color=TXT, lw=0.9, label="PbI$_2$ forms above")
    ax.plot(xs, (H - dh["CsI"] - xs) / 2, color=ORANGE, lw=0.9, ls=(0, (4, 2.5)), label="CsI forms below")
    ax.add_patch(Polygon(V, closed=True, fc=FILL, ec=PURPLE, lw=0.6, zorder=3,
                         label="$\\gamma$-CsPbI$_3$ stable"))
    for v in V:
        n = names.get(tuple(v))
        if n:
            ax.plot(*v, "o", ms=3.2, color=PURPLE, zorder=4)
            dx, dy, ha, va = {"A": (-0.04, -0.03, "right", "top"), "B": (0.03, 0.03, "left", "bottom"),
                              "C": (-0.06, 0.03, "right", "bottom"), "D": (-0.06, -0.03, "right", "top")}[n]
            ax.text(v[0] + dx, v[1] + dy, n, color=PURPLE, ha=ha, va=va, fontweight="semibold", zorder=5)
    ax.axhline(0, color=MUT, lw=0.5)
    ax.axvline(0, color=MUT, lw=0.5)
    ax.set_xlim(-2.3, 0.25)
    ax.set_ylim(-1.15, 0.2)
    ax.set_xlabel("$\\Delta\\mu_{\\mathrm{Pb}}$ (eV)")
    ax.set_ylabel("$\\Delta\\mu_{\\mathrm{I}}$ (eV)")
    ax.legend(frameon=False, loc="lower left", fontsize=8, handlelength=2.2)
    ax.text(0.97, 0.95, "strip width %.0f meV" % ((dh["PbI2"] - H + dh["CsI"]) * 1000),
            transform=ax.transAxes, ha="right", va="top", color=MUT, fontsize=8)
    fig.tight_layout(pad=0.3)
    os.makedirs("assets", exist_ok=True)
    fig.savefig("assets/stability_region.png", dpi=600, facecolor="white")

    rep = ["Stability region of gamma-CsPbI3 (VASP PBEsol, elements: bcc Cs, fcc Pb, solid I2)", "",
           "Formation enthalpies (eV per formula unit):"]
    rep += ["  %-7s %8.3f" % (k, v) for k, v in dh.items()]
    rep += ["", "Decomposition CsPbI3 -> CsI + PbI2: %.3f eV per formula unit (negative = CsPbI3 stable)"
            % (H - dh["CsI"] - dh["PbI2"]), "",
            "Corners (eV):   dmu_Cs    dmu_Pb    dmu_I"]
    for v in V:
        n = names.get(tuple(v), "-")
        rep.append("  %s           %7.3f   %7.3f   %7.3f" % (n, H - v[0] - 3 * v[1], v[0], v[1]))
    rep += ["", "A, B: iodine-rich (dmu_I = 0). C, D: lead-rich, iodine-poor (dmu_Pb = 0).",
            "Cs4PbI6 and CsPb2I5 not included (published phase diagrams cited instead)."]
    open("vasp/05_reference_phases/stability_region.txt", "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
