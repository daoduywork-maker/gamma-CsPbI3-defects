#!/usr/bin/env python3
"""
Chemical-potential stability region of gamma-CsPbI3 (step 5).

Reads the final total energies of the reference phases (05_reference_phases/*/vcrelax.out)
when they are present; otherwise uses the values below (job 217708, 23 Oct 2026).
The CsPbI3 energy is the perfect 160-atom supercell / 32 (job 217406).

Conditions (Delta mu_i = mu_i - mu_i(element), elements: bcc Cs, fcc Pb, solid I2):
    Delta mu_Cs + Delta mu_Pb + 3 Delta mu_I = DH(CsPbI3)      (CsPbI3 forms)
    every Delta mu_i <= 0                                      (no element precipitates)
    Delta mu_Cs + Delta mu_I   <= DH(CsI)                      (no CsI)
    Delta mu_Pb + 2 Delta mu_I <= DH(PbI2)                     (no PbI2)
Eliminating Delta mu_Cs leaves a polygon in the (Delta mu_Pb, Delta mu_I) plane.
delta-CsPbI3 is left out on purpose (same composition; it would empty the region).

Writes assets/stability_region.png and 05_reference_phases/stability_region.txt.
Run from the project root:  python3 05_reference_phases/stability_region.py
"""

import itertools
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Polygon

RY = 13.605693122994  # eV
E = {  # final total energies, Ry, per cell (job 217708)
    "Cs": (-62.89427877, 1), "Pb": (-859.43397176, 1), "I2": (-1491.69347976, 4),
    "CsI": (-436.04489173, 1), "PbI2": (-1605.41570805, 1),
}
E_PERFECT, N_FU = -65326.88713687, 32   # perfect 2x2x2 supercell, job 217406

# ---- figure style (same as the other project figures) ---------------------------
FONT = "Inter" if any(f.name == "Inter" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in"})
CM = 1 / 2.54
TXT, MUT, ORANGE, PURPLE, FILL = "#0B0B0B", "#52514E", "#D85A30", "#7F77DD", "#DCD9F5"
# ------------------------------------------------------------------------------


def final_energy(path):
    last = None
    for line in open(path):
        if line.startswith("!"):
            last = float(line.split()[4])
    return last


def load():
    for k, n in (("Cs", "Cs"), ("Pb", "Pb"), ("I2", "I2"), ("CsI", "CsI"), ("PbI2", "PbI2")):
        p = os.path.join("05_reference_phases", n, "vcrelax.out")
        if os.path.exists(p):
            E[k] = (final_energy(p), E[k][1])
    mu = {"Cs": E["Cs"][0] / E["Cs"][1], "Pb": E["Pb"][0] / E["Pb"][1], "I": E["I2"][0] / E["I2"][1]}
    dh = {"CsI": (E["CsI"][0] - mu["Cs"] - mu["I"]) * RY,
          "PbI2": (E["PbI2"][0] - mu["Pb"] - 2 * mu["I"]) * RY,
          "CsPbI3": (E_PERFECT / N_FU - mu["Cs"] - mu["Pb"] - 3 * mu["I"]) * RY}
    return dh


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
            dx, ha = (0.05, "left") if n == "B" else ((-0.14, "right") if n == "A" else (-0.06, "right"))
            ax.text(v[0] + dx, v[1] + ((-0.06 if n == "A" else 0.03) if n in "AC" else -0.03), n, color=PURPLE, ha=ha,
                    va="bottom" if n == "C" else "top", fontweight="semibold", zorder=5)
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

    rep = ["Stability region of gamma-CsPbI3 (PBEsol, elements: bcc Cs, fcc Pb, solid I2)", "",
           "Formation enthalpies (eV per formula unit):"]
    rep += ["  %-7s %8.3f" % (k, v) for k, v in dh.items()]
    rep += ["", "Decomposition CsPbI3 -> CsI + PbI2: %.3f eV per formula unit (negative = CsPbI3 stable)"
            % (H - dh["CsI"] - dh["PbI2"]), "",
            "Corners (eV):   dmu_Cs    dmu_Pb    dmu_I"]
    for v in V:
        n = names.get(tuple(v), "-")
        rep.append("  %s           %7.3f   %7.3f   %7.3f" % (n, H - v[0] - 3 * v[1], v[0], v[1]))
    rep += ["", "A, B: iodine-rich (dmu_I = 0). C, D: lead-rich, iodine-poor (dmu_Pb = 0).",
            "Cs4PbI6 and CsPb2I5 not yet included; they can only shrink the region."]
    open("05_reference_phases/stability_region.txt", "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
