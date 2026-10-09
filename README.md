# gamma-CsPbI3-defects

First-principles study of iodine defect migration in orthorhombic γ-CsPbI₃, using Quantum ESPRESSO.

This repository holds the inputs, scripts and text outputs. Scratch data (wavefunctions, charge densities) is not tracked.

## Status

| Stage | State |
|---|---|
| Convergence test, soft and tight relaxation of the unit cell | Done |
| Cluster setup; `neb.x` and `pp.x` compiled (Quantum ESPRESSO 6.5) | Done |
| Perfect supercell and vacancy relaxations (5 jobs) | On the cluster |
| Set of distinct bulk hops | Settled: 10 (6 short, 4 long) |
| Hop end points and NEB inputs (`build_neb.py`) | To do |
| Bulk barriers (NEB) | To do |
| CsI-terminated slab: vacancies and barriers against depth | To do |

## Introduction

### γ-CsPbI₃

CsPbI₃ is a halide perovskite with the formula ABX₃. Each Pb atom sits at the centre of an octahedron of six iodine atoms. The octahedra share corners and form a three-dimensional network, and the Cs atoms fill the cavities between them.

The compound exists in several phases:

| Phase | Structure | Notes |
|---|---|---|
| α | Cubic perovskite, octahedra not tilted | Stable only at high temperature |
| β | Tetragonal perovskite, tilted about one axis | Intermediate, on cooling from α |
| γ | Orthorhombic perovskite, tilted about all three axes | The black perovskite phase found at room temperature; metastable |
| δ | Orthorhombic, not a perovskite (yellow) | The stable phase at room temperature; poor light absorber |

The γ phase is the one used in solar cells and light emitters, with a band gap of about 1.7 eV.

At zero temperature the cubic structure is not a minimum of the energy: the octahedra lower their energy by tilting. A relaxation without thermal motion, such as the calculations here, therefore belongs to the γ structure. It is also the perovskite phase present in devices at room temperature.

![Top and side views of the relaxed γ-CsPbI₃ lattice](assets/gamma_CsPbI3_lattice_tilted_octahedra.png)

The figure is drawn from the soft-relaxed structure in `01_unitcell/final/`; the tight relaxation changes it by less than 0.03 Å, which is not visible at this scale. The top view shows one layer of octahedra (Pb with its four in-plane iodine atoms) and the Cs atoms above it; the octahedra are rotated about c, in opposite senses for neighbours. The side view shows one sheet of octahedra seen along the in-plane diagonal; the Pb–I–Pb links along c are bent instead of straight.

| Property | Value (this work, PBEsol) |
|---|---|
| Space group | Pnma (No. 62), written here in the Pbnm setting with c as the long axis |
| Atoms per unit cell | 20 (4 Cs, 4 Pb, 12 I) |
| Lattice parameters | a = 8.362 Å, b = 8.961 Å, c = 12.350 Å |
| Pb–I bond lengths | 3.17 to 3.19 Å |
| Pb–I–Pb angles | 148° (equatorial) and 155° (apical); 180° in the cubic phase |
| Iodine sites | 4 apical (linking octahedra along c) and 8 equatorial (linking them within the ab plane) |

The tilting is what makes the two iodine sites different, and it is the reason the defect study below treats apical and equatorial positions separately.

### Defect - The two iodine sites

![Apical and equatorial iodine vacancies around one Pb atom](assets/iodine_vacancy_sites_apical_vs_equatorial.png)

Each Pb sits at the centre of an octahedron of six iodines. Because the octahedra are tilted, the six are not all equivalent:

- **Apical (4c)**: the two above and below Pb, along c, in the CsI layers.
- **Equatorial (8d)**: the four around Pb, in the PbI₂ layers.

### Why defects matter

Halide perovskites tolerate defects electronically: most native defects leave no deep trap states, which is why solution-processed films still perform well. Their weak point is ionic. Iodine vacancies form easily and move at room temperature, and moving ions cause:

- current–voltage hysteresis and slow, drifting response in solar cells and detectors;
- ions piling up at interfaces and reacting with contacts;
- loss of stability, including the change of γ-CsPbI₃ to the yellow δ phase, which tends to start at surfaces and grain boundaries.

Surfaces are where vacancies form, collect and escape, and where the perovskite meets the other device layers. How fast vacancies move near the surface, and whether they are drawn to it, guides surface passivation and interface design.

## Literature review

Full notes, numbers and sources: [`Literatures/literature_review.md`](Literatures/literature_review.md).

| Paper | What it did | What it leaves open |
|---|---|---|
| **Arber 2025** (anchor) | Bulk γ-CsPbI₃, PBEsol, 2×2×2 supercell: iodine vacancy barriers 0.34 eV (8d-8d), 0.35 eV (8d-4c), about 0.77 eV (4c-4c); MD activation energy 0.42 eV | Surfaces; more than one barrier per type of path; the charge state |
| Biega 2021 | Cubic CsPbBr₃ slabs: the long axial-to-axial barrier is about half the bulk value at the surface | Edge hops; the tilted phase; a slab whose barriers return to the bulk value |
| Ahmad 2024 | Orthorhombic CsPbI₃ 17-layer slabs: vacancy and interstitial formation energies against depth | Barriers; a slab interior that matches its own bulk (off by 0.05 to 0.66 eV) |

### The gap

One point per paper:

- **Arber 2025** gives one barrier per type of path, although the tilted structure has several distinct variants of each, and does not state the charge state.
- **Biega 2021** shows a surface effect for one long jump only, in the cubic bromide, in a thin, partly frozen slab that never returns to the bulk.
- **Ahmad 2024** has the right material and surface, but only formation energies, and its slab interior does not reproduce its bulk.

**Overall gap:** nobody has computed iodine vacancy migration barriers in γ-CsPbI₃ layer by layer below the surface, in a slab whose interior reproduces the bulk.

This appears as three specific gaps:

| Gap | Statement |
|---|---|
| **G1 — Hop resolution** | Bulk barriers are known only per type of path. The tilted structure has 10 symmetry-distinct hops (6 short, 4 long), and which charge state the published values belong to is not stated. |
| **G2 — Depth** | The surface effect on vacancy migration is known for one long jump in cubic CsPbBr₃ only. For γ-CsPbI₃ there are no barriers against depth, and how deep the surface reaches is unknown. |
| **G3 — Slab–bulk consistency** | Neither surface study recovers its own bulk inside the slab, so surface and bulk values cannot be compared cleanly. |

### Research questions

| | Question | Gap | Hypothesis |
|---|---|---|---|
| **RQ1** | Which site does the vacancy prefer, and by how much, in each charge state? | G1 | **H1.** 8d by a few hundredths of an eV in both; one charge state reproduces paper A's +0.03 eV. |
| **RQ2** | What are the barriers of the 10 distinct bulk hops? | G1 | **H2.** Variants of one type differ by up to about 0.1 eV, rising with hop length; long hops are clearly higher. |
| **RQ3** | How do site energies and barriers change layer by layer below the CsI-terminated surface? | G2 | **H3.** Barriers drop and the vacancy is slightly more stable in the top layers; the effect fades within two to three layers (about 1 nm). |
| **RQ4** | Once the surface splits each pair of equivalent hops, which direction is favoured? | G2 | **H4.** Hops towards the surface are easier, giving a net drift of vacancies to the surface. |
| **RQ5** | Does the middle of the slab reproduce the bulk site energy and barrier? | G3 | **H5.** Yes, within about 0.02 eV, for a symmetric 11-layer slab with all atoms free. |

**Novelty**

| | Contribution | Gap |
|---|---|---|
| **N1** | All 10 symmetry-distinct bulk hops, with both charge states stated | G1 |
| **N2** | First depth-resolved vacancy barriers in γ-CsPbI₃, followed back to the bulk | G2 |
| **N3** | The surface splitting of equivalent hops as a measure of directional drift | G2 |
| **N4** | A slab checked against its own bulk reference | G3 |

Limits on the novelty claim: a web search and a cited-by check of papers A, B and C (October 2026, Google Scholar and the publishers' "cited by" lists) found no depth-resolved vacancy barriers in γ-CsPbI₃. The closest work: Pols 2022 (reactive MD of CsPbI₃ slabs; iodine vacancies seen moving in and out of the surface, no barriers), surface studies of CsPbI₃ with formation energies only (Li et al., arXiv 2411.01599; arXiv 2309.04870), and bulk-only migration studies (Tyagi et al., arXiv 2409.16051; Miskin 2025). Paper C's group (Ahmad) works on defect mobility near interfaces in other materials and is the most likely to extend C to barriers.

**If the hypotheses fail.** If H3 is false (no change below the top layer), the surface effect is confined to one layer; that still answers G2. If H5 is false, comparing the neutral and +1 vacancy separates a structural mismatch from a charge-referencing one; that answers G3.

### Scope

The scope is exactly what G1–G3 require.

| In scope | Needed for |
|---|---|
| Bulk 4c and 8d vacancy, charge +1 and neutral: site energies | G1 |
| NEB for the 10 distinct bulk hops | G1 |
| CsI-terminated (001) slab: site energies and hops layer by layer, down to the bulk-like middle | G2 |
| Middle-layer site energy and barrier against the bulk; 15-layer thickness test | G3 |

**Settings.** PBEsol, no spin-orbit coupling, no dispersion correction.

**Not in the current scope**

- Interstitials and other defects
- PbI₂ termination and other facets
- Absolute formation energies against μ_I and E_F
- Machine-learned potentials and long-time dynamics

**Deferred:** diffusion coefficients from the 10 barriers by kinetic Monte Carlo (cheap, would add the anisotropy); a spin-orbit check on the site energies.

## Methods

### Settings

| Item | Value |
|---|---|
| Code | Quantum ESPRESSO `pw.x`: version 7.6 on the laptop (convergence test, soft relaxation), version 6.5 on the cluster (tight relaxation and all defect calculations) |
| Functional | PBEsol |
| Spin-orbit coupling | Not included (scalar-relativistic pseudopotentials) |
| Dispersion correction | None |
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


| Step | Calculation | Result |
|---|---|---|
| 1 | Tight relaxation of the 20-atom cell | Reference lattice. **Done** |
| 2 | Perfect 2×2×2 supercell (160 atoms) | Energy reference |
| 3 | 4c and 8d vacancy, charge +1 and neutral | Site energy difference; charge state compared with paper A |
| 4 | NEB for the 10 distinct bulk hops | Bulk barriers; validation against paper A |
| 5 | CsI-terminated (001) slab: build and convergence | Slab whose middle reproduces the bulk |
| 6 | Vacancies at increasing depth | Site energy against depth |
| 7 | NEB at increasing depth | Barriers against depth, converging to step 4 |

One vacancy per supercell; the cell is fixed in all defect calculations.

### Bulk (steps 2 to 4)

**Validation targets from paper A** (same material, functional and supercell):

| Quantity | Paper A | Our check |
|---|---|---|
| Vacancy site energy, 4c minus 8d | about +0.03 eV | Step 3, both charge states |
| Barrier 8d to 8d | 0.34 eV | Step 4 |
| Barrier 8d to 4c (average of both directions) | 0.35 eV | Step 4 |
| Barrier 4c to 4c (long jump) | about 0.77 eV | Step 4 |

Paper A does not state its charge state; whichever of ours reproduces these numbers indicates which one they used.

**Hop set.** All octahedra are equivalent (Pb on Wyckoff site 4b), and Pb is an inversion centre, so the 12 edges of one octahedron give **6 short hops** (S1–S6). Hops between corner-sharing octahedra give **4 long hops** (L1–L4).

![The 10 distinct iodine hops on three corner-sharing octahedra, viewed along a and along c](assets/octahedra_hops.png)

| Hop | Ends | Length (Å) | | Hop | Ends | Length (Å) |
|---|---|---|---|---|---|---|
| S1 | 8d–8d | 4.41 | | L1 | 8d–8d | 4.80 |
| S2 | 4c–8d | 4.43 | | L2 | 8d–8d | 5.18 |
| S3 | 4c–8d | 4.45 | | L3 | 4c–4c | 5.28 |
| S4 | 4c–8d | 4.53 | | L4 | 4c–8d | 5.93 |
| S5 | 4c–8d | 4.56 | | | | |
| S6 | 8d–8d | 4.60 | | | | |

Lengths from the tight-relaxed cell. One vacancy per site type is enough in the bulk. Each 4c–8d NEB gives both directions.

**Checks**

- Neutral vacancy: total magnetisation about 1 μB per cell.

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
| Soft relaxation | 8.3776 | 8.9330 | 12.3518 | 924.38 |
| **Tight relaxation** | **8.3620** | **8.9607** | **12.3503** | **925.41** |
| Tight vs soft | −0.19% | +0.31% | −0.01% | +0.11% |
| Tight vs experiment | −2.50% | +1.18% | −0.98% | −2.31% |

| | Pb–I–Pb angles | Pb–I bond lengths (Å) |
|---|---|---|
| Experiment, 293 K | 150.84° to 160.63° | 3.148 to 3.221 |
| Soft relaxation | 148.09° to 153.54° | 3.172 to 3.188 |
| **Tight relaxation** | **148.19° and 154.54°** | **3.165 to 3.190** |

| | Soft relaxation | Tight relaxation |
|---|---|---|
| Force limit (largest component) | 0.026 eV/Å (10⁻³ Ry/Bohr) | 0.010 eV/Å (4×10⁻⁴ Ry/Bohr) |
| Pressure limit | 0.5 kbar | 0.2 kbar |
| Final largest force component | | 0.0047 eV/Å (1.8×10⁻⁴ Ry/Bohr) |
| Final pressure | −0.04 kbar | −0.13 kbar |
| Steps and time | 37 + 3 evaluations, 16 h 24 min on a 6-core laptop | 14 steps, 1 h 32 min on one 40-core node |
| Code | Quantum ESPRESSO 7.6 | Quantum ESPRESSO 6.5 |

The tight relaxation lowered the energy by 1.9 meV per 20-atom cell. The volume and c hardly changed, but a shortened and b lengthened by 0.2 to 0.3%: the cell is very soft against exchanging a for b, which goes with a small change in octahedral tilt. Run on the soft-relaxed structure, the two code versions gave the same total force to six decimal places.

The defect calculations use the tight-relaxed cell.


## File structure

One folder per step of the Methods. The steps that have not started yet hold only a `.gitkeep`.

```
.
├── README.md                    this file
├── NOTES.md                     working notes: cluster, jobs, decisions, commands
├── Literatures/                 literature_review.md (papers A, B and C in detail) and the papers as PDF (not tracked)
├── LICENSE
├── run_qe.pbs                   PBS job script for pw.x, shared by all cluster jobs
├── assets/                      figures used in this README
│
├── 01_unitcell/                 step 1: convergence test, soft and tight relaxation of the 20-atom cell
├── 02_pristine/                 step 2: perfect 2×2×2 supercell (160 atoms)
├── 03_vacancies/                step 3: 4c and 8d vacancies, charge +1 and neutral
├── 04_bulk_neb/                 step 4: NEB for the 10 bulk hops (to do)
├── 05_slab/                     step 5: CsI-terminated (001) slab, build and convergence (to do)
├── 06_slab_vacancies/           step 6: vacancies at increasing depth (to do)
└── 07_slab_neb/                 step 7: NEB at increasing depth (to do)
```

### `01_unitcell/`

```
01_unitcell/
├── gamma_CsPbI3_vcrelax.in      base input: experimental γ-CsPbI₃ cell (20 atoms) and settings
├── kconv.sh                     convergence test (k-mesh and cutoff)
├── conv/                        its inputs and outputs: k221 … k664 at 50 Ry, e40 … e80 at 4×4×3
├── conv_summary.txt             energies from the convergence test
├── relax2stage.sh               two-stage variable-cell relaxation (soft)
├── stage1_k332/                 stage 1, coarse 3×3×2 k-mesh: vcrelax.in, vcrelax.out
├── stage2_k443/                 stage 2, converged 4×4×3 k-mesh: vcrelax.in, vcrelax.out
├── final/                       soft-relaxed structure: scf-ready input, structure blocks, .cif
├── relax_summary.txt            energies, forces, timing; lattice against experiment
└── tight/                       tight relaxation, run on the cluster
    ├── unit_tight_relaxed.in    the tight-relaxed cell; every later structure is built from it
    ├── vcrelax.in               tight-relaxation input
    ├── vcrelax.out              its output
    └── vcrelax.cif
```

The base input holds the experimental room-temperature structure (Sutton et al., ACS Energy Lett. 2018). Both shell scripts read it from their own folder and neither changes it.

### `02_pristine/` and `03_vacancies/`

```
02_pristine/
├── relax.in                     perfect supercell, atoms relaxed at fixed cell: the energy reference
└── relax.cif

03_vacancies/
├── build_defects.py             writes 01_unitcell/tight/vcrelax.in, 02_pristine/ and 03_vacancies/
├── sites_report.txt             which atoms were removed
├── q+1/                         charge +1
│   ├── vac_I_apical/            vacancy on a 4c site: relax.in, relax.cif
│   └── vac_I_equatorial/        vacancy on an 8d site
└── q0/                          the same two, neutral and spin-polarised
    ├── vac_I_apical/
    └── vac_I_equatorial/
```

`build_defects.py` builds vacancies only; the NEB end points will come from a separate script, `build_neb.py`, in `04_bulk_neb/`.

`run_qe.pbs` loads the modules and runs `pw.x` in the folder it is submitted from, with as many processes as nodes × 40. Give the node count, input name and k-point pools on the `qsub` line, for example `qsub -N pristine -l nodes=2:ppn=40 -v INPUT=relax.in,NK=2 <path>/run_qe.pbs`. Check memory first: see `NOTES.md`.

The cluster copy lives in `~/cspbi3/` with its own layout (`pristine_222/`, `q+1/`, `q0/`).

## How to reproduce

```bash
# 1. convergence test and soft relaxation
cd 01_unitcell
bash kconv.sh | tee conv_summary.txt
bash relax2stage.sh
cd ..

# 2-3. supercell and vacancy inputs (from the project root, after the tight relaxation)
python3 03_vacancies/build_defects.py 01_unitcell/tight/unit_tight_relaxed.in --pseudo-dir /path/to/pseudo
```

Set `PW` (path to `pw.x`) and `NP` (number of MPI processes) at the top of each shell script. Set `pseudo_dir` in `01_unitcell/gamma_CsPbI3_vcrelax.in`. `build_defects.py` needs Python 3 with NumPy and ASE.

## Not tracked

Listed in `.gitignore`:

- `tmp/` and `*.save/`: Quantum ESPRESSO scratch data
- `*.wfc*`, `*.xml`: wavefunctions and data files
- `backup/`, `*:Zone.Identifier`, `__pycache__/`
- `Literatures/*.pdf`: the papers themselves (copyrighted), kept locally only

## Next steps

1. Finish the five supercell relaxations; check the k-mesh, energies and the neutral magnetisation.
2. Compare the 4c and 8d vacancy energies with paper A (about +0.03 eV) for both charge states.
3. Write `build_neb.py` (end points for S1–S6 and L1–L4); trial NEB for one 8d-8d hop against 0.34 eV, then the rest.
4. Build the CsI-terminated slab and run the convergence tests before any defect in it.
