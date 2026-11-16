#!/usr/bin/env python3
"""
Vacancy diffusion tensor of V_I+ in gamma-CsPbI3 from the hop barriers (step 9).

Method (master equation on the hop network, as Smolders et al. 2024):
  every iodine site of the relaxed unit cell and every hop i -> j (+ lattice vector) up to
  6.1 A is listed and labelled S1-S6, L1-L4 by its ends (4c/8d) and length. A hop has the
  rate Gamma = nu exp(-(E_TS - E_i)/kT), with the saddle energy E_TS = E(lower end) + Ea.
  The long-time spreading of the occupation follows from the k-dependent rate matrix W(k):
  its eigenvalue closest to zero is lambda(k) = -k.D.k for small k. Second-order
  perturbation theory in k gives, with pi the equilibrium site occupations,
      D_ab = 1/2 sum_i pi_i sum_j Gamma_ij r_a r_b  -  sym[ u B_a W0^+ B_b pi ],
  where B_a holds Gamma_ij r_a. The second term is the correction for a lattice with more
  than one kind of site; it vanishes for one site per cell. A direct eigenvalue at small k
  checks the result.

This is the vacancy diffusivity. The iodide diffusivity is D_I = x_v f D_v (x_v vacancy site
fraction from the formation energy, f correlation factor), left for later.

Prefactor nu = 1e12 Hz until the Vineyard prefactors are computed.

Usage: python3 tools/diffusion_tensor.py [--T 300] [--unit vasp/01_unitcell/relax/CONTCAR]
"""
import argparse
import os
import sys

import numpy as np
from ase.io import read

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_neb import HOPS, VASP_LEN, LEN_TOL, PAIR_CUT, site_types  # noqa: E402

KB = 8.617333262e-5  # eV/K
# +1 barriers (eV), VASP PBEsol CI-NEB; for a 4c-8d hop measured from the lower end (4c)
BARRIER = {"S1": 0.345, "S2": 0.326, "S3": 0.462, "S4": 0.326, "S5": 0.348, "S6": 0.434, "L3": 0.777}
E_SITE = {"4c": 0.0, "8d": 0.00086}  # eV, E(8d) - E(4c) = +0.9 meV (+1, 159-atom cells)


def hop_list(unit):
    types = site_types(unit)
    I = [a.index for a in unit if a.symbol == "I"]
    cell = unit.cell.array
    pos = unit.positions
    hops = []
    R = range(-2, 3)
    for i in I:
        for j in I:
            for n in [(x, y, z) for x in R for y in R for z in R]:
                r = pos[j] + np.array(n) @ cell - pos[i]
                d = np.linalg.norm(r)
                if d < 0.5 or d > PAIR_CUT:
                    continue
                lab = None
                for h, (t1, t2, _) in HOPS.items():
                    if sorted((types[i], types[j])) == sorted((t1, t2)) and abs(d - VASP_LEN[h]) < LEN_TOL:
                        lab = h
                if lab:
                    hops.append((I.index(i), I.index(j), r, lab))
    return [types[i] for i in I], hops


def tensor(stypes, hops, T, barrier, nu=1e12):
    n = len(stypes)
    E = np.array([E_SITE[t] for t in stypes])
    pi = np.exp(-E / (KB * T)); pi /= pi.sum()
    W0 = np.zeros((n, n)); B = np.zeros((3, n, n)); C = np.zeros((3, 3, n, n))
    for i, j, r, lab in hops:
        if lab not in barrier:
            continue
        ets = min(E[i], E[j]) + barrier[lab]
        g = nu * np.exp(-(ets - E[i]) / (KB * T))
        W0[j, i] += g; W0[i, i] -= g
        B[:, j, i] += g * r
        C[:, :, j, i] += g * np.outer(r, r)
    u = np.ones(n)
    Wp = np.linalg.pinv(W0)
    D = np.zeros((3, 3))
    for a in range(3):
        for b in range(3):
            D[a, b] = 0.5 * u @ C[a, b] @ pi - 0.5 * (u @ B[a] @ Wp @ B[b] @ pi + u @ B[b] @ Wp @ B[a] @ pi)
    # check: eigenvalue of W(k) closest to zero, k along each axis
    chk = []
    for a in range(3):
        k = np.zeros(3); k[a] = 2e-3
        Wk = np.zeros((n, n), complex)
        for i, j, r, lab in hops:
            if lab not in barrier:
                continue
            ets = min(E[i], E[j]) + barrier[lab]
            g = nu * np.exp(-(ets - E[i]) / (KB * T))
            Wk[j, i] += g * np.exp(-1j * k @ r); Wk[i, i] -= g
        lam = np.linalg.eigvals(Wk)
        chk.append(-lam[np.argmax(lam.real)].real / k[a] ** 2)
    return D, np.array(chk), pi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", default="vasp/01_unitcell/relax/CONTCAR")
    ap.add_argument("--T", type=float, default=300.0)
    ap.add_argument("--out", default="vasp/04_bulk_neb/diffusion_tensor.txt")
    a = ap.parse_args()
    unit = read(a.unit, format="vasp")
    stypes, hops = hop_list(unit)
    rep = ["Vacancy (V_I+) diffusion tensor, master equation on the hop network",
           "unit cell %s: %d iodine sites (%d 4c, %d 8d), axes a, b, c = x, y, z" %
           (a.unit, len(stypes), stypes.count("4c"), stypes.count("8d")), ""]
    for t in ("4c", "8d"):
        idx = [k for k, s in enumerate(stypes) if s == t]
        cnt = {}
        for i, j, r, lab in hops:
            if i == idx[0]:
                cnt[lab] = cnt.get(lab, 0) + 1
        rep.append("hops from one %s site: %s" % (t, ", ".join("%s %d" % kv for kv in sorted(cnt.items()))))
    rep += ["", "barriers (eV): " + ", ".join("%s %.3f" % kv for kv in BARRIER.items()),
            "missing hops (L1, L2, L4) left out; nu = 1e12 Hz; E(8d) - E(4c) = +0.86 meV", ""]
    D, chk, pi = tensor(stypes, hops, a.T, BARRIER)
    cm = 1e-16
    rep.append("T = %.0f K, D_v (cm^2/s):" % a.T)
    for r_ in D * cm:
        rep.append("   " + "  ".join("%10.3e" % x for x in r_))
    rep.append("check, eigenvalue at small k (diagonal): " + "  ".join("%10.3e" % x for x in chk * cm))
    rep.append("anisotropy: D_aa : D_bb : D_cc = 1 : %.2f : %.2f" % (D[1, 1] / D[0, 0], D[2, 2] / D[0, 0]))
    # Arrhenius fit 250-400 K, and sensitivity tests
    Ts = np.linspace(250, 400, 7)
    for ax, nm in ((0, "a"), (1, "b"), (2, "c")):
        y = [np.log(tensor(stypes, hops, t, BARRIER)[0][ax, ax]) for t in Ts]
        Ea = -np.polyfit(1 / (KB * Ts), y, 1)[0]
        rep.append("effective activation energy along %s (250-400 K): %.3f eV" % (nm, Ea))
    rep.append("")
    rep.append("Sensitivity at %.0f K (ratio to the result above, diagonal a, b, c):" % a.T)
    tests = {"L1, L2, L4 added at 0.60 eV": dict(BARRIER, L1=0.60, L2=0.60, L4=0.60),
             "only S1, S2, S4, S5 (fast hops)": {k: BARRIER[k] for k in ("S1", "S2", "S4", "S5")},
             "S2 and S4 +0.02 eV": dict(BARRIER, S2=0.346, S4=0.346)}
    for name, bar in tests.items():
        Dt = tensor(stypes, hops, a.T, bar)[0]
        rep.append("  %-34s %.2f  %.2f  %.2f" % (name, *(np.diag(Dt) / np.diag(D))))
    txt = "\n".join(rep) + "\n"
    open(a.out, "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
