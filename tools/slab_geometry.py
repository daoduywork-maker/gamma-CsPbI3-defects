#!/usr/bin/env python3
"""
Layer-by-layer geometry of the CsI-terminated (001) slabs against the bulk (step 7 check).

    python3 tools/slab_geometry.py vasp/07_slab/L11/CONTCAR [more CONTCARs ...]
                                   [--bulk vasp/01_unitcell/relax/CONTCAR]

Prints, for every layer from the surface inwards: Pb-I bond range and equatorial
Pb-I-Pb angle (PbI2 layers), apical Pb-I-Pb angle (CsI layers), and the spacing
between neighbouring PbI2 layers; the bulk values first for comparison.
"""
import argparse

import numpy as np
from ase.io import read
from ase.neighborlist import neighbor_list


def bonds_angles(at):
    sym = np.array(at.get_chemical_symbols())
    i, j, d, D = neighbor_list("ijdD", at, 3.6)
    pbI = [(a, b, dd, DD) for a, b, dd, DD in zip(i, j, d, D) if sym[a] == "Pb" and sym[b] == "I"]
    nb = {}
    for a, b, dd, DD in pbI:
        nb.setdefault(b, []).append(-DD)
    ang = {I: np.degrees(np.arccos(np.dot(v[0], v[1]) / np.linalg.norm(v[0]) / np.linalg.norm(v[1])))
           for I, v in nb.items() if len(v) == 2}
    return sym, pbI, ang


def layers(at, sym):
    z = at.positions[:, 2]
    out = []
    for el, lab in (("Pb", "PbI2"), ("Cs", "CsI")):
        zz = np.sort(z[sym == el])
        g = [[zz[0]]]
        for v in zz[1:]:
            (g[-1].append(v) if v - g[-1][-1] < 1.0 else g.append([v]))
        out += [(np.mean(x), lab) for x in g]
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slabs", nargs="+")
    ap.add_argument("--bulk", default="vasp/01_unitcell/relax/CONTCAR")
    a = ap.parse_args()
    u = read(a.bulk)
    sym, pbI, ang = bonds_angles(u)
    c = u.cell[2, 2]
    z = u.positions[:, 2]
    ap_ = [v for I, v in ang.items() if abs(((z[I] / c) % 0.5) - 0.25) < 0.1]
    eq_ = [v for I, v in ang.items() if abs(((z[I] / c) % 0.5) - 0.25) >= 0.1]
    bl = [dd for *_, dd, _ in pbI]
    print("bulk: Pb-I %.3f-%.3f A, equatorial %.2f deg, apical %.2f deg, PbI2 spacing %.3f A"
          % (min(bl), max(bl), np.mean(eq_), np.mean(ap_), c / 2))
    for p in a.slabs:
        s = read(p)
        sym, pbI, ang = bonds_angles(s)
        z = s.positions[:, 2]
        lay = layers(s, sym)
        top = lay[0][0]
        half = len(lay) // 2
        print("== %s (%d layers)" % (p, len(lay)))
        prev = None
        for k, (zl, lab) in enumerate(lay[:half + 1]):
            I_here = [I for I in ang if abs(z[I] - zl) < 1.0]
            if lab == "PbI2":
                pbs = [m for m in range(len(s)) if sym[m] == "Pb" and abs(z[m] - zl) < 1.0]
                b = [dd for aa, bb, dd, _ in pbI if aa in pbs]
                sp = "" if prev is None else "  spacing %.3f" % (zl - prev)
                prev = zl
                print("  layer %2d PbI2 depth %5.2f A  Pb-I %.3f-%.3f  equatorial %.2f%s"
                      % (k + 1, zl - top, min(b), max(b), np.mean([ang[I] for I in I_here]), sp))
            else:
                txt = "%.2f" % np.mean([ang[I] for I in I_here]) if I_here else "surface"
                print("  layer %2d CsI  depth %5.2f A  apical %s" % (k + 1, zl - top, txt))


if __name__ == "__main__":
    main()
