# VASP counterpart of the QE workflow

Every step done so far in Quantum ESPRESSO, repeated in VASP with the same physics, so that the two codes cross-check each other and the barriers can be compared one-to-one with Arber 2025 (VASP, PBEsol, 500 eV).

| | QE (done) | VASP (this folder) |
|---|---|---|
| Functional | PBEsol | PBEsol (`GGA = PS`) |
| Potentials | SSSP 1.3.0 (Cs US, Pb/I PAW) | PAW `Cs_sv`, `Pb_d`, `I` |
| Cutoff | 60 / 480 Ry | 500 eV (`PREC = Accurate`, `LASPH`) |
| k-meshes | 4×4×3 unit cell, 2×2×2 supercell | same, Γ-centred (same points as QE's unshifted meshes) |
| Force limit | 4×10⁻⁴ Ry/Bohr | `EDIFFG = -0.01` eV/Å (the same) |
| Charge +1 | `tot_charge = 1` | `NELECT = 1400` (159-atom cell: 1401 − 1) |
| Neutral | `nspin = 2` | `ISPIN = 2`, small start moments |
| NEB | neb.x, 4 moving images, CI | VTST: `IMAGES = 4`, `LCLIMB`, FIRE (`IOPT = 3`) |
| Vacancy sites | 4c / 8d iodine nearest the cell centre | the same two sites (checked: same coordinates) |

One VASP build for everything: `vasp/vasp632vtst` (NEB needs VTST).

## Order of work

| Step | Folder | Built by | Run | Needs |
|---|---|---|---|---|
| V1a | `01_unitcell/conv/` (7 cutoffs, 5 k-meshes) | `build_vasp.py unitcell` | 1 node, one job, `DIRS=...` | — |
| V1b | `01_unitcell/relax/` | `build_vasp.py unitcell` | 1 node, `STAGES=2` | — |
| V5 | `05_reference_phases/` (6 phases) | `build_vasp.py refs` | 1 node, one job, `DIRS=...` | — |
| V2–V3 | `02_pristine/`, `03_vacancies/q+1`, `q0` | `build_vasp.py supercell --unit 01_unitcell/relax/CONTCAR` | 4 nodes each | V1b CONTCAR |
| V4 | `04_bulk_neb/q+1/S1, S2, L3, S6` | `tools/build_neb.py S1 --charge q+1 --code vasp` | 4 nodes (1 image per node) | V3 CONTCARs |
| V8 | `07_slab/L07, L09, L11` (CsI-terminated (001), 1×1 in-plane, 34/44/54 atoms) | `build_vasp.py slab` | 1 node, one job, `DIRS=...` | V1b CONTCAR |

V1 and V5 are built and can run now. V2–V4 are built when the relaxed files come back (the cluster has no Python).

## Cluster commands

Copy the `vasp` folder to `~/cspbi3/vasp` (drag and drop), then:

```bash
module avail vasp; module show vasp/vasp632vtst      # once: check the module and the name of vasp_std
cd ~/cspbi3/vasp
B=~/cspbi3/vasp

# POTCARs for every folder with a POSCAR
bash $B/make_potcar.sh 01_unitcell/conv/* 01_unitcell/relax 05_reference_phases/*

# V1a: convergence tests, one job, one after the other
cd 01_unitcell/conv && qsub -N v_conv -l nodes=1:ppn=40 -l walltime=48:00:00 \
   -v DIRS="$(ls -d */ | tr '\n' ' ')" $B/run_vasp.pbs && cd -
# V1b: variable-cell relaxation, restarted once from CONTCAR
cd 01_unitcell/relax && qsub -N v_unit -l nodes=1:ppn=40 -l walltime=48:00:00 -v STAGES=2 $B/run_vasp.pbs && cd -
# V5: reference phases, one job
cd 05_reference_phases && qsub -N v_refs -l nodes=1:ppn=40 -l walltime=24:00:00 \
   -v DIRS="Cs Pb I2 CsI PbI2 I2_molecule" $B/run_vasp.pbs && cd -
```

Supercells and NEB (after V2–V4 are built): `bash $B/make_potcar.sh <folder>`, then `qsub -N <name> $B/run_vasp.pbs` from the folder (default 4 std40 nodes, 360 h). Watch `mem.log` in the first 10 minutes.

## Memory (check before every large job)

Small cells (V1, V5): a few GB. Supercells: estimated 30–60 GB in total for +1 and roughly twice that for the spin-polarised neutral cells, i.e. well inside 4 × 75 GB; VASP needs far less than QE here (no 480 Ry density grid). NEB: each image runs on its own node (160 cores / 4 images), so per node ≈ one supercell. These are estimates: the first job of each kind is the measurement (`mem.log`, and `Maximum memory used` at the end of OUTCAR).

## What to compare with QE

| Quantity | QE value |
|---|---|
| Relaxed unit cell a, b, c | 8.362, 8.961, 12.350 Å |
| E(8d) − E(4c), charge +1 | −1.06 meV (8d lower) |
| E(8d) − E(4c), neutral | +40.4 meV (4c lower) |
| Neutral cells | 0 μB, shallow donor |
| ΔH_f CsI, PbI₂, CsPbI₃ | −3.09, −1.84, −4.99 eV/f.u.; CsPbI₃ stable vs CsI + PbI₂ by 63 meV |
| Barriers S1, S2, L3, S6 (+1) | pending in QE |
