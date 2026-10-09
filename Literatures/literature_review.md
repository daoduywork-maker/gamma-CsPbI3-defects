# Literature review: the three papers that define the project

Read 8 October 2026: paper A with its Supporting Information, paper B, and paper C with its Supporting Information. Numbers are as reported, or read from the papers' figures where marked "about". Interpretations that are ours, not the authors', are marked **(our reading)**.

**Our setup, for comparison**

| Item | Ours |
|---|---|
| Material and phase | γ-CsPbI₃, orthorhombic (Pnma, Pbnm setting, c the long axis) |
| Code | Quantum ESPRESSO |
| Functional | PBEsol, no dispersion correction, no spin-orbit coupling |
| Cutoff | 60 Ry (480 Ry density) |
| Relaxed cell | a = 8.362, b = 8.961, c = 12.350 Å |
| Defect supercell | 2×2×2, 160 atoms (159 with a vacancy), k-mesh 2×2×2 |
| Force limit | Largest component 0.010 eV/Å |
| Defects so far | Iodine vacancy on apical (4c) and equatorial (8d) sites, charge +1 and neutral |

Site names: the papers use the crystallographic labels. **I(4c) = apical** (in the CsI layers, linking octahedra along c). **I(8d) = equatorial** (in the PbI₂ layers). Biega and Leppert, working on the cubic phase, say **axial** for the apical position.

---

## Paper A. Ion migration in bulk γ-CsPbI₃

A. N. Arber, Vikram, F. C. Mocanu and M. S. Islam (University of Oxford), *Ion Migration and Dopant Effects in the Gamma-CsPbI₃ Perovskite Photovoltaic Material: Atomistic Insights through Ab Initio and Machine Learning Methods*, Chem. Mater. 37, 4416 (2025). DOI: 10.1021/acs.chemmater.5c00503

### Method

| Question | Answer |
|---|---|
| Code and functional | VASP, PAW, PBEsol, 500 eV |
| Dispersion, spin-orbit coupling | Neither mentioned. Their band gap of 1.60 eV (experiment 1.72) fits a calculation without spin-orbit coupling |
| Spin | Spin-polarised in every calculation, "to ensure that any effects due to unpaired electrons, notably in the defect structures, were captured" |
| k-points | "k-point spacing of 0.2/2π Å⁻¹", written ambiguously |
| Force limit | 0.01 eV/Å |
| Defect cell | 2×2×2 supercell, 159 atoms with one iodine vacancy. No finite-size correction; they argue the cell is large enough |
| Lattice (their labels swapped to ours) | a = 8.68, b = 8.71, c = 12.44 Å; experiment 8.58, 8.86, 12.47 Å |
| Defects | I vacancy (three paths), Cs and Pb vacancies, Schottky and Frenkel energies, B-site dopants |
| NEB | Climbing image. About 9 to 11 images, judging by the points in Fig. S1 |
| Reported barrier | **Average of forward and backward** barriers (SI, Fig. S1 caption) |
| Machine-learned potential | MACE. About 4,000 structures, all 2×2×2 supercells: 238 NEB images, about 3,600 from ab initio MD (NPT and NVT, 300 to 600 K), some MD snapshots, plus Sn-doped sets. Errors 0.50 meV per atom, 1.06 meV/Å |
| MD | LAMMPS, 960-atom cells, 1% iodine vacancies placed at random, about 80 ns, 300 to 500 K |

### Charge state: not stated

Neither the main text nor the SI says which charge the defect cells carry.

- For +1: the vacancy is written V_I• (Kröger–Vink, one positive charge); the Schottky and Frenkel equations are written as balanced charged defects.
- For neutral cells **(our reading)**: the remark about unpaired electrons fits the neutral vacancy, which has one; the +1 vacancy has none. No total charge, background or correction is mentioned.

To settle it: compare our +1 and neutral results with their numbers, or ask the corresponding author (S. Islam).

### Hops and barriers

| Path (their name) | Our name | Barrier |
|---|---|---|
| I8d to I8d | equatorial to equatorial | 0.34 eV |
| I8d to I4c | equatorial to apical | 0.35 eV (average; forward and backward differ by about 0.03 eV) |
| I4c to I4c | apical to apical, the long jump | about 0.77 eV |
| Cs vacancy | | about 0.75 eV |
| Pb vacancy | | about 1.6 eV |
| From the MACE MD (Arrhenius) | | 0.42 eV pristine, 0.43 eV with 3% Sn |

- One barrier per type of path. They do not separate the symmetry-distinct variants within each type (our set: 6 short and 4 long hops, see the README).
- The paths are slightly curved, bowing away from the Pb atom.
- Dopants change the 8d-to-8d barrier only between 0.24 eV (Zn) and 0.44 eV (Cd).
- Schottky defect 0.18 eV per defect, iodine Frenkel 0.58 eV per defect.

### Site energies

From Fig. S1: the end of the 8d-to-4c path lies about 0.03 eV above its start. So **a vacancy on the apical (4c) site is about 0.03 eV higher than on the equatorial (8d) site.**

### Overlap with us

| Question | Answer |
|---|---|
| Surfaces or slabs | None |
| Same as our bulk stage? | Largely yes: same material, functional, supercell and defect |
| Open questions in their conclusions | Doping strategies; nothing on surfaces |

**Summary:** the bulk iodine-vacancy barriers in γ-CsPbI₃ are published (0.34 to 0.35 eV for the edge hops). Our bulk stage becomes a validation, plus the symmetry-distinct variants of every hop type.

**Discrepancy to keep in mind:** their cell is less distorted in plane than experiment (8.68 against 8.71 Å); ours is more distorted (8.36 against 8.96 Å). The a/b distortion is very soft in our calculation (1.9 meV per cell over the whole tight relaxation), so different codes and settings can land at different points. This may affect the equatorial hops and needs discussing in a paper.

---

## Paper B. Halogen vacancy migration at CsPbBr₃ surfaces

R.-I. Biega and L. Leppert (Bayreuth and Twente), *Halogen vacancy migration at surfaces of CsPbBr₃ perovskites: insights from density functional theory*, J. Phys.: Energy 3, 034017 (2021). DOI: 10.1088/2515-7655/ac10fe

### Method

| Question | Answer |
|---|---|
| Code and functional | VASP, PAW, PBEsol, 300 eV |
| Phase | **Cubic** CsPbBr₃ (no octahedral tilting), a = 5.86 Å |
| k-points | 4×4×4 bulk, 4×4×1 slab |
| Force limit | 0.05 eV/Å |
| Cell | Volume and shape fixed |
| Charge state | Not stated |
| NEB | Climbing image, **3 images**. Barrier = saddle minus initial state |

### Slab setup

| Question | Answer |
|---|---|
| Size | 2 × 1 × 6 cubic cells: 11.7 × 5.9 Å in plane, 6 layers |
| Terminations | A = PbBr₂, B = CsBr |
| Fixed layers | Bottom 3 fixed, top 3 mobile (also a test with 4 mobile) |
| Vacuum | 30 Å |
| Checks | Surface energy within 25 meV against slab thickness |
| Known artefacts | The authors call the 2 × 1 cell "asymmetric": it causes a 20% compression of surface axial bonds, much less in 2 × 2 |

### What "axial-to-axial" is

A jump between **two neighbouring axial sites in the same layer, about 5.9 Å apart**: not along an octahedron edge. It is the equivalent of paper A's 4c-to-4c long jump. The short edge hops, the easiest paths in the bulk, were **not computed at the surface**.

### Results

Vacancy preference for the surface (binding energy, bulk minus slab formation energy, axial vacancy):

| Layer | A (PbBr₂) | B (CsBr) |
|---|---|---|
| 1 | 0.42 eV | 0.23 eV |
| 2 | 0.22 eV | 0.23 eV |
| 3 | 0.05 eV | 0.02 eV |

Axial-to-axial barriers:

| Where | 2×1 cell, 3 mobile layers | 2×1 cell, 4 mobile layers | 2×2 cell |
|---|---|---|---|
| Bulk | 0.65 eV | | 0.48 eV |
| Layer 1 | 0.40 (A), 0.31 (B) | 0.38 (A) | 0.28 |
| Layer 2 | 0.29 (A), 0.30 (B) | 0.26 (A) | 0.20 |
| Layer 3 | 0.30 (A) | 0.27 (A) | 0.26 |
| Layer 4 | | 0.29 (A) | |

- At the surface the path curves strongly (deviation 1.24 Å at A, against 0.13 Å in the bulk).
- Lower barriers go with compressed axial Pb–Br bonds.
- A NaCl monolayer on the surface raises the barrier to 0.57 eV; NaBr to 0.48 eV.

### Weakness

**The barriers never return to the bulk value with depth** (0.29 eV in layer 4 against 0.65 eV in the bulk). The authors note that the fixed bottom layers may affect the barriers and that "bulk-like barriers deeper into the surface would likely require structural models with more surface layers". How much of the "halving" is a surface effect and how much comes from a thin, partly frozen slab with a small cross-section is therefore open.

**Summary:** the template for our slab study, but for the long jump only, in the cubic bromide, in a slab too thin to show recovery to the bulk.

---

## Paper C. Defect formation energies versus depth

B. Ahmad, M. S. R. Limon and Z. Ahmad (Texas Tech), *Modulation of point defect properties near surfaces in metal halide perovskites*, arXiv 2407.02249 (2024); Phys. Rev. Materials 8, 125402 (2024)

### Method

| Question | Answer |
|---|---|
| Code and functional | Quantum ESPRESSO, PBE + D3 dispersion |
| Pseudopotentials, cutoff | Norm-conserving (PseudoDojo), 75 Ry / 300 Ry |
| k-points | 2×2×2 bulk, 3×3×1 slab |
| Convergence | Energy 10⁻⁴ Ry, forces 10⁻³ Ry/Bohr (0.026 eV/Å) |
| Lattice | Their Table S2 lists the experimental values (8.856, 8.576, 12.472 Å, matching Sutton et al. to the third decimal). Whether the cell was relaxed with their functional is not stated |
| Bulk defect cell | 80 atoms (2×2×1) |
| Defects | I vacancy and I interstitial, charge +1, 0, −1 |
| Charge correction | Freysoldt scheme (sxdefectalign in bulk, sxdefectalign2d in the slab), dielectric constant 18 for CsPbI₃. Bulk correction for the +1 vacancy 0.02 eV |
| Chemical potential | Pb-rich, PbI₂-excess limit only; secondary phases CsI and PbI₂ |

### Slab setup

| Question | Answer |
|---|---|
| Thickness | 17 layers, alternating PbI₂ and CsI, about 25 Å |
| Termination | Apparently PbI₂ on both faces (shown for MAPbI₃; not stated for CsPbI₃) |
| Vacuum | 10 Å on each side, dipole correction |
| In-plane size, fixed layers | Not stated |
| Which iodine | Always in a PbI₂ layer: **equatorial (8d) only** |
| Depths | 4 layers, about 3 to 22 Å |

### Results for CsPbI₃ (formation energy at the valence band edge, read from Fig. 6)

| Defect | Bulk | Top layer | Deep slab layers (plateau) | Plateau minus bulk |
|---|---|---|---|---|
| Vacancy, +1 | about −0.13 eV | −0.20 eV | about −0.37 eV | about −0.24 eV |
| Vacancy, 0 | about 1.23 eV | about 1.33 eV | about 1.35 eV | about +0.11 eV |
| Vacancy, −1 | about 2.53 eV | about 2.67 eV | about 2.88 eV | about +0.35 eV |

- Surface-to-bulk differences in CsPbI₃: 0.07 eV for the +1 vacancy up to 0.27 eV for the −1 interstitial.
- Decay length for the +1 vacancy in CsPbI₃: 0.06 Å, i.e. only the top layer is affected. The longest is 3.75 Å (+1 interstitial).
- The −1 vacancy pulls two Pb atoms to 3.56 Å in the bulk, but not in the slab (5.87 Å): a different structure.
- The +1 interstitial bonds to Cs in the bulk but only to Pb near the surface.
- Charge transition levels of the vacancy shift by about 0.1 eV between surface and depth.

### Weakness: the slab interior does not match the bulk

The deep layers reach a flat plateau, so the surface influence has died out and 17 layers is thick enough. But the plateau differs from the separate bulk calculation by 0.05 to 0.66 eV across defects (the authors' own range). The authors attribute it to different bond lengths and bonding environments, and possibly the charge corrections.

**(Our reading)** The offset changes sign with the charge and is smallest for the neutral vacancy: −0.24, +0.11 and +0.35 eV for +1, 0 and −1. That pattern points mainly to how charged defects are referenced in the two calculations (band-edge alignment between slab and bulk, 3D against 2D charge correction), which shifts +1 and −1 in opposite directions and leaves the neutral one untouched. The remaining ~0.1 eV seen even for the neutral vacancy would come from structural differences, such as an 80-atom bulk cell against a 17-layer slab, and a loose force limit. The lattice choice is not a likely cause: whichever lattice they used, it was presumably the same for bulk and slab, so it affects both equally.

**Summary:** the static picture for our material, but equatorial sites only, one termination, no barriers, and a slab that does not reproduce its own bulk reference.

---

## What the three papers leave open

1. **Barriers versus depth in γ-CsPbI₃.** Paper A has bulk barriers only; paper C has formation energies only; paper B has barriers for the bromide.
2. **The easy edge hops at a surface.** Paper B computed only the long axial-to-axial jump; paper A had no surface.
3. **Apical sites near the surface.** Paper C removed equatorial iodine only.
4. **Convergence to the bulk.** Neither surface study shows its slab returning to its own bulk values: paper B because the slab is thin and partly frozen, paper C because of a mismatch between the slab and bulk calculations.

### Why the convergence problem is less serious for barriers than for formation energies

A barrier is the energy of the saddle point minus the energy of the start, in the same slab with the same charge.

| Source of error | Affects formation energies | Affects barriers |
|---|---|---|
| Band-edge alignment between slab and bulk | Yes | No: same calculation |
| Charge-correction scheme | Yes | Almost none: same charge at start and saddle |
| Chemical potential | Yes | No |
| Slab too thin or partly frozen | Yes | **Yes** |

So for barriers, the one thing to get right is the slab itself: deep and free enough that the barrier visibly returns to the bulk value. For formation energies (step 8 of the plan) careful alignment and charge corrections are needed as well.

### Correction to an earlier estimate

Earlier we quoted 0.07 to 0.27 eV as the surface preference and up to 30,000-fold enrichment at the surface. The 0.27 eV belongs to the −1 interstitial. For the +1 iodine vacancy paper C finds 0.07 eV, about a 15-fold enrichment at room temperature. The top layer is therefore unlikely to become crowded with vacancies, and the dilute treatment of step 8 should hold.

---

## Decisions for the next run

| Decision | What the papers suggest | Choice |
|---|---|---|
| Hops in the bulk | A: one per type (8d-8d, 8d-4c, 4c-4c) | All distinct 8d-8d, 8d-4c and 4c-4c paths, separated by symmetry, not only by length |
| Labels | A and C use 4c and 8d | 4c / 8d in figures and the paper; apical / equatorial in explanations |
| Charge state | A: not stated; C: all three | +1 first; neutral as a check and to identify paper A's charge state |
| Spin polarisation | A: everywhere | Required for the neutral vacancy (check total magnetisation about 1 μB); optional test on one +1 structure |
| NEB images | A: about 9 to 11; B: 3 | 7 for the first trial, more if the profile is not smooth; climbing image on |
| Reported barrier | A: average of both directions; B: from the initial state | Report both directions; also give the average for comparison with A |
| Validation targets | A | Site energy 4c minus 8d about +0.03 eV; barriers 0.34 (8d-8d) and 0.35 eV (8d-4c, average) |
| Slab in-plane size | B: 2×1 gives artefacts | 2×2 of our cell, the same as the bulk supercell |
| Slab thickness and freedom | B: too thin, bottom frozen | Symmetric slab, all layers free, thick enough to show recovery to the bulk |
| Termination | B: both; C: PbI₂ | CsI first (as planned), PbI₂ later |
| Sites at depth | C: equatorial only | Both 4c and 8d |
| Dispersion, spin-orbit coupling | C: D3; A: neither | Neither, as A. Spin-orbit single-point check later |
| Charge correction | C: Freysoldt 3D and 2D | Needed for step 8 only |
| Interstitial | C: several configurations | Later stage |

**Is our bulk stage already published in paper A?** Largely yes. What is left: the symmetry-distinct variants of every hop type, both charge states with an explicit statement, and serving as the consistent bulk reference for our own slab.

**What is still open after these three papers:** depth-resolved migration barriers in γ-CsPbI₃ for all paths, apical and equatorial, in a slab shown to converge to the bulk.

**Anything that surprised me or that I did not understand:**

## Related work

Papers outside A, B and C that the project uses. Notes are short; entries marked **(title and abstract only)** have not been read in full.

| Paper | What it gives us | Where we use it |
|---|---|---|
| N. Xu et al., *Point defects in metal halide perovskites*, Nat. Rev. Mater. (2025) | Review of point defects, their electronic tolerance and their role in instability | Citation for "Why defects matter" **(title and abstract only)** |
| Z. Wylie et al., *Surface iodide defects control the kinetics of the CsPbI₃ perovskite phase transformation*, ACS Energy Lett. 9, 4378 (2024), doi:10.1021/acsenergylett.4c01465 | Experiment: CsI or CdI₂ treatment slows the change to δ-CsPbI₃ about fivefold; X-ray photoelectron spectroscopy ties this to surface iodide; surface iodide vacancies are proposed as nucleation sites for the δ phase | Motivation for the surface focus **(abstract only)** |
| M. Pols, T. Hilpert, I. A. W. Filot, A. C. T. van Duin, S. Calero, S. Tao, *What happens at surfaces and grain boundaries of halide perovskites: insights from reactive molecular dynamics simulations of CsPbI₃*, ACS Appl. Mater. Interfaces (2022), arXiv:2205.10545 | Reactive MD (ReaxFF) of orthorhombic CsPbI₃ slabs, 300–700 K: a cubic-like surface shell about 2 nm thick; iodine vacancies seen moving into and out of the surface, without barriers or rates | Closest earlier work for G2; the 2 nm shell is a guide for how deep the surface effect may reach (H3) |
| T. J. A. M. Smolders, R. A. De Souza, A. B. Walker, M. J. Wolf, *Diffusivity tensors of Br and Cs vacancies in biaxially strained perovskite CsPbBr₃*, Chem. Mater. (2024) | Direction-resolved vacancy diffusivity in bulk CsPbBr₃ under strain | Method reference for the deferred diffusion-tensor (kinetic Monte Carlo) add-on **(title only)** |

## Novelty check (October 2026)

- **Keyword search** for depth-resolved vacancy migration at CsPbI₃ and halide perovskite surfaces. Closest hits: Pols 2022 (above); CsI-terminated (100) surfaces of cubic and tetragonal CsPbI₃, formation energies only (arXiv:2309.04870); surface stability of orthorhombic CsPbI₃, no migration (Li et al., arXiv:2411.01599); machine-learned force field for bulk CsPbI₃ only (Tyagi et al., arXiv:2409.16051); bulk orthorhombic CsPbBr₃ NEB only (Miskin et al., PCCP 2025).
- **Cited-by check** of papers A (11 citing works), B (about 28) and C (about 13): reviews, devices, other materials, and the Ahmad group's work on battery materials and halide segregation. None computes vacancy barriers against depth in γ-CsPbI₃.
- **Result:** N2 and N3 stand. The Ahmad group (paper C) is the most likely to extend their study to barriers; check their new papers until ours is out.
