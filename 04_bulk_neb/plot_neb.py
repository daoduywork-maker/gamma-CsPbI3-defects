#!/usr/bin/env python3
"""
Plot a QE neb.x energy profile (the <prefix>.dat images and the <prefix>.int curve).

    python3 04_bulk_neb/plot_neb.py 04_bulk_neb/q+1/S1/neb_S1_qp1 --label "S1, +1" --out assets/neb_S1_qp1.png

The .dat file has: reaction coordinate (0-1), energy (eV, relative to image 1), error (eV/A).
The .int file has: reaction coordinate, interpolated energy (eV).
Figure style: the project style (Inter, 9 pt, purple/orange/black).
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", help="path to <prefix> (reads <prefix>.dat and <prefix>.int)")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--path-length", type=float, default=None,
                    help="total path length in A (x axis in A instead of 0-1)")
    a = ap.parse_args()

    d = np.loadtxt(a.prefix + ".dat")
    c = np.loadtxt(a.prefix + ".int")
    xs, xc = d[:, 0], c[:, 0]
    xlab = "Reaction coordinate (normalized)"
    if a.path_length:
        xs, xc, xlab = xs * a.path_length, xc * a.path_length, "Reaction coordinate (Å)"
    e, ec = d[:, 1], c[:, 1]
    k = int(np.argmax(e))

    fig, ax = plt.subplots(figsize=(8.5 * CM, 6.0 * CM))
    ax.plot(xc, ec, color=TXT, lw=1.0, zorder=2)
    ax.plot(xs, e, "o", ms=4.5, color=PU, zorder=3, label="NEB images")
    ax.plot(xs[k], e[k], "o", ms=6.5, mfc="none", mec=OR, mew=1.2, zorder=4, label="climbing image")
    ax.annotate("", xy=(xs[k], e[k]), xytext=(xs[k], 0), arrowprops=dict(arrowstyle="<->", color=MUT, lw=0.8))
    ax.text(xs[k] + 0.02 * (xs[-1] - xs[0]), e[k] / 2, "%.3f eV" % e[k], va="center", color=TXT)
    ax.axhline(0, color=MUT, lw=0.5, ls=(0, (3, 2)))
    ax.set_xlabel(xlab)
    ax.set_ylabel("Energy (eV)")
    ax.set_xlim(xs[0] - 0.03 * (xs[-1] - xs[0]), xs[-1] + 0.03 * (xs[-1] - xs[0]))
    ax.set_ylim(-0.04, max(e) * 1.25)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    if a.label:
        ax.text(0.03, 0.95, a.label, transform=ax.transAxes, va="top", fontweight="semibold")
    fig.tight_layout(pad=0.3)
    fig.savefig(a.out, dpi=600, facecolor="white")
    print("barrier %.3f eV at image %d; written %s" % (e[k], k + 1, a.out))


if __name__ == "__main__":
    main()
