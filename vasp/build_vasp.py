#!/usr/bin/env python3
"""
VASP counterpart of the Quantum ESPRESSO workflow (steps 1, 2, 3 and 5).

Same physics as the QE runs: PBEsol (GGA = PS), no spin-orbit coupling, no
dispersion, same structures, same vacancy sites, same force limit
(0.01 eV/A = 4e-4 Ry/Bohr). Only the code and the basis change:
PAW potentials Cs_sv, Pb_d, I and a 500 eV cutoff (as in Arber 2025).

Subcommands (run from the project root; the cluster has no Python):

  unitcell   step 1: cutoff and k-mesh tests, then the variable-cell relaxation
             python3 vasp/build_vasp.py unitcell
  supercell  steps 2 and 3: perfect 2x2x2 supercell and the four vacancy cells,
             built from the relaxed VASP unit cell
             python3 vasp/build_vasp.py supercell --unit vasp/01_unitcell/relax/CONTCAR
  refs       step 5: Cs, Pb, solid I2, CsI, PbI2 and the I2 molecule
             python3 vasp/build_vasp.py refs
  slab       step 8: CsI-terminated (001) slabs, 7, 9 and 11 layers, 1x1 in-plane
             python3 vasp/build_vasp.py slab [--layers 13 15 17]
  slabvac    step 9 test: 2x2 copy of a relaxed slab with +1 vacancies at its centre
             python3 vasp/build_vasp.py slabvac --slab vasp/08_slab/L11/CONTCAR

The NEB inputs (step 4) come from tools/build_neb.py with --code vasp.
POTCAR files are made on the cluster with vasp/make_potcar.sh.

Needs: python3 with numpy, ase and spglib.
"""

import argparse
import math
import os
import sys

import numpy as np
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "qe", "05_reference_phases"))

# ---- settings ----------------------------------------------------------------
ENCUT = 500                      # eV, as in Arber 2025 (VASP, PBEsol)
ENCUT_TEST = (350, 400, 450, 500, 550, 600, 650)
KMESH_TEST = ((2, 2, 1), (3, 3, 2), (4, 4, 3), (5, 5, 4), (6, 6, 4))
K_UNIT = (4, 4, 3)               # same as QE
K_SUPER = (2, 2, 2)              # same as QE
EDIFFG = -0.01                   # eV/A, same force limit as QE (4e-4 Ry/Bohr)
ZVAL = {"Cs": 9, "Pb": 14, "I": 7}   # Cs_sv, Pb_d, I (checked again by make_potcar.sh)
ORDER = ("Cs", "Pb", "I")
PB_I_CUTOFF = 3.6
# ------------------------------------------------------------------------------


def sort_atoms(atoms):
    """Cs, Pb, I order (one block per species, as POSCAR needs); stable within a species."""
    idx = [i for s in ORDER for i, a in enumerate(atoms.get_chemical_symbols()) if a == s]
    return atoms[idx]


def nelect(atoms, charge=0):
    return sum(ZVAL[s] for s in atoms.get_chemical_symbols()) - charge


def write_poscar(path, atoms, comment):
    write(path, atoms, format="vasp", direct=True, sort=False)


def write_kpoints(path, k, comment="Gamma-centred mesh (same points as the QE unshifted mesh)"):
    with open(path, "w") as f:
        f.write("%s\n0\nGamma\n%d %d %d\n0 0 0\n" % (comment, *k))


def incar(path, title, tags):
    """tags: list of (key, value, comment) or a bare comment string."""
    with open(path, "w") as f:
        f.write("SYSTEM = %s\n" % title)
        for t in tags:
            if isinstance(t, str):
                f.write("\n# %s\n" % t)
            else:
                k, v, c = t
                f.write("%-8s = %-14s%s\n" % (k, v, ("  ! " + c) if c else ""))


def base_tags(lreal):
    return [
        "Electronic structure (same physics as the QE runs)",
        ("GGA", "PS", "PBEsol"),
        ("PREC", "Accurate", ""),
        ("ENCUT", ENCUT, "eV; PAW Cs_sv, Pb_d, I"),
        ("LASPH", ".TRUE.", "non-spherical terms inside the PAW spheres"),
        ("LREAL", lreal, "Auto for the 159/160-atom cells, .FALSE. for small cells"),
        ("ALGO", "Normal", ""),
        ("NELM", 200, ""),
        ("EDIFF", "1E-6", "eV"),
        ("ISMEAR", 0, "Gaussian"),
        ("SIGMA", 0.01, "eV; insulator (QE: fixed occupations)"),
        "Output",
        ("LWAVE", ".FALSE.", ""),
        ("LCHARG", ".FALSE.", ""),
    ]


def para_tags(ncore=10, kpar=1):
    return ["Parallelisation (40 cores per std40 node)",
            ("NCORE", ncore, ""),
            ("KPAR", kpar, "k-point groups, more of them is faster but uses more memory")]


# ---------------------------------------------------------------- step 1 -----
def cmd_unitcell(a):
    start = read(a.start, format="espresso-in" if a.start.endswith(".in") else None)
    start = sort_atoms(start)
    out = os.path.join(HERE, "01_unitcell")

    # cutoff test: static runs at 4x4x3 (energy and pressure)
    for e in ENCUT_TEST:
        d = os.path.join(out, "conv", "encut_%d" % e)
        os.makedirs(d, exist_ok=True)
        write_poscar(os.path.join(d, "POSCAR"), start, "gamma-CsPbI3 start structure")
        write_kpoints(os.path.join(d, "KPOINTS"), K_UNIT)
        tags = [t if not (isinstance(t, tuple) and t[0] == "ENCUT") else ("ENCUT", e, "cutoff test")
                for t in base_tags(".FALSE.")]
        incar(os.path.join(d, "INCAR"), "cutoff test %d eV" % e,
              tags + ["Static run", ("NSW", 0, ""), ("ISIF", 2, "prints the stress")] + para_tags(10, 4))
    # k-mesh test: static runs at 500 eV
    for k in KMESH_TEST:
        d = os.path.join(out, "conv", "k%d%d%d" % k)
        os.makedirs(d, exist_ok=True)
        write_poscar(os.path.join(d, "POSCAR"), start, "gamma-CsPbI3 start structure")
        write_kpoints(os.path.join(d, "KPOINTS"), k)
        incar(os.path.join(d, "INCAR"), "k-mesh test %dx%dx%d" % k,
              base_tags(".FALSE.") + ["Static run", ("NSW", 0, ""), ("ISIF", 2, "")] + para_tags(10, 2))

    # variable-cell relaxation (run twice by run_vasp.pbs: STAGES=2 restarts from CONTCAR)
    d = os.path.join(out, "relax")
    os.makedirs(d, exist_ok=True)
    write_poscar(os.path.join(d, "POSCAR"), start, "gamma-CsPbI3 start structure")
    write_kpoints(os.path.join(d, "KPOINTS"), K_UNIT)
    incar(os.path.join(d, "INCAR"), "gamma-CsPbI3 unit cell, variable-cell relaxation",
          base_tags(".FALSE.") + [
              "Relaxation: cell shape, volume and atoms",
              ("IBRION", 2, "conjugate gradient"),
              ("ISIF", 3, ""),
              ("NSW", 200, ""),
              ("EDIFFG", EDIFFG, "eV/A, same force limit as QE"),
              ("PSTRESS", 0, "kbar")] + para_tags(10, 4))
    print("Written: vasp/01_unitcell/conv/ (%d cutoff + %d k-mesh tests) and vasp/01_unitcell/relax/"
          % (len(ENCUT_TEST), len(KMESH_TEST)))
    print("Start structure: %s (%d atoms), cell %.4f %.4f %.4f A" % (a.start, len(start), *start.cell.lengths()))


# ----------------------------------------------------------- steps 2 and 3 ---
def iodine_tags(unit):
    """1 = apical (4c), 2 = equatorial (8d), as in qe/03_vacancies/build_defects.py."""
    sym = np.array(unit.get_chemical_symbols())
    tags = np.zeros(len(unit), dtype=int)
    pb = np.where(sym == "Pb")[0]
    chat = unit.cell.array[2] / np.linalg.norm(unit.cell.array[2])
    for i in np.where(sym == "I")[0]:
        vec = unit.get_distances(i, pb, mic=True, vector=True)
        d = np.linalg.norm(vec, axis=1)
        if np.sort(d)[1] > PB_I_CUTOFF:
            sys.exit("iodine %d has fewer than two Pb within %.1f A" % (i, PB_I_CUTOFF))
        bond = vec[np.argmin(d)] / d.min()
        tags[i] = 1 if abs(bond @ chat) > 0.7 else 2
    return tags


def defect_incar(path, title, natoms_note, charge, spin):
    tags = base_tags("Auto") + [
        "Relaxation: atoms only, cell fixed (as in QE)",
        ("IBRION", 2, ""),
        ("ISIF", 2, ""),
        ("NSW", 300, ""),
        ("EDIFFG", EDIFFG, "eV/A, same force limit as QE")]
    if charge is not None:
        tags += ["Charge state: %s" % natoms_note, ("NELECT", charge, "default minus the charge")]
    if spin:
        tags += ["Odd electron count: spin-polarised (QE: nspin = 2)",
                 ("ISPIN", 2, ""), ("MAGMOM", "%d*0.1" % spin, "small start moment on every atom")]
    tags += para_tags(10, 1)
    incar(path, title, tags)


def cmd_supercell(a):
    unit = sort_atoms(read(a.unit))
    tags = iodine_tags(unit)
    if ((tags == 1).sum(), (tags == 2).sum()) != (4, 8):
        sys.exit("expected 4 apical and 8 equatorial iodine in the unit cell")
    unit.set_tags(tags)
    sc = sort_atoms(unit.repeat((2, 2, 2)))
    out = HERE
    rep = ["Unit cell: %s" % a.unit,
           "Supercell: 2x2x2, %d atoms, cell %.4f %.4f %.4f A, k-mesh %d %d %d (Gamma)"
           % (len(sc), *sc.cell.lengths(), *K_SUPER),
           "Electrons (Cs_sv 9, Pb_d 14, I 7): perfect %d" % nelect(sc), ""]

    d = os.path.join(out, "02_pristine")
    os.makedirs(d, exist_ok=True)
    write_poscar(os.path.join(d, "POSCAR"), sc, "perfect 2x2x2 supercell")
    write_kpoints(os.path.join(d, "KPOINTS"), K_SUPER)
    defect_incar(os.path.join(d, "INCAR"), "perfect 2x2x2 supercell (energy and VBM reference)", "", None, 0)

    centre = sc.cell.array.sum(axis=0) / 2
    stags = sc.get_tags()
    for t, name in ((1, "vac_I_apical"), (2, "vac_I_equatorial")):
        cand = np.where(stags == t)[0]
        i = cand[np.argmin(np.linalg.norm(sc.positions[cand] - centre, axis=1))]
        vac = sc.copy()
        del vac[i]
        rep.append("%s: removed atom %d (POSCAR order) at (%.3f, %.3f, %.3f) A"
                   % (name, i + 1, *sc.positions[i]))
        for folder, q, spin in (("q+1", 1, False), ("q0", 0, True)):
            d = os.path.join(out, "03_vacancies", folder, name)
            os.makedirs(d, exist_ok=True)
            write_poscar(os.path.join(d, "POSCAR"), vac, "%s %s" % (name, folder))
            write_kpoints(os.path.join(d, "KPOINTS"), K_SUPER)
            ne = nelect(vac, q)
            defect_incar(os.path.join(d, "INCAR"), "%s, %s" % (name, "charge +1" if q else "neutral"),
                         "+1, %d electrons" % ne if q else "neutral", ne if q else None,
                         len(vac) if spin else 0)
        rep.append("  electrons: q+1 %d (NELECT set), q0 %d (default)" % (nelect(vac, 1), nelect(vac)))
    rep += ["", "Same choice as the QE cells: the 4c or 8d iodine closest to the cell centre."]
    with open(os.path.join(out, "03_vacancies", "sites_report.txt"), "w") as f:
        f.write("\n".join(rep) + "\n")
    print("\n".join(rep))


# ---------------------------------------------------------------- step 5 -----
def cmd_refs(a):
    import build_refs as br
    out = os.path.join(HERE, "05_reference_phases")
    rows = []
    for name, (atoms, metal, sg, source) in br.phases().items():
        atoms = sort_atoms(atoms)
        d = os.path.join(out, name)
        os.makedirs(d, exist_ok=True)
        k = br.kmesh(atoms, br.K_LEN_METAL if metal else br.K_LEN_INSULATOR)
        write_poscar(os.path.join(d, "POSCAR"), atoms, name + " start structure")
        write_kpoints(os.path.join(d, "KPOINTS"), k)
        tags = base_tags(".FALSE.")
        if metal:
            tags = [t if not (isinstance(t, tuple) and t[0] in ("ISMEAR", "SIGMA")) else
                    (("ISMEAR", 1, "Methfessel-Paxton, metal") if t[0] == "ISMEAR" else ("SIGMA", 0.1, "eV (QE: MV 0.01 Ry)"))
                    for t in tags]
        incar(os.path.join(d, "INCAR"), name + ", variable-cell relaxation",
              tags + ["Relaxation", ("IBRION", 2, ""), ("ISIF", 3, ""), ("NSW", 200, ""),
                      ("EDIFFG", EDIFFG, "")] + para_tags(4, 1))
        rows.append("%-12s %3d atoms  k %s  %s" % (name, len(atoms), "x".join(map(str, k)), source))
    # isolated I2 molecule
    from ase import Atoms
    mol = Atoms("I2", positions=[(0, 0, 0), (0, 0, 2.67)], cell=[br.BOX] * 3, pbc=True)
    mol.center()
    d = os.path.join(out, "I2_molecule")
    os.makedirs(d, exist_ok=True)
    write_poscar(os.path.join(d, "POSCAR"), mol, "I2 molecule in a box")
    write_kpoints(os.path.join(d, "KPOINTS"), (1, 1, 1), "Gamma point only")
    incar(os.path.join(d, "INCAR"), "I2 molecule, atoms relaxed in a fixed box",
          base_tags(".FALSE.") + ["Relaxation", ("IBRION", 2, ""), ("ISIF", 2, ""), ("NSW", 100, ""),
                                  ("EDIFFG", EDIFFG, "")] + para_tags(4, 1))
    rows.append("%-12s %3d atoms  Gamma  I-I 2.67 A, %.0f A box" % ("I2_molecule", 2, br.BOX))
    print("\n".join(rows))


# ---- step 8: CsI-terminated (001) slabs for the thickness test ----------------
SLAB_LAYERS = (7, 9, 11)
SLAB_VACUUM = 15.0               # A of vacuum between periodic copies
K_SLAB = (4, 4, 1)               # same in-plane density as the unit cell (4x4x3)


def build_slab(unit, nlayers, vacuum=SLAB_VACUUM):
    """Symmetric CsI-terminated (001) slab, 1x1 in-plane, nlayers odd.

    In the unit cell (c the long axis) the layers sit at z = 0 (PbI2), 1/4 (CsI),
    1/2 (PbI2), 3/4 (CsI). Layer k of the stacked cell is at z = k/4 (in units of c);
    CsI layers have odd k. The slab keeps layers 1 ... nlayers, so both faces are CsI.
    Both faces are equivalent by symmetry (checked with spglib: 7 and 11 layers have a
    PbI2 middle layer on Pb inversion centres, P2_1/c; 9 layers a CsI middle layer on the
    mirror plane), so there is no net dipole along the normal.
    """
    assert nlayers % 2 == 1
    reps = (nlayers + 1) // 4 + 1
    big = unit.repeat((1, 1, reps))
    c = unit.cell[2, 2]
    z = big.positions[:, 2] / c
    k = np.rint(z * 4).astype(int) % (4 * reps)
    keep = [i for i in range(len(big)) if 1 <= k[i] <= nlayers]
    slab = big[keep]
    slab.positions[:, 2] -= slab.positions[:, 2].min()
    thick = slab.positions[:, 2].max()
    cell = slab.cell.copy()
    cell[2] = [0, 0, thick + vacuum]
    slab.set_cell(cell)
    slab.positions[:, 2] += vacuum / 2
    return sort_atoms(slab), thick


def cmd_slab(a):
    unit = read(a.unit, format="vasp")
    out = os.path.join(HERE, "08_slab")
    os.makedirs(out, exist_ok=True)
    rows = ["CsI-terminated (001) slabs, 1x1 in-plane, built from %s" % a.unit,
            "in-plane cell fixed at the relaxed bulk a, b (%.4f x %.4f A); vacuum %.1f A"
            % (unit.cell[0, 0], unit.cell[1, 1], SLAB_VACUUM), ""]
    for n in (a.layers or SLAB_LAYERS):
        slab, thick = build_slab(unit, n)
        d = os.path.join(out, "L%02d" % n)
        os.makedirs(d, exist_ok=True)
        sym = slab.get_chemical_symbols()
        ncs, npb, ni = (sym.count(s) for s in ORDER)
        fu = npb                      # CsPbI3 units; the rest is CsI
        extra = ncs - npb
        assert ni == 3 * npb + extra, "not CsPbI3 + CsI"
        write_poscar(os.path.join(d, "POSCAR"), slab, "slab")
        write_kpoints(os.path.join(d, "KPOINTS"), K_SLAB, "Gamma-centred, 4x4 in-plane, 1 along the normal")
        incar(os.path.join(d, "INCAR"), "gamma-CsPbI3 (001) slab, CsI-terminated, %d layers" % n,
              base_tags(".FALSE.") + [
                  "Relaxation: atoms only, in-plane cell fixed at the bulk value",
                  ("IBRION", 2, "conjugate gradient"),
                  ("ISIF", 2, "fixed cell"),
                  ("NSW", 200, ""),
                  ("EDIFFG", EDIFFG, "eV/A, same force limit as QE"),
                  "Symmetric slab: no dipole correction needed"] + para_tags(10, 2))
        rows.append("L%02d: %d layers (%d CsI + %d PbI2), %3d atoms = %d CsPbI3 + %d CsI, "
                    "thickness %.2f A, c = %.2f A, NELECT %d"
                    % (n, n, (n + 1) // 2, (n - 1) // 2, len(slab), fu, extra, thick,
                       slab.cell[2, 2], nelect(slab)))
    rows += ["", "Check after the runs: E(L09) - E(L07) and E(L11) - E(L09) should both equal",
             "2 CsPbI3 of bulk (2 x E_unit / 4); the middle layer should match bulk Pb-I bonds and tilts."]
    name = "slabs_report.txt" if not a.layers else "slabs_report_L%s.txt" % "_".join("%02d" % n for n in a.layers)
    with open(os.path.join(out, name), "w") as f:
        f.write("\n".join(rows) + "\n")
    print("\n".join(rows))


# ---- step 9 (first test): +1 vacancies at the centre of a 2x2 slab ---------------
K_SLAB_2X2 = (2, 2, 1)


def cmd_slabvac(a):
    """2x2 in-plane copy of a relaxed 1x1 slab, plus +1 iodine vacancies at its centre.

    The centre test of hypothesis H5: the 8d (equatorial) iodine of the PbI2 layer and the
    4c (apical) iodine of the CsI layer closest to the slab centre, each nearest the cell
    centre in the plane. Their energy difference (and later the barriers between them) is
    compared with the bulk; no chemical potential or charge correction enters a difference
    between two +1 cells of the same slab.
    """
    slab = sort_atoms(read(a.slab))
    n = int(round(len(slab) / 1))
    sc = sort_atoms(slab.repeat((2, 2, 1)))
    sym = np.array(sc.get_chemical_symbols())
    z = sc.positions[:, 2]

    def layer_z(el):
        zz = np.sort(z[sym == el])
        g = [[zz[0]]]
        for v in zz[1:]:
            (g[-1].append(v) if v - g[-1][-1] < 1.0 else g.append([v]))
        return [np.mean(x) for x in g]

    zpb, zcs = layer_z("Pb"), layer_z("Cs")
    zmid = (min(zpb + zcs) + max(zpb + zcs)) / 2
    lpb = min(zpb, key=lambda v: abs(v - zmid))
    lcs = min(zcs, key=lambda v: abs(v - zmid))
    xy = sc.cell.array[:2].sum(axis=0)[:2] / 2
    out = os.path.join(HERE, "09_slab_vacancies", a.name)
    rep = ["Slab: %s repeated 2x2x1, %d atoms, cell %.4f %.4f %.4f A, k-mesh %d %d %d (Gamma)"
           % (a.slab, len(sc), *sc.cell.lengths(), *K_SLAB_2X2),
           "Slab centre z = %.3f A; middle PbI2 layer z = %.3f, nearest CsI layer z = %.3f" % (zmid, lpb, lcs), ""]
    d = os.path.join(out, "pristine")
    os.makedirs(d, exist_ok=True)
    write_poscar(os.path.join(d, "POSCAR"), sc, "slab 2x2")
    write_kpoints(os.path.join(d, "KPOINTS"), K_SLAB_2X2, "Gamma-centred, 2x2 in-plane, 1 along the normal")
    defect_incar(os.path.join(d, "INCAR"), "%s pristine 2x2 slab" % a.name, "", None, 0)
    for name, lz in (("vac_I_8d_centre", lpb), ("vac_I_4c_centre", lcs)):
        cand = np.where((sym == "I") & (np.abs(z - lz) < 1.0))[0]
        i = cand[np.argmin(np.linalg.norm(sc.positions[cand, :2] - xy, axis=1))]
        vac = sc.copy()
        del vac[i]
        d = os.path.join(out, "q+1", name)
        os.makedirs(d, exist_ok=True)
        write_poscar(os.path.join(d, "POSCAR"), vac, "%s %s q+1" % (a.name, name))
        write_kpoints(os.path.join(d, "KPOINTS"), K_SLAB_2X2, "Gamma-centred, 2x2 in-plane, 1 along the normal")
        ne = nelect(vac, 1)
        defect_incar(os.path.join(d, "INCAR"), "%s %s, charge +1" % (a.name, name), "+1, %d electrons" % ne, ne, 0)
        rep.append("%s: removed atom %d (POSCAR order) at (%.3f, %.3f, %.3f) A, %.2f A from the slab centre; NELECT %d"
                   % (name, i + 1, *sc.positions[i], abs(sc.positions[i, 2] - zmid), ne))
    rep += ["", "Compare E(8d) - E(4c) with the bulk (VASP +0.9 meV, QE -1.06 meV); then the centre barriers.",
            "Charged slab: VASP adds a compensating background; the vacancies sit at the centre, so the",
            "background term is nearly the same for both and cancels in the difference."]
    with open(os.path.join(out, "report.txt"), "w") as f:
        f.write("\n".join(rep) + "\n")
    print("\n".join(rep))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("unitcell")
    p.add_argument("--start", default="qe/01_unitcell/gamma_CsPbI3_vcrelax.in",
                   help="start structure (default: the same experimental start as the QE runs)")
    p = sub.add_parser("supercell")
    p.add_argument("--unit", required=True, help="relaxed VASP unit cell (CONTCAR)")
    sub.add_parser("refs")
    p = sub.add_parser("slab")
    p.add_argument("--unit", default="vasp/01_unitcell/relax/CONTCAR", help="relaxed VASP unit cell (CONTCAR)")
    p.add_argument("--layers", type=int, nargs="+", help="odd layer counts (default 7 9 11)")
    p = sub.add_parser("slabvac")
    p.add_argument("--slab", default="vasp/08_slab/L11/CONTCAR", help="relaxed 1x1 slab (CONTCAR)")
    p.add_argument("--name", default="L11_2x2")
    a = ap.parse_args()
    if a.cmd == "slabvac":
        return cmd_slabvac(a)
    {"unitcell": cmd_unitcell, "supercell": cmd_supercell, "refs": cmd_refs, "slab": cmd_slab}[a.cmd](a)


if __name__ == "__main__":
    main()
