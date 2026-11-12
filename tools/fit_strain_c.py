#!/usr/bin/env python3
"""
Fit E(c) for each in-plane strain (step 10, method of Xu et al. 2019, SI Note 1).

Input: a text file with one line per relaxed cell, "eps dc E" (strains in %, energy in eV),
made on the cluster with the grep loop in vasp/10_strain/README.md.

    python3 tools/fit_strain_c.py vasp/10_strain/unit/energies.txt --c0 12.4020 --out assets/strain_unit_Ec.png

For each eps, a cubic polynomial in dc is fitted (quadratic if fewer than 5 points); its minimum
gives the relaxed out-of-plane strain dc*(eps), c(eps) = c0(1 + dc*/100) and E_min(eps).
The effective Poisson-type ratio is reported as -dc*/eps. Figure: project style.
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
COLORS = ["#7F77DD", "#0B0B0B", "#D85A30", "#52514E", "#1D9E75"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--c0", type=float, required=True, help="unstrained c in A")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    d = np.loadtxt(a.data, comments="#")
    eps_all = np.unique(d[:, 0])
    fig, ax = plt.subplots(figsize=(8.5 * CM, 6.0 * CM)) if a.out else (None, None)
    emin0 = None
    rows = []
    for k, e in enumerate(eps_all):
        m = d[:, 0] == e
        dc, E = d[m, 1], d[m, 2]
        order = 3 if len(dc) >= 5 else 2
        p = np.polyfit(dc, E, order)
        x = np.linspace(dc.min(), dc.max(), 400)
        y = np.polyval(p, x)
        i = int(np.argmin(y))
        if i in (0, len(x) - 1):
            print("eps %+.1f: minimum at the edge of the scan, extend the c range" % e)
        rows.append((e, x[i], a.c0 * (1 + x[i] / 100), y[i]))
        if e == 0:
            emin0 = y[i]
        if ax is not None:
            ax.plot(x, (y - y[i]) * 1000, color=COLORS[k % len(COLORS)], lw=1.0)
            ax.plot(dc, (E - y[i]) * 1000, "o", ms=3.5, color=COLORS[k % len(COLORS)], label="ε = %+.1f%%" % e)
    print("%8s %10s %10s %14s %12s %10s" % ("eps (%)", "dc* (%)", "c (A)", "E_min (eV)", "dE (meV)", "-dc*/eps"))
    for e, dcs, c, em in rows:
        de = (em - emin0) * 1000 if emin0 is not None else float("nan")
        r = -dcs / e if e != 0 else float("nan")
        print("%8.1f %10.3f %10.4f %14.6f %12.2f %10.3f" % (e, dcs, c, em, de, r))
    if ax is not None:
        ax.set_xlabel("Out-of-plane strain of c (%)")
        ax.set_ylabel("Energy above the minimum (meV)")
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout(pad=0.3)
        fig.savefig(a.out, dpi=600, facecolor="white")
        print("written", a.out)


if __name__ == "__main__":
    main()
