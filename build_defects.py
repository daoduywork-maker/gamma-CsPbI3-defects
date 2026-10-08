#!/usr/bin/env python3
"""
Build the bulk iodine-vacancy structures for gamma-CsPbI3 from a relaxed unit cell.

Reads a Quantum ESPRESSO input holding the relaxed 20-atom cell and writes,
under an output folder (default: defects/):

  unitcell_tight/vcrelax.in       tight variable-cell relaxation of the unit cell
  pristine_222/relax.in           perfect 2x2x2 supercell (160 atoms), energy reference
  q+1/ and q0/                    the same vacancies in two charge states:
                                  +1 (closed shell) and neutral (spin-polarised)
    vac_I_apical/relax.in         one apical iodine removed
    vac_I_equatorial/relax.in     one equatorial iodine removed
  *.cif next to every input       for viewing in VESTA
  sites_report.txt                which atoms were removed

This script builds vacancies only. The end points and NEB inputs for the
10 distinct hops (S1-S6, L1-L4) will come from a separate script, build_neb.py.

Usage:
    python3 build_defects.py unitcell_tight/unit_tight_relaxed.in
    python3 build_defects.py unitcell_tight/unit_tight_relaxed.in --pseudo-dir /path/on/cluster

Needs: python3 with numpy and ase.
"""

import argparse
import os
import re
import sys

import numpy as np
from ase.io import read, write

# ---- settings for the generated inputs (edit here if needed) ----------------
ECUTWFC = 60.0          # Ry, from the convergence test
ECUTRHO = 480.0
K_UNIT = (4, 4, 3)      # converged mesh for the 20-atom cell
FORC_THR = 4.0e-4       # Ry/Bohr, about 0.01 eV/Angstrom
ETOT_THR = 1.0e-5       # Ry
CONV_THR = 1.0e-9       # Ry, SCF
PRESS_THR = 0.2         # kbar, for the unit-cell relaxation
PB_I_CUTOFF = 3.6       # Angstrom, Pb-I bonds are about 3.2
MASSES = {"Cs": 132.905, "Pb": 207.2, "I": 126.904}
# ------------------------------------------------------------------------------


def parse_species(path):
    """Return {element: pseudopotential file} from the ATOMIC_SPECIES block."""
    lines = open(path).read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip().upper().startswith("ATOMIC_SPECIES"))
    species = {}
    for l in lines[start + 1:]:
        p = l.split()
        if len(p) != 3:
            break
        species[p[0]] = p[2]
    return species


def kmesh_for(rep):
    """Scale the unit-cell mesh down for a supercell, rounding up."""
    return tuple(max(1, int(np.ceil(k / r))) for k, r in zip(K_UNIT, rep))


def write_qe(path, atoms, species, calc, kpts, pseudo_dir, prefix, charge=0, open_shell=False, note=""):
    order = [s for s in ("Cs", "Pb", "I") if s in set(atoms.get_chemical_symbols())]
    with open(path, "w") as f:
        if note:
            for l in note.splitlines():
                f.write("! " + l + "\n")
            f.write("\n")
        f.write("&CONTROL\n")
        f.write("  calculation   = '%s'\n" % calc)
        f.write("  prefix        = '%s'\n" % prefix)
        f.write("  outdir        = './tmp'\n")
        f.write("  pseudo_dir    = '%s'\n" % pseudo_dir)
        f.write("  etot_conv_thr = %.1e\n" % ETOT_THR)
        f.write("  forc_conv_thr = %.1e\n" % FORC_THR)
        f.write("  nstep         = 300\n")
        f.write("  tprnfor       = .true.\n")
        f.write("  tstress       = .true.\n")
        f.write("/\n\n&SYSTEM\n")
        f.write("  ibrav       = 0\n")
        f.write("  nat         = %d\n" % len(atoms))
        f.write("  ntyp        = %d\n" % len(order))
        f.write("  ecutwfc     = %.1f\n" % ECUTWFC)
        f.write("  ecutrho     = %.1f\n" % ECUTRHO)
        if open_shell:
            # odd number of electrons: needs spin polarisation and a little smearing
            f.write("  occupations = 'smearing'\n")
            f.write("  smearing    = 'gaussian'\n")
            f.write("  degauss     = 0.002\n")
            f.write("  nspin       = 2\n")
            f.write("  starting_magnetization(%d) = 0.1\n" % (order.index("I") + 1))
        else:
            f.write("  occupations = 'fixed'\n")
        if charge != 0:
            f.write("  tot_charge  = %.1f\n" % charge)
        f.write("/\n\n&ELECTRONS\n")
        f.write("  conv_thr    = %.1e\n" % CONV_THR)
        f.write("  mixing_beta = 0.3\n")
        f.write("  electron_maxstep = 300\n")
        f.write("/\n\n&IONS\n  ion_dynamics = 'bfgs'\n/\n")
        if calc == "vc-relax":
            f.write("\n&CELL\n  cell_dynamics  = 'bfgs'\n  press          = 0.0\n")
            f.write("  press_conv_thr = %.2f\n  cell_dofree    = 'all'\n/\n" % PRESS_THR)
        f.write("\nATOMIC_SPECIES\n")
        for s in order:
            f.write("%-3s %9.3f  %s\n" % (s, MASSES[s], species[s]))
        f.write("\nCELL_PARAMETERS angstrom\n")
        for v in atoms.cell.array:
            f.write("  %16.10f %16.10f %16.10f\n" % tuple(v))
        f.write("\nATOMIC_POSITIONS angstrom\n")
        for s, r in zip(atoms.get_chemical_symbols(), atoms.positions):
            f.write("%-3s %16.10f %16.10f %16.10f\n" % (s, r[0], r[1], r[2]))
        f.write("\nK_POINTS automatic\n%d %d %d  0 0 0\n" % kpts)
    write(os.path.splitext(path)[0] + ".cif", atoms)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("unitcell", help="QE input with the relaxed 20-atom cell")
    ap.add_argument("--out", default="defects", help="output folder (default: defects)")
    ap.add_argument("--rep", default="2,2,2", help="supercell repetitions (default: 2,2,2)")
    ap.add_argument("--pseudo-dir", default=None, help="pseudopotential folder on the machine that will run the jobs")
    args = ap.parse_args()

    rep = tuple(int(x) for x in args.rep.split(","))
    species = parse_species(args.unitcell)
    pseudo_dir = args.pseudo_dir
    if pseudo_dir is None:
        m = re.search(r"pseudo_dir\s*=\s*'([^']*)'", open(args.unitcell).read())
        pseudo_dir = m.group(1) if m else "./pseudo"

    unit = read(args.unitcell, format="espresso-in")
    sym = np.array(unit.get_chemical_symbols())
    if sorted(set(sym)) != ["Cs", "I", "Pb"]:
        sys.exit("Expected Cs, Pb and I in the unit cell, found: %s" % sorted(set(sym)))

    # Classify iodine by its bonds: apical iodine bridges two Pb along the long (c) axis.
    tags = np.zeros(len(unit), dtype=int)       # 0 = not iodine, 1 = apical, 2 = equatorial
    pb = np.where(sym == "Pb")[0]
    for i in np.where(sym == "I")[0]:
        vec = unit.get_distances(i, pb, mic=True, vector=True)
        d = np.linalg.norm(vec, axis=1)
        near = vec[np.argsort(d)[:2]]
        if np.sort(d)[1] > PB_I_CUTOFF:
            sys.exit("Iodine atom %d does not have two Pb neighbours within %.1f A." % (i, PB_I_CUTOFF))
        bond = near[0] / np.linalg.norm(near[0])
        chat = unit.cell.array[2] / np.linalg.norm(unit.cell.array[2])
        tags[i] = 1 if abs(bond @ chat) > 0.7 else 2
    unit.set_tags(tags)
    n_ap, n_eq = int((tags == 1).sum()), int((tags == 2).sum())
    if (n_ap, n_eq) != (4, 8):
        print("WARNING: expected 4 apical and 8 equatorial iodine, found %d and %d." % (n_ap, n_eq))

    sc = unit.repeat(rep)
    ksc = kmesh_for(rep)
    os.makedirs(args.out, exist_ok=True)
    report = []
    report.append("Source unit cell : %s" % args.unitcell)
    report.append("Supercell        : %dx%dx%d, %d atoms, k-mesh %d %d %d" % (*rep, len(sc), *ksc))
    report.append("Cell lengths (A) : %.4f %.4f %.4f" % tuple(sc.cell.lengths()))
    report.append("")

    def sub(name):
        p = os.path.join(args.out, name)
        os.makedirs(p, exist_ok=True)
        return p

    # Tight relaxation of the unit cell
    write_qe(os.path.join(sub("unitcell_tight"), "vcrelax.in"), unit, species, "vc-relax", K_UNIT,
             pseudo_dir, "unit_tight",
             note="Tight variable-cell relaxation of the 20-atom gamma-CsPbI3 cell.\n"
                  "Run this first, then rebuild the supercell from its result.")

    # Perfect supercell
    write_qe(os.path.join(sub("pristine_%d%d%d" % rep), "relax.in"), sc, species, "relax", ksc,
             pseudo_dir, "pristine",
             note="Perfect supercell. Fixed cell, atoms relaxed. Energy reference for all defects.")

    stags = sc.get_tags()
    ssym = np.array(sc.get_chemical_symbols())
    centre = sc.cell.array.sum(axis=0) / 2.0
    label = {1: "apical", 2: "equatorial"}

    # Each vacancy is written twice: charge +1 (the mobile species in the real
    # material, closed shell) and neutral (odd electron count, spin-polarised).
    states = (("q+1", 1, False, "charge +1"), ("q0", 0, True, "neutral"))

    for t in (1, 2):
        cand = np.where(stags == t)[0]
        a = cand[np.argmin(np.linalg.norm(sc.positions[cand] - centre, axis=1))]
        pos_a = sc.positions[a].copy()

        vac = sc.copy()
        del vac[a]
        name = "vac_I_%s" % label[t]
        for folder, q, opn, qtext in states:
            write_qe(os.path.join(sub(os.path.join(folder, name)), "relax.in"), vac, species, "relax", ksc,
                     pseudo_dir, "%s_%s" % (name, folder.replace("+", "p")), charge=q, open_shell=opn,
                     note="Iodine vacancy on an %s site, %s (atom %d of the perfect supercell removed)."
                          % (label[t], qtext, a + 1))

        report.append("%s vacancy: removed atom %d at (%.3f, %.3f, %.3f) A" % (label[t].capitalize(), a + 1, *pos_a))

        report.append("")

    report.append("q+1/ holds the +1 charged vacancies, q0/ the neutral ones (spin-polarised).")
    with open(os.path.join(args.out, "sites_report.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))
    print("\nWritten to: %s/" % args.out)


if __name__ == "__main__":
    main()
