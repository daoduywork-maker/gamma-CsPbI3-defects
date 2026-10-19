#!/usr/bin/env python3
"""
Hop network of the iodine vacancy in the perfect gamma-CsPbI3 supercell.

For a vacancy on a 4c (apical) or 8d (equatorial) site, counts how many
neighbouring iodine sites it can reach with each hop (S1-S6, L1-L4), and
gives each hop's displacement along a, b and c. Uses the hop definitions
and site classification of build_neb.py, so the labels match the NEB inputs.

Why: transport depends on how many hops of each kind there are and which
directions they open, not only on the lowest barrier. This table is the
input for a later kinetic Monte Carlo or analytic diffusion estimate.

Usage (from the project root):
    python3 04_bulk_neb/hop_network.py [--pristine 02_pristine/relax.in] [--out 04_bulk_neb/hop_network.txt]

Needs: python3 with numpy, ase and spglib (via build_neb.py).
"""

import argparse
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from ase.io import read

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_neb import HOPS, PAIR_CUT, frac_mic, label_pair, site_types  # noqa: E402

SAME_LAYER_TOL = 1.5  # A; |dc| below this stays in one layer (tilt buckles a layer by about 1 A)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pristine", default="02_pristine/relax.in")
    ap.add_argument("--out", default="04_bulk_neb/hop_network.txt")
    a = ap.parse_args()

    perfect = read(a.pristine, format="espresso-in")
    types = site_types(perfect)
    iod = sorted(types)
    cell = perfect.cell.array
    fp = perfect.get_scaled_positions()

    counts = {}                       # site -> Counter(label)
    disp = defaultdict(list)          # label -> list of |da|, |db|, |dc| (A)
    unlabeled = 0
    for i in iod:
        c = Counter()
        for j in iod:
            if j == i:
                continue
            d = frac_mic(fp[j] - fp[i]) @ cell
            r = np.linalg.norm(d)
            if r > PAIR_CUT:
                continue
            lab = label_pair(types, i, j, r)
            if lab is None:
                unlabeled += 1
                continue
            c[lab] += 1
            # cell vectors of this orthorhombic cell are along x, y, z
            disp[lab].append(np.abs(d))
        counts[i] = c

    # every site of one type must see the same hops (one Wyckoff orbit each)
    per_type = {}
    for t in ("8d", "4c"):
        sites = [i for i in iod if types[i] == t]
        first = counts[sites[0]]
        bad = [i for i in sites if counts[i] != first]
        if bad:
            sys.exit(f"{t} sites do not all see the same hops (e.g. atom {bad[0]}); check the hop table")
        per_type[t] = first

    lines = []
    n8, n4 = sum(1 for t in types.values() if t == "8d"), sum(1 for t in types.values() if t == "4c")
    lines.append(f"Perfect supercell: {a.pristine}, {len(iod)} iodine sites ({n8} 8d, {n4} 4c)")
    lines.append("Hops available to ONE vacancy, by its site type, and the hop displacement (A)\n")
    lines.append(f"{'hop':4} {'ends':7} {'length':>6}  {'from 8d':>7} {'from 4c':>7}  {'|da|':>5} {'|db|':>5} {'|dc|':>5}  direction")
    for lab, (t1, t2, L) in HOPS.items():
        m = np.mean(disp[lab], axis=0) if disp[lab] else np.zeros(3)
        if m[2] < SAME_LAYER_TOL:
            direction = "within one layer"
        elif {t1, t2} == {"4c", "8d"}:
            direction = "PbI2 layer <-> CsI layer"
        else:
            direction = "across a layer, along c"
        lines.append(f"{lab:4} {t1+'-'+t2:7} {L:6.2f}  {per_type['8d'][lab]:7d} {per_type['4c'][lab]:7d}  "
                     f"{m[0]:5.2f} {m[1]:5.2f} {m[2]:5.2f}  {direction}")
    tot8, tot4 = sum(per_type["8d"].values()), sum(per_type["4c"].values())
    lines.append(f"{'total':20} {tot8:7d} {tot4:7d}")
    lines.append("")
    lines.append("8d sites lie in the PbI2 layers, 4c sites in the CsI layers. Moving the vacancy")
    lines.append("along c needs 4c-8d hops (8d -> 4c -> 8d) or the long L2; within the ab plane,")
    lines.append("8d-8d hops (S1, S6, L1) and L3 between 4c sites are enough.")
    lines.append("")
    lines.append("Checks: every 4c-8d hop must appear twice as often from 4c as from 8d "
                 f"(there are {n8 // max(n4, 1)}x more 8d sites).")
    for lab, (t1, t2, _) in HOPS.items():
        if {t1, t2} == {"4c", "8d"}:
            ok = per_type["4c"][lab] * n4 == per_type["8d"][lab] * n8
            lines.append(f"  {lab}: {per_type['8d'][lab]} x {n8} = {per_type['4c'][lab]} x {n4}  {'ok' if ok else 'MISMATCH'}")
    if unlabeled:
        lines.append(f"Note: {unlabeled} I-I pairs within {PAIR_CUT} A matched no hop label (counted twice).")
    text = "\n".join(lines)
    print(text)
    with open(a.out, "w") as f:
        f.write(text + "\n")
    print(f"\nwritten: {a.out}")


if __name__ == "__main__":
    main()
