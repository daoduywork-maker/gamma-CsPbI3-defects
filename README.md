# gamma-CsPbI3-defects

First-principles study of iodine defect migration in orthorhombic γ-CsPbI₃, using Quantum ESPRESSO.

This repository holds the inputs, scripts and text outputs. Scratch data (wavefunctions, charge densities) is not tracked.

## Status

| Stage | State |
|---|---|
| Convergence test (k-points, cutoff) | Done |
| Soft relaxation of the 20-atom unit cell | Done |
| Defect supercell, vacancy and hop inputs | Built, not yet run |
| Tight relaxation, defect energies, NEB barriers | To do, on the cluster |

## File structure

```
.
├── README.md                    this file
├── LICENSE                      licence for the repository
│
├── gamma_CsPbI3_vcrelax.in      base input: experimental γ-CsPbI₃ cell (20 atoms) and settings
│
├── kconv.sh                     runs the convergence test
├── conv/                        its inputs and outputs, one pair per setting
├── conv_summary.txt             energies from the convergence test
│
├── relax2stage.sh               runs the two-stage variable-cell relaxation
├── stage1_k332/                 stage 1: relaxation at the coarse 3×3×2 k-mesh
├── stage2_k443/                 stage 2: relaxation at the converged 4×4×3 k-mesh
├── final/                       the relaxed structure, ready to use
├── relax_summary.txt            report of the relaxation
│
├── build_defects.py             builds the supercell, vacancy and hop inputs
└── defects/                     everything that script wrote
```

### Top-level files

| File | Purpose |
|---|---|
| `gamma_CsPbI3_vcrelax.in` | Starting point for everything. Holds the experimental room-temperature structure (Sutton et al., ACS Energy Lett. 2018) and the calculation settings. Both shell scripts read it and neither changes it. |
| `kconv.sh` | Makes copies of the base input as single-point calculations with different k-meshes and cutoffs, runs them, and prints the energy per atom for each. |
| `conv_summary.txt` | The table printed by `kconv.sh`. |
| `relax2stage.sh` | Relaxes the cell and atoms in two stages (coarse mesh, then converged mesh), exports the result to `final/`, and writes `relax_summary.txt`. |
| `relax_summary.txt` | Energies, pressure, forces and timing for each stage; lattice parameters compared with experiment; Pb–I–Pb angles before and after. |
| `build_defects.py` | Reads a relaxed unit cell and writes the inputs for the defect calculations. Does no physics calculation itself. |

### Folders

| Folder | Contents |
|---|---|
| `conv/` | `k221`, `k332`, `k443`, `k554`, `k664`: k-mesh series at 50 Ry. `e40` to `e80`: cutoff series at 4×4×3. Each has an `.in` and an `.out`. |
| `stage1_k332/` | `vcrelax.in` and `vcrelax.out` for stage 1. The output contains every geometry step. |
| `stage2_k443/` | The same for stage 2, which started from the stage 1 result. |
| `final/` | `gamma_CsPbI3_relaxed_scf.in`: complete input with the relaxed structure. `structure_blocks.txt`: cell and positions only. `gamma_CsPbI3_relaxed.cif`: for viewing. |
| `defects/` | See below. |

### Inside `defects/`

```
defects/
├── sites_report.txt             which atoms were removed, and every hop distance
├── unitcell_tight/vcrelax.in    tight relaxation of the 20-atom cell
├── pristine_222/relax.in        perfect 2×2×2 supercell (160 atoms), the energy reference
├── q+1/                         defects with charge +1
│   ├── vac_I_apical/relax.in        vacancy on an apical iodine site
│   ├── vac_I_equatorial/relax.in    vacancy on an equatorial iodine site
│   └── hop_<from>_to_<to>_<d>A/     one folder per distinct vacancy hop
│       ├── initial.in               vacancy at the first site
│       └── final.in                 neighbouring iodine moved in; vacancy at the second site
└── q0/                          the same structures, neutral and spin-polarised
```

Every input has a `.cif` beside it for viewing.

Apical iodine links two Pb atoms along the long c axis. Equatorial iodine lies in the Pb–I plane. The two are different sites in the γ phase because of the octahedral tilting.

## Settings

| Item | Value |
|---|---|
| Code | Quantum ESPRESSO 7.6, `pw.x` |
| Functional | PBEsol |
| Pseudopotentials | SSSP 1.3.0 PBEsol efficiency |
| Plane-wave cutoff | 60 Ry (density 480 Ry) |
| k-mesh, 20-atom cell | 4×4×3 |
| k-mesh, 160-atom supercell | 2×2×2 |

Pseudopotential files:

| Element | File |
|---|---|
| Cs | `cs_pbesol_v1.uspp.F.UPF` |
| Pb | `Pb.pbesol-dn-kjpaw_psl.0.2.2.UPF` |
| I | `I.pbesol-n-kjpaw_psl.0.2.UPF` |

## Results so far

### Convergence

| k-mesh (50 Ry) | Energy above 6×6×4 (meV/atom) |
|---|---|
| 2×2×1 | 45.46 |
| 3×3×2 | 2.52 |
| 4×4×3 | 0.23 |
| 5×5×4 | 0.004 |

| Cutoff (4×4×3) | Energy above 80 Ry (meV/atom) | Pressure (kbar) |
|---|---|---|
| 40 Ry | 5.83 | −1.89 |
| 50 Ry | 3.29 | −1.57 |
| 60 Ry | 0.86 | −1.48 |
| 70 Ry | 0.40 | −1.35 |
| 80 Ry | 0 | −1.39 |

### Relaxed unit cell

| | a (Å) | b (Å) | c (Å) | Volume (Å³) |
|---|---|---|---|---|
| Experiment, 293 K | 8.5766 | 8.8561 | 12.4722 | 947.33 |
| This work, 0 K | 8.3776 | 8.9330 | 12.3518 | 924.38 |
| Difference | −2.32% | +0.87% | −0.97% | −2.42% |

| | Pb–I–Pb angles | Pb–I bond lengths (Å) |
|---|---|---|
| Experiment, 293 K | 150.84° to 160.63° | 3.148 to 3.221 |
| This work, 0 K | 148.09° to 153.54° | 3.172 to 3.188 |

This is a soft relaxation: forces to 10⁻³ Ry/Bohr (0.026 eV/Å), pressure to 0.5 kbar. Stage 1 took 37 energy evaluations and 13 h 54 min; stage 2 took 3 evaluations and 2 h 30 min, on a 6-core laptop.

### Vacancy hops identified

| Hop | Distance (Å) |
|---|---|
| Apical ↔ equatorial | 4.44, 4.45, 4.55 |
| Equatorial ↔ equatorial | 4.42, 4.59 |

Hops are grouped by type and by distance rounded to 0.01 Å, so two different hops of nearly equal length may be merged. This needs checking before the full set of barriers is computed.

## How to reproduce

```bash
# 1. convergence test
bash kconv.sh | tee conv_summary.txt

# 2. two-stage relaxation
bash relax2stage.sh

# 3. defect inputs
python3 build_defects.py final/gamma_CsPbI3_relaxed_scf.in --pseudo-dir /path/to/pseudo
```

Set `PW` (path to `pw.x`) and `NP` (number of MPI processes) at the top of each shell script. Set `pseudo_dir` in `gamma_CsPbI3_vcrelax.in`. `build_defects.py` needs Python 3 with NumPy and ASE.

## Not tracked

Listed in `.gitignore`:

- `tmp/` and `*.save/`: Quantum ESPRESSO scratch data
- `*.wfc*`, `*.xml`: wavefunctions and data files
- `backup/`, `*:Zone.Identifier`, `__pycache__/`

## Next steps

1. Tight relaxation of the unit cell (`defects/unitcell_tight`), then rebuild `defects/` from its result.
2. Relax the perfect supercell and the two +1 vacancies.
3. Relax the end points of one hop and run a trial NEB.
4. Remaining hops, neutral charge state, then the surface slab.