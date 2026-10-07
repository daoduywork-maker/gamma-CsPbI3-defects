# gamma-CsPbI3-defects

First-principles study of iodine defect migration in orthorhombic γ-CsPbI₃, using Quantum ESPRESSO.

This repository holds the inputs, scripts and text outputs. Scratch data (wavefunctions, charge densities) is not tracked.

## Status

| Stage | State |
|---|---|
| Convergence test (k-points, cutoff) | Done |
| Soft relaxation of the 20-atom unit cell | Done |
| Defect supercell, vacancy and hop inputs | Built from the soft-relaxed cell; to be rebuilt after the tight relaxation |
| Cluster setup (job script, pseudopotentials, modules) | Done |
| Tight relaxation of the unit cell | Submitted on the cluster, waiting in the queue |
| Perfect supercell and vacancy relaxations | To do |
| Migration barriers (NEB) | To do; `neb.x` is not yet installed on the cluster |
| Interstitial, surface slab, machine-learned potential | Later stages |

## The material: γ-CsPbI₃

### What it is

CsPbI₃ is a halide perovskite with the formula ABX₃. Each Pb atom sits at the centre of an octahedron of six iodine atoms. The octahedra share corners and form a three-dimensional network, and the Cs atoms fill the cavities between them.

The compound exists in several phases:

| Phase | Structure | Notes |
|---|---|---|
| α | Cubic perovskite, octahedra not tilted | Stable only at high temperature |
| β | Tetragonal perovskite, tilted about one axis | Intermediate, on cooling from α |
| γ | Orthorhombic perovskite, tilted about all three axes | The black perovskite phase found at room temperature; metastable |
| δ | Orthorhombic, not a perovskite (yellow) | The stable phase at room temperature; poor light absorber |

The γ phase is the one used in solar cells and light emitters, with a band gap of about 1.7 eV.

### Why γ and not the cubic α phase

At zero temperature the cubic structure is not a minimum of the energy: the octahedra lower their energy by tilting. A relaxation without thermal motion, such as the calculations here, therefore belongs to the γ structure. It is also the perovskite phase present in devices at room temperature.

### The structure

![Top and side views of the relaxed γ-CsPbI₃ lattice](assets/gamma_CsPbI3_lattice_tilted_octahedra.png)

The figure is drawn from the relaxed structure in `final/`. The top view shows one layer of octahedra (Pb with its four in-plane iodine atoms) and the Cs atoms above it; the octahedra are rotated about c, in opposite senses for neighbours. The side view shows one sheet of octahedra seen along the in-plane diagonal; the Pb–I–Pb links along c are bent instead of straight.

| Property | Value (this work, PBEsol) |
|---|---|
| Space group | Pnma (No. 62), written here in the Pbnm setting with c as the long axis |
| Atoms per unit cell | 20 (4 Cs, 4 Pb, 12 I) |
| Lattice parameters | a = 8.378 Å, b = 8.933 Å, c = 12.352 Å |
| Pb–I bond lengths | 3.17 to 3.19 Å |
| Pb–I–Pb angles | 148° to 154° (180° in the cubic phase) |
| Iodine sites | 4 apical (linking octahedra along c) and 8 equatorial (linking them within the ab plane) |

The tilting is what makes the two iodine sites different, and it is the reason the defect study below treats apical and equatorial positions separately.

## Defect study: what we are going to do

### The two iodine sites

![Apical and equatorial iodine vacancies around one Pb atom](assets/iodine_vacancy_sites_apical_vs_equatorial.png)

Each Pb atom sits at the centre of an octahedron of six iodine atoms. In γ-CsPbI₃ the octahedra are tilted, so the six are not all equivalent:

- **Apical** iodine: the two above and below Pb, along the c axis.
- **Equatorial** iodine: the four around Pb, in the plane perpendicular to c.

Removing one iodine leaves a vacancy. Because the two sites are different, an apical vacancy and an equatorial vacancy can have different energies, and a vacancy can move by two kinds of nearest-neighbour hop along an octahedron edge: apical ↔ equatorial and equatorial ↔ equatorial (4.4 to 4.6 Å, listed under Results).

### Questions

1. Which site does the vacancy prefer, and by how much?
2. How high is the energy barrier for each kind of hop? The lowest barriers set how fast iodine moves through the crystal.
3. Do the answers change close to a surface, layer by layer?

### Steps

| Step | Calculation | Result |
|---|---|---|
| 1 | Tight relaxation of the 20-atom cell: forces below 0.010 eV/Å (4×10⁻⁴ Ry/Bohr), pressure below 0.2 kbar | Reference lattice for everything that follows |
| 2 | Build the 2×2×2 supercell (160 atoms) and relax its atoms at fixed cell | Energy of the perfect crystal |
| 3 | Remove one apical iodine, or one equatorial iodine, and relax. Charge +1 first, neutral afterwards | Energy difference between the two vacancy sites |
| 4 | For each distinct hop, relax the start and end structures, then find the path between them with the nudged elastic band (NEB) method | Migration barrier of each hop in the bulk |
| 5 | Repeat steps 3 and 4 for an extra iodine atom (interstitial) | The same quantities for the second mobile defect |
| 6 | Build a slab with the CsI-terminated (001) surface and repeat for defects at increasing depth | Site energies and barriers as a function of distance from the surface |
| 7 | Train a machine-learned interatomic potential on these calculations | Hop rates at finite temperature, larger cells, longer times |

One defect is placed in each supercell. The cell is kept fixed in all defect calculations, so every energy is compared with the same perfect supercell.

### Where this sits in the literature

- Vacancy migration at surfaces has been computed for CsPbBr₃, where the barrier at the surface is about half the bulk value (Biega and Leppert, J. Phys.: Energy 3, 2021).
- Ion migration in bulk γ-CsPbI₃ has been studied with ab initio and machine-learning methods (Chem. Mater. 37, 4416, 2025).
- Formation energies of iodine vacancies and interstitials as a function of depth below the (001) surface of orthorhombic CsPbI₃ have been reported, without migration barriers (Ahmad, Limon and Ahmad, Phys. Rev. Materials 8, 125402, 2024).

The aim here is the piece these leave open: migration barriers as a function of depth below the surface in γ-CsPbI₃. Steps 1 to 4 reproduce bulk values and serve as the reference and as a check against published numbers.

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
├── defects/                     everything that script wrote
│
├── run_qe.pbs                   job script for the cluster queue
└── assets/                      figures used in this README
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
| `run_qe.pbs` | PBS job script for the cluster: loads the modules and runs `pw.x` on one 40-core node. Submit it from the folder that holds the input, for example `qsub -N pristine -v INPUT=relax.in,NK=2 run_qe.pbs`. |

### Folders

| Folder | Contents |
|---|---|
| `conv/` | `k221`, `k332`, `k443`, `k554`, `k664`: k-mesh series at 50 Ry. `e40` to `e80`: cutoff series at 4×4×3. Each has an `.in` and an `.out`. |
| `stage1_k332/` | `vcrelax.in` and `vcrelax.out` for stage 1. The output contains every geometry step. |
| `stage2_k443/` | The same for stage 2, which started from the stage 1 result. |
| `final/` | `gamma_CsPbI3_relaxed_scf.in`: complete input with the relaxed structure. `structure_blocks.txt`: cell and positions only. `gamma_CsPbI3_relaxed.cif`: for viewing. |
| `defects/` | See below. |
| `assets/` | `gamma_CsPbI3_lattice_tilted_octahedra.png`: top and side views of the relaxed lattice. `iodine_vacancy_sites_apical_vs_equatorial.png`: sketch of the two vacancy sites. |

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
| Code | Quantum ESPRESSO `pw.x`: version 7.6 on the laptop (convergence test, soft relaxation), version 6.5 on the cluster (tight relaxation and all defect calculations) |
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

1. Tight relaxation of the unit cell (`defects/unitcell_tight`) on the cluster, then rebuild `defects/` from its result.
2. Relax the perfect supercell and the two +1 vacancies.
3. Get `neb.x` on the cluster, relax the end points of one hop and run a trial NEB.
4. Remaining hops, neutral charge state, interstitial, then the surface slab.