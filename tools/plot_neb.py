#!/usr/bin/env python3
"""
Plot a NEB energy profile: QE neb.x (<prefix>.dat and <prefix>.int) or VASP/VTST (--vasp).

VASP: python3 tools/plot_neb.py --vasp vasp/04_bulk_neb/q+1/S1 --label "S1, +1" --out assets/neb_S1_qp1_vasp.png
reads <dir>/neb_data.txt (image, energy, force along the tangent) and the image structures
(<dir>/NN/CONTCAR, falling back to POSCAR); reaction coordinate = cumulative distance between
images (all atoms, minimum image), curve = cubic Hermite spline with slope -F_tangent at every
image (as VTST nebbarrier.pl).

QE:

    python3 tools/plot_neb.py qe/04_bulk_neb/q+1/S1/neb_S1_qp1 --label "S1, +1" --out assets/neb_S1_qp1.png

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


def vasp_profile(folder):
    import os
    from ase.io import read
    rows = [l.split() for l in open(os.path.join(folder, "neb_data.txt")) if l.strip() and not l.startswith("#")]
    names = [r[0] for r in rows]
    E = np.array([float(r[1]) for r in rows])
    F = np.array([float(r[2]) for r in rows])
    ims = []
    for n in names:
        c = os.path.join(folder, n, "CONTCAR")
        p = c if os.path.exists(c) and os.path.getsize(c) > 0 else os.path.join(folder, n, "POSCAR")
        if p.endswith("POSCAR") and n not in (names[0], names[-1]):
            print("warning: %s has no CONTCAR, using the start path" % n)
        ims.append(read(p, format="vasp"))
    x = [0.0]
    for a0, a1 in zip(ims[:-1], ims[1:]):
        df = a1.get_scaled_positions() - a0.get_scaled_positions()
        df -= np.round(df)
        x.append(x[-1] + np.linalg.norm(df @ a0.cell.array))
    x = np.array(x)
    e = E - E[0]
    xc, ec = [], []
    for k in range(len(x) - 1):
        h = x[k + 1] - x[k]
        t = np.linspace(0, 1, 40)
        h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
        xc += list(x[k] + t * h)
        ec += list(h00 * e[k] + h10 * h * (-F[k]) + h01 * e[k + 1] + h11 * h * (-F[k + 1]))
    return x, e, np.array(xc), np.array(ec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", nargs="?", help="QE: path to <prefix> (reads <prefix>.dat and <prefix>.int)")
    ap.add_argument("--vasp", help="VASP NEB folder holding neb_data.txt and 00 ... NN")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--path-length", type=float, default=None,
                    help="total path length in A (x axis in A instead of 0-1)")
    a = ap.parse_args()

    if a.vasp:
        xs, e, xc, ec = vasp_profile(a.vasp)
        xlab = "Reaction coordinate (Å)"
    else:
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
    span = xs[-1] - xs[0]
    # barrier label: try beside the arrow under the peak, then just outside the curve; keep the first
    # position whose text box misses the curve, the image markers and the frame
    xc_arr, ec_arr = np.asarray(xc), np.asarray(ec)
    w, h = 0.27 * span, 0.07 * e[k]              # approximate text box (data units)
    lo, hi = xs[0] - 0.03 * span, xs[-1] + 0.03 * span
    cands = []
    for frac in (0.3, 0.2, 0.45, 0.6, 0.75):
        y = frac * e[k]
        cands += [(y, xs[k] + 0.03 * span, True), (y, xs[k] - 0.03 * span, False)]
        r = xc_arr[(xc_arr > xs[k]) & (ec_arr <= y)]
        l = xc_arr[(xc_arr < xs[k]) & (ec_arr <= y)]
        if len(r):
            cands.append((y, r.min() + 0.03 * span, True))
        if len(l):
            cands.append((y, l.max() - 0.03 * span, False))
    choice = None
    for y, x, right in cands:
        x0, x1 = (x, x + w) if right else (x - w, x)
        if x0 < lo or x1 > hi:
            continue
        inbox = lambda X, Y: (X >= x0) & (X <= x1) & (np.abs(Y - y) < h)
        if not np.any(inbox(xc_arr, ec_arr)) and not np.any(inbox(np.asarray(xs), np.asarray(e))):
            choice = (y, x, right)
            break
    y, x, right = choice or (0.3 * e[k], xs[k] + 0.03 * span, True)
    ax.text(x, y, "%.3f eV" % e[k], va="center", ha="left" if right else "right", color=TXT)
    ax.axhline(0, color=MUT, lw=0.5, ls=(0, (3, 2)))
    ax.set_xlabel(xlab)
    ax.set_ylabel("Energy (eV)")
    ax.set_xlim(xs[0] - 0.03 * (xs[-1] - xs[0]), xs[-1] + 0.03 * (xs[-1] - xs[0]))
    ax.set_ylim(-0.04, max(e) * 1.25)
    ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2,
              handletextpad=0.3, columnspacing=1.2, borderaxespad=0.2)
    if a.label:
        ax.text(0.03, 0.95, a.label, transform=ax.transAxes, va="top", fontweight="semibold")
    fig.tight_layout(pad=0.3)
    fig.savefig(a.out, dpi=600, facecolor="white")
    print("barrier %.3f eV at image %d; written %s" % (e[k], k + 1, a.out))


if __name__ == "__main__":
    main()
