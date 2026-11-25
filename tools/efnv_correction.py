#!/usr/bin/env python3
"""
Extended FNV (Kumagai & Oba, PRB 89, 195205, 2014) finite-size correction for V_I+ in gamma-CsPbI3,
from the atomic-site potentials in the VASP OUTCARs (no LOCPOT needed).

    E_corr = E_lat + q * < dV_site + phi_PC(site) >_far ,   E_lat = -E_PC

E_PC        point-charge lattice energy in the anisotropic dielectric (Ewald sum, with background), < 0;
            the correction E_lat = -E_PC removes it
dV_site     V_core(defect) - V_core(perfect) at every atom, as printed by VASP. VASP prints the potential
            energy of an electron: dV_site against phi_PC has slope -1.09 at r > 3.5 A (checked 25 Nov),
            so the electron-energy alignment is < dV_site - (-phi_PC) >_far
phi_PC      electrostatic potential of the periodic point charge (+ background) at that atom
<...>_far   average over atoms outside the sphere inscribed in the Wigner-Seitz cell around the defect

Inputs per strain (vasp/08_fnv/eps<e>/): {perfect,vac}/CONTCAR and core_pot.txt (core potentials,
last ionic step); dielectric tensor = electronic + ionic from vasp/dielectric.txt (DFPT).
Formation energies use vasp/06_strain/super/ef_strain.txt (dE, VBM) with the old alignment and
0.06 eV estimate replaced by E_corr. Output: vasp/08_fnv/efnv.txt
"""
import os, re, itertools
import numpy as np
from ase.io import read
from scipy.special import erfc

K = 14.399645          # e^2 / (4 pi eps0) in eV*A
MU_I0 = -7.02297865 / 4
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "vasp")


def dielectric():
    blocks, cur = [], []
    for line in open(os.path.join(V, "dielectric.txt")):
        p = line.split()
        if len(p) == 3:
            try:
                cur.append([float(x) for x in p])
            except ValueError:
                pass
        if len(cur) == 3:
            blocks.append(np.array(cur)); cur = []
    return blocks[0] + blocks[-1]          # electronic (with local fields) + ionic


def core(path):
    v = {}
    for line in open(path):
        p = line.split()
        for i in range(0, len(p) - 1, 2):
            v[int(p[i]) - 1] = float(p[i + 1])
    return np.array([v[i] for i in range(len(v))])


class Ewald:
    def __init__(self, cell, eps, gamma=None, nr=4, ng=8):
        self.A = cell; self.eps = eps; self.ie = np.linalg.inv(eps); self.de = np.sqrt(np.linalg.det(eps))
        self.V = abs(np.linalg.det(cell)); self.B = 2 * np.pi * np.linalg.inv(cell).T
        self.g = gamma or 2.0 / self.V ** (1 / 3)
        rng = lambda n: range(-n, n + 1)
        self.R = np.array([np.array(n) @ cell for n in itertools.product(rng(nr), rng(nr), rng(nr))])
        G = np.array([np.array(n) @ self.B for n in itertools.product(rng(ng), rng(ng), rng(ng)) if any(n)])
        gEg = np.einsum("ij,jk,ik->i", G, eps, G)
        self.G, self.wG = G, np.exp(-gEg / (4 * self.g ** 2)) / gEg

    def _dist(self, X):
        return np.sqrt(np.einsum("ij,jk,ik->i", X, self.ie, X))

    def phi(self, r):
        """potential (V per unit charge, times K) of a unit point charge at 0 plus background, at r"""
        d = self._dist(self.R + r)
        real = np.sum(erfc(self.g * d) / d) / self.de
        recip = 4 * np.pi / self.V * np.sum(self.wG * np.cos(self.G @ r))
        return K * (real + recip - np.pi / (self.V * self.g ** 2))

    def energy(self, q=1.0):
        R = self.R[np.linalg.norm(self.R, axis=1) > 1e-8]
        d = self._dist(R)
        real = np.sum(erfc(self.g * d) / d) / self.de
        recip = 4 * np.pi / self.V * np.sum(self.wG)
        return 0.5 * q * q * K * (real + recip - 2 * self.g / (np.sqrt(np.pi) * self.de) - np.pi / (self.V * self.g ** 2))


def selftest():
    L, e = 10.0, 1.0
    E = Ewald(np.eye(3) * L, np.eye(3) * e).energy()
    madelung = 2.837297
    print("self-test, simple cubic: E_PC = %.5f eV, expected %.5f eV" % (E, -K * madelung / (2 * e * L)))


def correction(e_str):
    d = os.path.join(V, "08_fnv", e_str)
    perf, vac = read(os.path.join(d, "perfect", "CONTCAR"), format="vasp"), read(os.path.join(d, "vac", "CONTCAR"), format="vasp")
    Vp, Vd = core(os.path.join(d, "perfect", "core_pot.txt")), core(os.path.join(d, "vac", "core_pot.txt"))
    cell = perf.cell.array
    fp, fd = perf.get_scaled_positions(), vac.get_scaled_positions()
    # map defect atoms to perfect sites; the unmatched perfect site is the vacancy
    used, idx = set(), []
    for k, f in enumerate(fd):
        dd = fp - f; dd -= np.round(dd)
        dist = np.linalg.norm(dd @ cell, axis=1)
        dist[[i for i in used]] = 1e9
        dist[[i for i, s in enumerate(perf.get_chemical_symbols()) if s != vac[k].symbol]] = 1e9
        j = int(np.argmin(dist)); used.add(j); idx.append(j)
    vsite = [i for i in range(len(perf)) if i not in used]
    assert len(vsite) == 1
    r0 = fp[vsite[0]]
    eps = dielectric()
    ew = Ewald(cell, eps)
    Rws = 0.5 * min(np.linalg.norm(cell, axis=1))
    rows = []
    for k, j in enumerate(idx):
        dr = fd[k] - r0; dr -= np.round(dr); r = dr @ cell
        dist = np.linalg.norm(r)
        rows.append((dist, Vd[k] - Vp[j], ew.phi(r)))
    rows = np.array(rows)
    far = rows[:, 0] > Rws
    q = 1.0
    E_pc = ew.energy(q)
    align = np.mean(rows[far, 1] + q * rows[far, 2])
    E_lat = -E_pc
    return E_lat, align, E_lat + q * align, int(far.sum()), Rws, eps


def main():
    selftest()
    ef = {}
    for line in open(os.path.join(V, "06_strain", "super", "ef_strain.txt")):
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        e, d4, d8, vbm, dv, site = float(p[0]), float(p[1]), float(p[2]), float(p[3]), float(p[4]), p[5]
        ef[e] = (d4 if site == "4c" else d8, vbm, dv, site)
    out = ["# eFNV (Kumagai-Oba) correction for V_I+, q = +1; dielectric tensor (electronic + ionic):"]
    first = True
    for e in (-1.0, -0.5, 0.0, 0.5, 1.0):
        E_pc, al, Ec, nfar, Rws, eps = correction("eps%+.1f" % e)
        if first:
            out.append("#   diag = %.3f %.3f %.3f" % tuple(np.diag(eps)))
            out.append("# eps(%)  E_lat(eV)  q*align(eV)  E_corr(eV)  n_far  R_ws(A)  E_f_old  E_f_eFNV  (I-rich, E_F at VBM, lower site)")
            first = False
        dE, vbm, dv, site = ef[e]
        old = dE + MU_I0 + vbm + dv + 0.06
        new = dE + MU_I0 + vbm + Ec
        out.append("%+5.1f   %.4f    %+.4f      %.4f     %3d    %.2f     %.3f    %.3f" % (e, E_pc, al, Ec, nfar, Rws, old, new))
    txt = "\n".join(out) + "\n"
    open(os.path.join(V, "08_fnv", "efnv.txt"), "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
