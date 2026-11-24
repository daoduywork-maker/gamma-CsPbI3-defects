#!/usr/bin/env python3
"""
Vacancy diffusivity tensor of V_I+ at -1, 0 and +1% biaxial strain (step 9, strained).

Same master-equation method as tools/diffusion_tensor.py. The hop network is taken from the
unstrained unit cell (hop labels need the unstrained lengths) and every hop vector is scaled
by the strained lattice: x, y by (1 + eps), z by c(eps)/c(0) from vasp/06_strain/unit/fit.txt.
Barriers of S1, S2, S4, S5 from the strained CI-NEBs (measured from the lower end, 8d at +-1%);
S3, S6 and L3 kept at the unstrained values. Site energies E(8d) - E(4c) from the strained
supercells. Output: vasp/06_strain/neb/diffusion_tensor_strain.txt
"""
import os, sys
import numpy as np
from ase.io import read
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import diffusion_tensor as dt

C = {-1.0: 12.4648, 0.0: 12.3877, 1.0: 12.3143}          # fitted c (A), vasp/06_strain/unit/fit.txt
DSITE = {-1.0: -0.0043, 0.0: 0.00086, 1.0: -0.0065}      # E(8d) - E(4c) (eV), strained supercells
BAR = {
    -1.0: dict(dt.BARRIER, S2=0.332, S4=0.332, S1=0.349, S5=0.367),
     0.0: dict(dt.BARRIER),
     1.0: dict(dt.BARRIER, S2=0.316, S4=0.308, S1=0.330, S5=0.329),
}
T = 300.0
unit = read("vasp/01_unitcell/relax/CONTCAR", format="vasp")
stypes, hops0 = dt.hop_list(unit)
rows = ["# V_I+ vacancy diffusivity at %.0f K (cm^2/s), nu = 1e12 Hz; strained hop vectors and barriers" % T,
        "# eps(%)   D_aa        D_bb        D_cc       D_cc/D_aa  D_bb/D_aa  max|chk-D|/D"]
for e in (-1.0, 0.0, 1.0):
    s = np.array([1 + e / 100, 1 + e / 100, C[e] / C[0.0]])
    hops = [(i, j, r * s, lab) for i, j, r, lab in hops0]
    dt.E_SITE = {"4c": 0.0, "8d": DSITE[e]}
    D, chk, pi = dt.tensor(stypes, hops, T, BAR[e])
    d = np.diag(D) * 1e-16
    err = np.max(np.abs(chk - np.diag(D)) / np.diag(D))
    rows.append("%+5.1f   %.3e  %.3e  %.3e   %.2f       %.2f       %.1e" % (e, d[0], d[1], d[2], d[2] / d[0], d[1] / d[0], err))
out = "vasp/06_strain/neb/diffusion_tensor_strain.txt"
open(out, "w").write("\n".join(rows) + "\n")
print("\n".join(rows))
