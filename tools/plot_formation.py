#!/usr/bin/env python3
"""
Formation energy of the iodine vacancy against the Fermi level (step 8, preliminary).

  E_f(V_I^q) = E_def(q) - E_bulk + mu_I + q (E_VBM + dV + E_F) + E_corr(q)
  mu_I = mu_I0 + dmu_I,  mu_I0 = E(solid I2)/atom

Preliminary: PBEsol band edges of the 160-atom cell, alignment dV from the mean
core potential of the 32 Cs, image-charge term estimated (0.06 eV for +1).
Usage: python3 tools/plot_formation.py --out assets/formation_energy_prelim.png
"""
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

FONT = "Inter" if any(f.name == "Inter" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.linewidth": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in",
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6})
CM = 1 / 2.54
TXT, MUT, OR, PU = "#0B0B0B", "#52514E", "#D85A30", "#7F77DD"

# VASP PBEsol, eV (NOTES.md job log)
E_BULK = -486.51068
E_DEF = {+1: -485.98408, 0: -482.55124}       # 4c site (8d: +0.9 meV and +33.5 meV)
DV = {+1: -0.0413, 0: 0.0}                    # eFNV site-potential alignment (tools/efnv_correction.py, vasp/08_fnv/efnv.txt)
E_CORR = {+1: 0.0489, 0: 0.0}                 # eFNV point-charge term, static dielectric tensor (DFPT)
E_VBM, E_CBM = 1.8489, 3.4679                 # pristine EIGENVAL
MU_I0 = -7.02297865 / 4                       # solid I2, 4 atoms
DMU = {"I-rich": 0.0, "I-poor": -0.953}       # stability strip (CsI, PbI2, Pb limits)


def ef(q, dmu, EF):
    return E_DEF[q] - E_BULK + MU_I0 + dmu + q * (E_VBM + DV[q] + EF) + E_CORR[q]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/formation_energy_prelim.png")
    a = ap.parse_args()
    gap = E_CBM - E_VBM
    eps = ef(0, 0, 0) - ef(+1, 0, 0)          # transition level (+/0) above the VBM
    EF = np.linspace(0, gap, 400)
    fig, ax = plt.subplots(figsize=(8.5 * CM, 6.5 * CM))
    for (name, dmu), col in zip(DMU.items(), (PU, OR)):
        p, n = ef(+1, dmu, EF), ef(0, dmu, EF)
        ax.plot(EF, p, color=col, lw=0.6, ls=(0, (3, 2)), alpha=0.6)
        ax.plot(EF, np.full_like(EF, ef(0, dmu, 0)), color=col, lw=0.6, ls=(0, (3, 2)), alpha=0.6)
        ax.plot(EF, np.minimum(p, n), color=col, lw=1.4, label=name)
        ax.plot([eps], [ef(0, dmu, 0)], "o", ms=3.5, color=col)
        ax.text(0.06, ef(+1, dmu, 0.06) - 0.24, "+1", color=col, fontsize=8)
        ax.text(eps - 0.06, ef(0, dmu, 0) + 0.08, "0", color=col, fontsize=8, ha="right")
    ax.axhline(0, color=MUT, lw=0.5)
    ax.axvline(eps, color=MUT, lw=0.5, ls=":")
    ax.text(eps - 0.03, 2.6, "ε(+/0) = %.2f eV" % eps, color=MUT, fontsize=8, ha="right")
    ax.set_xlim(0, gap)
    ax.set_ylim(-1.0, 2.8)
    ax.set_xlabel("Fermi level above VBM (eV)")
    ax.set_ylabel("Formation energy (eV)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    ax.text(0.98, 0.04, "preliminary: PBEsol edges", transform=ax.transAxes, ha="right", fontsize=7, color=MUT)
    fig.tight_layout()
    fig.savefig(a.out, dpi=300)
    for name, dmu in DMU.items():
        print("%-6s E_f(+1) at VBM %.3f, at CBM %.3f; E_f(0) %.3f eV" % (name, ef(1, dmu, 0), ef(1, dmu, gap), ef(0, dmu, 0)))
    print("gap %.3f eV, eps(+/0) %.3f eV above VBM (%.3f below CBM)" % (gap, eps, gap - eps))


if __name__ == "__main__":
    main()
