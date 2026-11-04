#!/usr/bin/env python3
"""
Build Quantum ESPRESSO inputs for the reference phases of step 5
(chemical-potential region of gamma-CsPbI3).

Writes, under qe/05_reference_phases/ (run from the project root):

  Cs/vcrelax.in         bcc Cs metal (Im-3m)          elemental reference mu_Cs
  Pb/vcrelax.in         fcc Pb metal (Fm-3m)          elemental reference mu_Pb
  I2/vcrelax.in         solid iodine (Cmca, 4 atoms)  elemental reference mu_I
  I2_molecule/relax.in  isolated I2 in a 15 A box     cross-check of mu_I (no dispersion in PBEsol)
  CsI/vcrelax.in        CsCl type (Pm-3m)             competing phase
  PbI2/vcrelax.in       2H-PbI2, CdI2 type (P-3m1)    competing phase
  *.cif next to every input, and structures_report.txt

Ternary competing phases (Cs4PbI6, CsPb2I5) are not built here: their
structures need a CIF (Materials Project or ICSD); see the README.

Settings match the CsPbI3 calculations: PBEsol, SSSP 1.3.0 pseudopotentials,
60/480 Ry, no spin-orbit coupling, no dispersion, non-spin-polarised.
Metals use Marzari-Vanderbilt smearing (0.01 Ry) and a denser k-mesh.

Starting structures are experimental (low-temperature where known); every
cell is relaxed with vc-relax, keeping its space group.

Usage (from the project root):
    python3 qe/05_reference_phases/build_refs.py --pseudo-dir /public/home/daomduy/cspbi3/pseudo_pbesol

Needs: python3 with numpy, ase and spglib.
"""

import argparse
import math
import os

import numpy as np
import spglib
from ase import Atoms
from ase.build import bulk
from ase.io import write
from ase.spacegroup import crystal

# ---- settings ----------------------------------------------------------------
ECUTWFC, ECUTRHO = 60.0, 480.0
ETOT_THR = 1.0e-6        # Ry (small cells: tighter than the supercells)
FORC_THR = 4.0e-4        # Ry/Bohr, same as the supercells
CONV_THR = 1.0e-10       # Ry, SCF
PRESS_THR = 0.2          # kbar, same as the unit cell
K_LEN_INSULATOR = 36.0   # A: n_i = ceil(K_LEN / |a_i|); the CsPbI3 4x4x3 mesh gives 33-37 A
K_LEN_METAL = 70.0       # A, metals need about twice as dense a mesh
DEGAUSS = 0.01           # Ry, Marzari-Vanderbilt smearing for the metals
BOX = 15.0               # A, cubic box for the I2 molecule
MASSES = {"Cs": 132.905, "Pb": 207.2, "I": 126.904}
PSEUDO = {"Cs": "cs_pbesol_v1.uspp.F.UPF",
          "Pb": "Pb.pbesol-dn-kjpaw_psl.0.2.2.UPF",
          "I": "I.pbesol-n-kjpaw_psl.0.2.UPF"}
# ------------------------------------------------------------------------------


def phases():
    """name -> (Atoms, metal?, expected space-group number, source of the start structure)"""
    out = {}
    out["Cs"] = (bulk("Cs", "bcc", a=6.05), True, 229,
                 "bcc, a = 6.05 A (experiment, about 80 K)")
    out["Pb"] = (bulk("Pb", "fcc", a=4.95), True, 225,
                 "fcc, a = 4.95 A (experiment)")
    i2 = crystal(["I"], basis=[(0.0, 0.1543, 0.1174)], spacegroup=64,
                 cellpar=[7.136, 4.686, 9.784, 90, 90, 90])
    out["I2"] = (primitive(i2), False, 64,
                 "Cmca, a = 7.136, b = 4.686, c = 9.784 A, I at 8f (0, 0.1543, 0.1174) (experiment, 110 K)")
    out["CsI"] = (crystal(["Cs", "I"], basis=[(0, 0, 0), (0.5, 0.5, 0.5)], spacegroup=221,
                          cellpar=[4.567, 4.567, 4.567, 90, 90, 90]), False, 221,
                  "CsCl type, a = 4.567 A (experiment)")
    out["PbI2"] = (crystal(["Pb", "I"], basis=[(0, 0, 0), (1 / 3, 2 / 3, 0.265)], spacegroup=164,
                           cellpar=[4.557, 4.557, 6.979, 90, 90, 120]), False, 164,
                   "2H (CdI2 type), a = 4.557, c = 6.979 A, I at 2d z = 0.265 (experiment)")
    return out


def primitive(atoms):
    cell = (atoms.cell.array, atoms.get_scaled_positions(), atoms.get_atomic_numbers())
    lat, pos, num = spglib.find_primitive(cell, symprec=1e-3)
    return Atoms(numbers=num, scaled_positions=pos, cell=lat, pbc=True)


def spacegroup(atoms):
    ds = spglib.get_symmetry_dataset((atoms.cell.array, atoms.get_scaled_positions(),
                                      atoms.get_atomic_numbers()), symprec=1e-3)
    return (ds.number, ds.international) if hasattr(ds, "number") else (ds["number"], ds["international"])


def kmesh(atoms, length):
    return tuple(max(1, math.ceil(length / np.linalg.norm(v))) for v in atoms.cell.array)


def write_input(path, name, atoms, kind, metal, k, pseudo_dir):
    calc = "vc-relax" if kind == "bulk" else "relax"
    species = sorted(set(atoms.get_chemical_symbols()), key=["Cs", "Pb", "I"].index)
    L = ["&CONTROL",
         f"  calculation   = '{calc}'",
         f"  prefix        = 'ref_{name}'",
         "  outdir        = './tmp'",
         f"  pseudo_dir    = '{pseudo_dir}'",
         f"  etot_conv_thr = {ETOT_THR:.1e}",
         f"  forc_conv_thr = {FORC_THR:.1e}",
         "  nstep         = 200",
         "  tprnfor       = .true.",
         "  tstress       = .true.",
         "/", "",
         "&SYSTEM",
         "  ibrav       = 0",
         f"  nat         = {len(atoms)}",
         f"  ntyp        = {len(species)}",
         f"  ecutwfc     = {ECUTWFC}",
         f"  ecutrho     = {ECUTRHO}"]
    if metal:
        L += ["  occupations = 'smearing'", "  smearing    = 'mv'", f"  degauss     = {DEGAUSS}"]
    else:
        L += ["  occupations = 'fixed'"]
    if kind == "molecule":
        L += ["  assume_isolated = 'mt'"]
    L += ["/", "",
          "&ELECTRONS", f"  conv_thr    = {CONV_THR:.1e}", "  mixing_beta = 0.3", "  electron_maxstep = 300", "/", "",
          "&IONS", "  ion_dynamics = 'bfgs'", "/", ""]
    if kind == "bulk":
        L += ["&CELL", "  cell_dynamics = 'bfgs'", "  cell_dofree   = 'all'",
              f"  press_conv_thr = {PRESS_THR}", "/", ""]
    L += ["ATOMIC_SPECIES"] + [f"{s:2s}  {MASSES[s]:8.3f}  {PSEUDO[s]}" for s in species] + [""]
    L += ["CELL_PARAMETERS angstrom"] + [f"  {v[0]:16.10f} {v[1]:16.10f} {v[2]:16.10f}" for v in atoms.cell.array] + [""]
    L += ["ATOMIC_POSITIONS crystal"] + [f"{s:2s} {p[0]:14.10f} {p[1]:14.10f} {p[2]:14.10f}"
                                         for s, p in zip(atoms.get_chemical_symbols(), atoms.get_scaled_positions())] + [""]
    if kind == "molecule":
        L += ["K_POINTS gamma", ""]
    else:
        L += ["K_POINTS automatic", f"  {k[0]} {k[1]} {k[2]} 0 0 0", ""]
    open(path, "w").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pseudo-dir", default="/public/home/daomduy/cspbi3/pseudo_pbesol")
    ap.add_argument("--out", default="qe/05_reference_phases")
    a = ap.parse_args()

    rep = ["Reference phases for step 5 (start structures, before relaxation)", ""]
    rep.append(f"{'phase':12s} {'atoms':>5s} {'space group':>14s} {'k-mesh':>9s}  start structure")
    for name, (atoms, metal, sg_expected, source) in phases().items():
        num, sym = spacegroup(atoms)
        if num != sg_expected:
            raise SystemExit(f"{name}: space group {num}, expected {sg_expected}")
        k = kmesh(atoms, K_LEN_METAL if metal else K_LEN_INSULATOR)
        d = os.path.join(a.out, name)
        os.makedirs(d, exist_ok=True)
        write_input(os.path.join(d, "vcrelax.in"), name, atoms, "bulk", metal, k, a.pseudo_dir)
        write(os.path.join(d, "start.cif"), atoms)
        f_units = len(atoms) // (2 if name == "I2" else (3 if name == "PbI2" else (2 if name == "CsI" else 1)))
        rep.append(f"{name:12s} {len(atoms):5d} {sym + ' (' + str(num) + ')':>14s} {'x'.join(map(str, k)):>9s}  {source}"
                   + (f"; {f_units} formula units" if f_units > 1 else ""))

    # isolated I2 molecule, start at the gas-phase bond length (2.67 A)
    mol = Atoms("I2", positions=[(0, 0, 0), (0, 0, 2.67)], cell=[BOX] * 3, pbc=True)
    mol.center()
    d = os.path.join(a.out, "I2_molecule")
    os.makedirs(d, exist_ok=True)
    write_input(os.path.join(d, "relax.in"), "I2_molecule", mol, "molecule", False, None, a.pseudo_dir)
    write(os.path.join(d, "start.cif"), mol)
    rep.append(f"{'I2_molecule':12s} {2:5d} {'-':>14s} {'gamma':>9s}  I-I 2.67 A (gas), {BOX:.0f} A cubic box, Martyna-Tuckerman")

    rep += ["",
            "Settings: PBEsol, SSSP 1.3.0, 60/480 Ry, no SOC, no dispersion, non-spin-polarised.",
            f"k-mesh: n_i = ceil(L / |a_i|), L = {K_LEN_INSULATOR:.0f} A (insulators) or {K_LEN_METAL:.0f} A (metals, MV smearing {DEGAUSS} Ry).",
            "Energies to use: total energy per atom (Cs, Pb, I) or per formula unit (CsI, PbI2) of the relaxed cell.",
            "Check after the run: I2 and PbI2 are held by van der Waals forces, which PBEsol lacks;",
            "compare the relaxed b/c (I2) and c (PbI2) with experiment. If c expands by more than about 5%,",
            "rerun with the experimental cell (calculation = 'relax') and note the energy change."]
    open(os.path.join(a.out, "structures_report.txt"), "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
