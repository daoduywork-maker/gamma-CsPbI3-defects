#!/usr/bin/env python3
"""
Build Quantum ESPRESSO NEB inputs (neb.x) for iodine-vacancy hops in gamma-CsPbI3.

One run builds one hop (S1-S6, L1-L4) in one charge state:

  1. Reads the perfect 2x2x2 supercell and the relaxed vacancy cells
     (apical 4c and equatorial 8d) of that charge state.
  2. Picks a neighbour j of the vacancy whose pair matches the hop label
     (site types and length, see HOPS below).
  3. Makes the relaxed end point by symmetry: an operation g of the perfect
     supercell that carries a relaxed vacancy onto site j. No new relaxation.
  4. Renumbers the atoms so atom k is on the same site in both end points,
     except the hopping iodine (site j -> the starting vacancy site).
  5. Builds the intermediate images with IDPP (ASE) and checks the closest
     approach of any two atoms along the path.
  6. Writes neb.in, path.xyz (all images, for viewing) and report.txt.

Usage (from the project root):
    python3 04_bulk_neb/build_neb.py S1 --charge q+1
    python3 04_bulk_neb/build_neb.py S2 --charge q+1 --images 5 --from 8d

Expected relaxed structures (copied from the cluster):
    03_vacancies/<charge>/vac_I_equatorial/relax.out
    03_vacancies/<charge>/vac_I_apical/relax.out
Override with --eq and --ap (a relax.in also works, for testing).

Needs: python3 with numpy, scipy, ase and spglib.
"""

import argparse
import math
import os
import sys

import numpy as np
import spglib
from ase.io import read, write
from scipy.optimize import linear_sum_assignment

try:
    from ase.mep import NEB
except ImportError:            # older ASE
    from ase.neb import NEB

# ---- settings ----------------------------------------------------------------
# hop label: (site type at one end, site type at the other end, length in A,
# from the tight structure; see the README hop table)
HOPS = {
    "S1": ("8d", "8d", 4.41), "S2": ("4c", "8d", 4.43), "S3": ("4c", "8d", 4.45),
    "S4": ("4c", "8d", 4.53), "S5": ("4c", "8d", 4.56), "S6": ("8d", "8d", 4.60),
    "L1": ("8d", "8d", 4.80), "L2": ("8d", "8d", 5.18), "L3": ("4c", "4c", 5.28),
    "L4": ("4c", "8d", 5.93),
}
LEN_TOL = 0.015         # A, match to the nominal length (lengths are 0.02 A apart at least)
PAIR_CUT = 6.1          # A, longest I-I pair considered
PB_I_CUT = 3.6          # A, Pb-I bond
MIN_DIST_WARN = 2.2     # A, flag any image with two atoms closer than this (I passing an edge comes to about 2.3 A of Pb before NEB relaxes it)
SYMPREC = 1e-3          # A, spglib tolerance on the perfect supercell
MEM_PER_IMAGE_GB = {"q+1": 137, "q0": 193}   # QE estimates for one 159-atom cell
USABLE_GB_PER_NODE = 75                     # of 92 GB on a std40 node
PATH_SETTINGS = """&PATH
  string_method = 'neb'
  restart_mode  = 'from_scratch'
  nstep_path    = 200
  num_of_images = {nimg}
  opt_scheme    = 'broyden'
  CI_scheme     = 'auto'
  k_max         = 0.3D0
  k_min         = 0.2D0
  path_thr      = 0.05D0
/"""
DROP_CONTROL = ("calculation", "etot_conv_thr", "forc_conv_thr", "nstep", "tstress", "tprnfor")
# ------------------------------------------------------------------------------


def frac_mic(d):
    return d - np.round(d)


def site_types(atoms):
    """'4c' (apical: Pb-I-Pb along c) or '8d' (equatorial) for every iodine."""
    types = {}
    pb = [a.index for a in atoms if a.symbol == "Pb"]
    for i in [a.index for a in atoms if a.symbol == "I"]:
        d = atoms.get_distances(i, pb, mic=True, vector=True)
        near = [v for v, n in zip(d, np.linalg.norm(d, axis=1)) if n < PB_I_CUT]
        if len(near) != 2:
            sys.exit(f"iodine {i} has {len(near)} Pb neighbours, expected 2")
        link = near[0] - near[1]                     # Pb-Pb vector through this iodine
        types[i] = "4c" if abs(link[2]) > 0.8 * np.linalg.norm(link) else "8d"
    return types


def label_pair(types, i, j, dist):
    for lab, (t1, t2, L) in HOPS.items():
        if sorted((types[i], types[j])) == sorted((t1, t2)) and abs(dist - L) < LEN_TOL:
            return lab
    return None


def map_to_sites(perfect, struct):
    """Site index (in the perfect cell) of every atom of struct, and the empty site."""
    fp, fs = perfect.get_scaled_positions(), struct.get_scaled_positions()
    cell = perfect.cell.array
    cost = np.full((len(fs), len(fp)), 1e6)
    for k, (f, s) in enumerate(zip(fs, struct.get_chemical_symbols())):
        same = np.array([p == s for p in perfect.get_chemical_symbols()])
        d = np.linalg.norm(frac_mic(fp - f) @ cell, axis=1)
        cost[k, same] = d[same]
    rows, cols = linear_sum_assignment(cost)
    worst = cost[rows, cols].max()
    if worst > 1.5:
        sys.exit(f"an atom is {worst:.2f} A from its site; structure does not match the perfect cell")
    site_of = np.empty(len(fs), dtype=int)
    site_of[rows] = cols
    empty = sorted(set(range(len(fp))) - set(cols))
    if len(empty) != 1:
        sys.exit(f"expected one empty site, found {len(empty)}")
    return site_of, empty[0], worst


def symmetry_ops(perfect):
    """Operations (R, t) of the perfect supercell with the site permutation of each."""
    cell = (perfect.cell.array, perfect.get_scaled_positions(), perfect.get_atomic_numbers())
    ds = spglib.get_symmetry_dataset(cell, symprec=SYMPREC)
    sg = ds.international if hasattr(ds, "international") else ds["international"]
    rots = ds.rotations if hasattr(ds, "rotations") else ds["rotations"]
    trans = ds.translations if hasattr(ds, "translations") else ds["translations"]
    fp, Z, lat = perfect.get_scaled_positions(), perfect.get_atomic_numbers(), perfect.cell.array
    ops = []
    for R, t in zip(rots, trans):
        new = fp @ R.T + t
        perm = np.empty(len(fp), dtype=int)
        for s, f in enumerate(new):
            d = np.linalg.norm(frac_mic(fp - f) @ lat, axis=1)
            d[Z != Z[s]] = 1e6
            perm[s] = int(np.argmin(d))
            if d[perm[s]] > 0.01:
                sys.exit("symmetry operation does not map the perfect cell onto itself")
        ops.append((R, t, perm))
    return sg, ops


def endpoint_by_symmetry(perfect, ops, template, target):
    """Positions (fractional, by site) of the relaxed vacancy moved onto site `target`."""
    site_of, r0, _ = map_to_sites(perfect, template)
    cands = [op for op in ops if op[2][r0] == target]
    if not cands:
        sys.exit(f"no symmetry operation takes site {r0} to site {target}")
    cands.sort(key=lambda op: (not np.allclose(op[0], np.eye(3)), np.abs(op[1]).sum()))
    R, t, perm = cands[0]
    fpos = {}
    for f, s in zip(template.get_scaled_positions(), site_of):
        fpos[perm[s]] = f @ R.T + t
    return fpos, R, t


def unwrap_to(f, ref):
    return ref + frac_mic(f - ref)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hop", choices=list(HOPS))
    ap.add_argument("--charge", default="q+1", choices=["q+1", "q0"])
    ap.add_argument("--images", type=int, default=5, help="intermediate images (default 5)")
    ap.add_argument("--from", dest="start", choices=["4c", "8d"],
                    help="starting site type for a 4c-8d hop (default 8d)")
    ap.add_argument("--pristine", default="02_pristine/relax.in")
    ap.add_argument("--eq", help="relaxed equatorial (8d) vacancy, relax.out or relax.in")
    ap.add_argument("--ap", help="relaxed apical (4c) vacancy, relax.out or relax.in")
    ap.add_argument("--out", default="04_bulk_neb")
    a = ap.parse_args()

    vdir = os.path.join("03_vacancies", a.charge)
    paths = {"8d": a.eq or os.path.join(vdir, "vac_I_equatorial", "relax.out"),
             "4c": a.ap or os.path.join(vdir, "vac_I_apical", "relax.out")}
    t1, t2, L = HOPS[a.hop]
    start = a.start or ("8d" if "8d" in (t1, t2) else "4c")
    if start not in (t1, t2):
        sys.exit(f"{a.hop} joins {t1} and {t2}; --from {start} does not apply")
    end = t2 if start == t1 else t1
    needed = sorted({start, end})
    for t in needed:
        if not os.path.exists(paths[t]):
            sys.exit(f"missing relaxed {t} vacancy: {paths[t]}")

    def load(p):
        return read(p, format="espresso-out", index=-1) if p.endswith(".out") else read(p, format="espresso-in")

    perfect = read(a.pristine, format="espresso-in")
    relaxed = {t: load(paths[t]) for t in needed}
    types = site_types(perfect)
    sg, ops = symmetry_ops(perfect)
    lat = perfect.cell.array
    fp = perfect.get_scaled_positions()

    # initial state: relaxed vacancy of the starting type, as found
    site_of, r, worst_init = map_to_sites(perfect, relaxed[start])
    if types[r] != start:
        sys.exit(f"the {start} file has its vacancy on a {types[r]} site")
    f_init = {s: unwrap_to(f, fp[s]) for f, s in zip(relaxed[start].get_scaled_positions(), site_of)}

    # neighbour j that makes this hop
    iod = [i for i in types if i != r]
    dvec = frac_mic(fp[iod] - fp[r]) @ lat
    dist = np.linalg.norm(dvec, axis=1)
    hits = [(d, j) for d, j in zip(dist, iod) if d < PAIR_CUT and label_pair(types, r, j, d) == a.hop]
    if not hits:
        sys.exit(f"no {a.hop} neighbour of site {r}")
    d_hop, j = min(hits, key=lambda x: (round(x[0], 3), x[1]))

    # final state: relaxed vacancy of the end type, carried onto site j
    f_end, R, t = endpoint_by_symmetry(perfect, ops, relaxed[end], j)
    f_end = {s: unwrap_to(f, fp[s]) for s, f in f_end.items()}

    # atom list: every occupied site of the initial state, in perfect-cell order
    order = [s for s in range(len(perfect)) if s != r]
    sym = perfect.get_chemical_symbols()
    ini_f = np.array([f_init[s] for s in order])
    fin_f = np.array([f_end[r] if s == j else f_end[s] for s in order])
    fin_f = np.array([unwrap_to(f, g) for f, g in zip(fin_f, ini_f)])

    from ase import Atoms
    mk = lambda F: Atoms([sym[s] for s in order], scaled_positions=F, cell=lat, pbc=True)
    first, last = mk(ini_f), mk(fin_f)
    first.set_scaled_positions(ini_f)
    last.set_scaled_positions(fin_f)
    # keep unwrapped coordinates (set_scaled_positions does not wrap)
    first.positions, last.positions = ini_f @ lat, fin_f @ lat

    images = [first] + [first.copy() for _ in range(a.images)] + [last]
    neb = NEB(images, method="improvedtangent")
    neb.interpolate(method="idpp")

    k_move = order.index(j)
    moved = np.linalg.norm(last.positions[k_move] - first.positions[k_move])
    others = np.delete(np.linalg.norm(last.positions - first.positions, axis=1), k_move)
    mins = []
    for im in images:
        D = im.get_all_distances(mic=True)
        np.fill_diagonal(D, 1e9)
        mins.append(D.min())

    # ---- write ----------------------------------------------------------------
    hopdir = os.path.join(a.out, a.charge, a.hop)
    os.makedirs(hopdir, exist_ok=True)
    write(os.path.join(hopdir, "path.xyz"), images, format="extxyz")

    tmpl = open(os.path.join(vdir, f"vac_I_{'equatorial' if start == '8d' else 'apical'}", "relax.in")).read().splitlines()
    eng, skip, block = [], False, None
    for line in tmpl:
        s = line.strip()
        if s.startswith("!"):
            continue
        if s.upper().startswith("&IONS"):
            skip = True
        if skip:
            if s == "/":
                skip = False
            continue
        if s.upper().startswith("ATOMIC_POSITIONS"):
            block = "pos"
            continue
        if block == "pos":
            if s == "" or s.upper().startswith("K_POINTS"):
                block = None
            else:
                continue
        key = s.split("=")[0].strip().lower()
        if key in DROP_CONTROL:
            continue
        if key == "prefix":
            line = f"  prefix        = 'neb_{a.hop}_{a.charge.replace('+', 'p')}'"
        eng.append(line)

    def pos_block(im):
        return ["ATOMIC_POSITIONS angstrom"] + [
            f"{s:2s} {p[0]:14.8f} {p[1]:14.8f} {p[2]:14.8f}" for s, p in zip(im.get_chemical_symbols(), im.positions)]

    pos = ["BEGIN_POSITIONS", "FIRST_IMAGE"] + pos_block(images[0])
    for im in images[1:-1]:
        pos += ["INTERMEDIATE_IMAGE"] + pos_block(im)
    pos += ["LAST_IMAGE"] + pos_block(images[-1]) + ["END_POSITIONS"]

    nimg = len(images)
    text = ["BEGIN", "BEGIN_PATH_INPUT", PATH_SETTINGS.format(nimg=nimg), "END_PATH_INPUT",
            "BEGIN_ENGINE_INPUT"] + eng + pos + ["END_ENGINE_INPUT", "END", ""]
    open(os.path.join(hopdir, "neb.in"), "w").write("\n".join(text))

    mem = MEM_PER_IMAGE_GB[a.charge]
    nodes_img = math.ceil(mem / USABLE_GB_PER_NODE)
    rep = [
        f"Hop {a.hop} ({t1}-{t2}, nominal {L:.2f} A), charge {a.charge}",
        f"Space group of the perfect supercell: {sg}, {len(ops)} operations",
        f"Start: vacancy on site {r} ({start}), from {paths[start]} (largest offset from a site {worst_init:.2f} A)",
        f"End:   vacancy on site {j} ({types[j]}), from {paths[end]} carried by "
        f"{'a pure translation' if np.allclose(R, np.eye(3)) else 'a point operation'} (t = {np.round(t, 4).tolist()})",
        f"Hopping iodine: perfect-cell site {j}, atom {k_move + 1} of {len(order)} in neb.in; "
        f"site distance {d_hop:.3f} A, moves {moved:.3f} A",
        f"Other atoms: largest end-to-end shift {others.max():.3f} A, mean {others.mean():.3f} A",
        f"Images: {nimg} in total ({a.images} intermediate, IDPP)",
        "Closest approach of two atoms per image (A): " + " ".join(f"{m:.2f}" for m in mins),
    ]
    if min(mins) < MIN_DIST_WARN:
        rep.append(f"WARNING: an image has two atoms closer than {MIN_DIST_WARN} A; check path.xyz")
    rep += [
        "",
        f"Memory: about {mem} GB per image -> at least {nodes_img} nodes per image ({USABLE_GB_PER_NODE} GB usable per node)",
        f"The end points are computed once; {a.images} moving images per NEB step.",
        "Run examples (images run side by side with -ni):",
        f"  4 nodes: mpirun neb.x -ni {4 // nodes_img} -nk 2 -inp neb.in" if 4 // nodes_img >= 1 else "  4 nodes: not enough for one image",
        f"  8 nodes: mpirun neb.x -ni {8 // nodes_img} -nk 2 -inp neb.in",
    ]
    open(os.path.join(hopdir, "report.txt"), "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))
    print(f"\nWritten: {hopdir}/neb.in, path.xyz, report.txt")


if __name__ == "__main__":
    main()
