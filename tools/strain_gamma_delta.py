#!/usr/bin/env python3
"""
gamma-delta energy against biaxial strain (step 6), from the E(x) scans.

gamma: vasp/06_strain/unit/energies.txt  (eps dc E conv), cubic fit of E(c) per eps
delta: vasp/06_strain/delta/energies_delta.txt  (plane eps dx E conv), cubic fit of E(x)
       per plane and eps; the plane is the strained plane (ab, ac, bc), x the free axis.
Both cells hold 4 formula units. Two limits:
  coherent   dE(eps) = [E_gamma(eps) - min_plane E_delta(eps)] / 4   (delta strained too)
  incoherent dE(eps) = [E_gamma(eps) - E_delta(0)] / 4               (delta grains relaxed)
Positive dE = gamma above delta. Writes vasp/06_strain/gamma_delta.txt and
assets/strain_gamma_delta.png.
"""
import collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

FONT = "Inter" if any(f.name == "Inter" for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 9, "axes.linewidth": 0.6,
                     "xtick.direction": "in", "ytick.direction": "in"})
CM = 1 / 2.54
TXT, MUT, OR, PU = "#0B0B0B", "#52514E", "#D85A30", "#7F77DD"


def emin(xs, es):
    xs, es = np.array(xs), np.array(es)
    p = np.polyfit(xs, es, 3 if len(xs) >= 5 else 2)
    g = np.linspace(xs.min(), xs.max(), 4001)
    v = np.polyval(p, g)
    k = v.argmin()
    return g[k], v[k]


def main():
    G = collections.defaultdict(list)
    for l in open("vasp/06_strain/unit/energies.txt"):
        e, dc, E, ok = l.split()
        if ok == "1":
            G[float(e)].append((float(dc), float(E)))
    D = collections.defaultdict(list)
    for l in open("vasp/06_strain/delta/energies_delta.txt"):
        p, e, dx, E, ok = l.split()
        if ok == "1":
            D[(p, float(e))].append((float(dx), float(E)))
    eps = sorted(G)
    Eg = {e: emin(*zip(*G[e]))[1] for e in eps}
    Ed = {k: emin(*zip(*v)) for k, v in D.items()}
    planes = ("ab", "ac", "bc")
    Ed0 = min(Ed[(p, 0.0)][1] for p in planes)
    rows = ["gamma-delta energy against biaxial strain (meV per formula unit; positive = gamma above delta)",
            "", "eps(%)  E_gamma-E_gamma(0)  dE_delta(ab)  dE_delta(ac)  dE_delta(bc)   coherent  incoherent  lowest-delta plane"]
    coh, inc, per = [], [], {p: [] for p in planes}
    for e in eps:
        dg = (Eg[e] - Eg[0.0]) / 4 * 1000
        dd = {p: (Ed[(p, e)][1] - Ed0) / 4 * 1000 for p in planes}
        best = min(planes, key=lambda p: Ed[(p, e)][1])
        c = (Eg[e] - Ed[(best, e)][1]) / 4 * 1000
        i = (Eg[e] - Ed0) / 4 * 1000
        coh.append(c); inc.append(i)
        for p in planes:
            per[p].append((Eg[e] - Ed[(p, e)][1]) / 4 * 1000)
        rows.append("%+5.1f   %10.2f        %8.2f      %8.2f      %8.2f      %8.2f   %8.2f     %s"
                    % (e, dg, dd["ab"], dd["ac"], dd["bc"], c, i, best))
    rows += ["", "dx* of delta (%% on the free axis): " + "; ".join(
        "%s %+.1f%%: %+.2f" % (p, e, Ed[(p, e)][0]) for p in planes for e in eps if e in (-1.0, 1.0))]
    txt = "\n".join(rows) + "\n"
    open("vasp/06_strain/gamma_delta.txt", "w").write(txt)
    print(txt)
    fig, ax = plt.subplots(figsize=(8.5 * CM, 6.5 * CM))
    for p, ls in zip(planes, (":", "-.", (0, (5, 2)))):
        ax.plot(eps, per[p], color=MUT, lw=0.8, ls=ls, label=r"coherent, $\delta$ %s plane" % p)
    ax.plot(eps, inc, "s-", color=OR, ms=4, lw=1.4, label=r"incoherent ($\delta$ relaxed)")
    ax.plot(eps, coh, "o-", color=PU, ms=4, lw=1.4, label=r"coherent, most stable $\delta$")
    ax.set_xlabel(r"Biaxial strain $\varepsilon$ (%)")
    ax.set_ylabel(r"$E_\gamma - E_\delta$ (meV per f.u.)")
    ax.legend(frameon=False, fontsize=6.5, loc="best")
    fig.tight_layout(pad=0.3)
    fig.savefig("assets/strain_gamma_delta.png", dpi=600, facecolor="white")


if __name__ == "__main__":
    main()
