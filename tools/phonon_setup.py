#!/usr/bin/env python3
"""
Phonopy finite-displacement inputs for gamma and delta CsPbI3 at 0 and +-1% strain (step 10).
Reads vasp/10_phonons/<phase>/eps<e>/relax/CONTCAR (tight relaxations), writes
vasp/10_phonons/<phase>/eps<e>/phonopy_disp.yaml and disp-NNN/{POSCAR,INCAR,KPOINTS}.
Supercells: gamma 2x2x1 (80 atoms, k 2x2x3), delta 3x2x1 (120 atoms, k 3x2x2); displacement 0.01 A.
Chains for run_multi: vasp/chains_phonon_probe.txt (one displacement per phase), vasp/chains_phonon.txt.
"""
import os
from phonopy import Phonopy
from phonopy.interface.calculator import read_crystal_structure, write_crystal_structure

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vasp")
SET = {"gamma": ([2, 2, 1], (2, 2, 3)), "delta": ([3, 2, 1], (3, 2, 2))}
INCAR = """SYSTEM = {title}
GGA      = PS              ! PBEsol
PREC     = Accurate
ENCUT    = 500
LASPH    = .TRUE.
LREAL    = .FALSE.         ! exact projectors for accurate forces
ADDGRID  = .TRUE.
ALGO     = Normal
NELM     = 200
EDIFF    = 1E-8
ISMEAR   = 0
SIGMA    = 0.01
IBRION   = -1
NSW      = 0
LWAVE    = .FALSE.
LCHARG   = .FALSE.
NCORE    = 10
KPAR     = 2
"""
chains = {}
for ph, (sc, k) in SET.items():
    for e in ("eps-1.0", "eps+0.0", "eps+1.0"):
        base = os.path.join(ROOT, "10_phonons", ph, e)
        u, _ = read_crystal_structure(os.path.join(base, "relax", "CONTCAR"), interface_mode="vasp")
        p = Phonopy(u, supercell_matrix=sc, primitive_matrix="P")
        p.generate_displacements(distance=0.01)
        p.save(os.path.join(base, "phonopy_disp.yaml"))
        dirs = []
        for n, cell in enumerate(p.supercells_with_displacements, 1):
            d = os.path.join(base, "disp-%03d" % n)
            os.makedirs(d, exist_ok=True)
            write_crystal_structure(os.path.join(d, "POSCAR"), cell, interface_mode="vasp")
            open(os.path.join(d, "INCAR"), "w").write(INCAR.format(title="%s %s phonon displacement %d" % (ph, e, n)))
            open(os.path.join(d, "KPOINTS"), "w").write("Gamma-centred\n0\nGamma\n%d %d %d\n" % k)
            dirs.append(os.path.relpath(d, ROOT))
        chains[(ph, e)] = dirs
        print(ph, e, len(dirs), "displacements")
open(os.path.join(ROOT, "chains_phonon_probe.txt"), "w").write(
    chains[("gamma", "eps+0.0")][0] + "\n" + chains[("delta", "eps+0.0")][0] + "\n")
allg = [d for (ph, e), v in chains.items() if ph == "gamma" for d in v]
alld = [d for (ph, e), v in chains.items() if ph == "delta" for d in v]
everything = allg + alld
lines = [everything[i::4] for i in range(4)]
open(os.path.join(ROOT, "chains_phonon.txt"), "w").write("\n".join(" ".join(l) for l in lines) + "\n")
print("chains:", [len(l) for l in lines])
