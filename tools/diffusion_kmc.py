#!/usr/bin/env python3
"""
Kinetic Monte Carlo check of tools/diffusion_tensor.py: independent vacancy walkers on the same
hop network and rates (residence-time algorithm), D_aa = <dx_a^2> / (2 t).
Usage: python3 tools/diffusion_kmc.py [--T 300] [--walkers 4000] [--steps 4000] [--seed 1]
"""
import argparse, os, sys
import numpy as np
from ase.io import read
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diffusion_tensor import hop_list, tensor, BARRIER, E_SITE, KB  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", default="vasp/01_unitcell/relax/CONTCAR")
    ap.add_argument("--T", type=float, default=300.0)
    ap.add_argument("--walkers", type=int, default=4000)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    stypes, hops = hop_list(read(a.unit, format="vasp"))
    n = len(stypes); E = np.array([E_SITE[t] for t in stypes])
    out = [[] for _ in range(n)]
    for i, j, r, lab in hops:
        if lab in BARRIER:
            g = 1e12 * np.exp(-(min(E[i], E[j]) + BARRIER[lab] - E[i]) / (KB * a.T))
            out[i].append((j, r, g))
    tot = np.array([sum(g for _, _, g in o) for o in out])
    cum = [np.cumsum([g for _, _, g in o]) / sum(g for _, _, g in o) for o in out]
    pi = np.exp(-E / (KB * a.T)); pi /= pi.sum()
    site = rng.choice(n, size=a.walkers, p=pi)
    x = np.zeros((a.walkers, 3)); t = np.zeros(a.walkers)
    for _ in range(a.steps):
        u1 = rng.random(a.walkers); u2 = rng.random(a.walkers)
        t += -np.log(u1) / tot[site]
        new = site.copy()
        for s in range(n):
            m = site == s
            if not m.any():
                continue
            k = np.searchsorted(cum[s], u2[m])
            x[m] += np.array([out[s][q][1] for q in k])
            new[m] = [out[s][q][0] for q in k]
        site = new
    # D = sum <dx^2> / (2 sum t): ratio of the means (unbiased for long walks); error by blocks
    Dk = (x ** 2).sum(axis=0) / (2 * t.sum())
    blk = np.array_split(np.arange(a.walkers), 20)
    Db = np.array([(x[b] ** 2).sum(axis=0) / (2 * t[b].sum()) for b in blk])
    err = Db.std(axis=0) / np.sqrt(len(blk))
    Dm = np.diag(tensor(stypes, hops, a.T, BARRIER)[0])
    print("T = %.0f K, %d walkers x %d hops" % (a.T, a.walkers, a.steps))
    for k, nm in enumerate("abc"):
        print("D_%s%s  KMC %.3e +- %.1e   master equation %.3e  (ratio %.3f)" %
              (nm, nm, Dk[k] * 1e-16, err[k] * 1e-16, Dm[k] * 1e-16, Dk[k] / Dm[k]))


if __name__ == "__main__":
    main()
