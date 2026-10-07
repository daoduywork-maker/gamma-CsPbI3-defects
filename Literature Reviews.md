# Reading notes: three papers that define the project

Fill in the blanks as you read. Short answers are enough; a number, a page or figure reference, or "not stated". The last section turns your answers into decisions for the next run.

Suggested order: Paper A, then B, then C.

**Our setup, for comparison while reading**

| Item | Ours |
|---|---|
| Material and phase | γ-CsPbI₃, orthorhombic (Pnma, Pbnm setting) |
| Code | Quantum ESPRESSO |
| Functional | PBEsol, no dispersion correction, no spin-orbit coupling |
| Cutoff | 60 Ry (480 Ry density) |
| Supercell | 2×2×2, 160 atoms, k-mesh 2×2×2 |
| Relaxed cell | a = 8.362, b = 8.961, c = 12.350 Å |
| Defects so far | Iodine vacancy on apical and equatorial sites, charge +1 and neutral |
| Convergence | Largest force component 0.010 eV/Å |

---

## Paper A. Ion migration in bulk γ-CsPbI₃ (read first)

**Ion Migration and Dopant Effects in the Gamma-CsPbI₃ Perovskite Photovoltaic Material: Atomistic Insights through Ab Initio and Machine Learning Methods**
Chem. Mater. 37, 4416 (2025). DOI: 10.1021/acs.chemmater.5c00503
Open copy: https://pmc.ncbi.nlm.nih.gov/articles/PMC12199300/
Authors: _fill in_

**Why it matters:** same material and phase as ours. It may already contain our bulk results. I could not open it, so everything below is unknown until you read it.

### Method

| Question | Answer |
|---|---|
| Code and functional | |
| Dispersion correction? Spin-orbit coupling? | |
| Supercell size and k-mesh | |
| Their relaxed lattice parameters a, b, c | |
| Which defects (I vacancy, I interstitial, Cs, Pb)? | |
| Which charge states? | |
| How barriers were computed (NEB, number of images, climbing image?) | |
| Which machine-learning potential, and trained on what? | |

### Hops and barriers

| Question | Answer |
|---|---|
| How many distinct iodine vacancy hops do they report? | |
| What do they call them (apical/equatorial, axial, in-plane, other)? | |
| How did they decide which hops are distinct (symmetry, distance, computed all)? | |
| Do they give forward and backward barriers separately? | |

Barrier table (copy their numbers):

| Hop (their name) | Hop length (Å) | Barrier (eV) | Charge state |
|---|---|---|---|
| | | | |
| | | | |
| | | | |
| | | | |

### Overlap with us

| Question | Answer |
|---|---|
| Do they compare apical and equatorial vacancy energies? Which is lower, by how much? | |
| Any surfaces or slabs at all? | |
| What do the dopants do, in one sentence? | |
| What do they name as open questions in the conclusions? | |

**My one-line summary of this paper:**

---

## Paper B. Vacancy migration at CsPbBr₃ surfaces (our template)

**Halogen vacancy migration at surfaces of CsPbBr₃ perovskites: insights from density functional theory**
R.-I. Biega and L. Leppert, J. Phys.: Energy 3 (2021). DOI: 10.1088/2515-7655/ac10fe

**Why it matters:** the same kind of study we plan, for the bromide. Known so far: the barrier for axial-to-axial bromine vacancy migration at the surface is about half the bulk value; they attribute this to larger bond-length freedom at the surface; an NaCl layer on the surface raises the barrier back toward the bulk value.

### Method

| Question | Answer |
|---|---|
| Code and functional | |
| Which phase of CsPbBr₃ (cubic, orthorhombic)? | |
| Bulk supercell size and k-mesh | |
| Charge state of the vacancy | |
| NEB details (images, climbing image, force threshold) | |

### Slab setup (we will copy or adapt this)

| Question | Answer |
|---|---|
| Surface orientation and termination (CsBr or PbBr₂) | |
| Slab thickness (number of layers) | |
| Vacuum thickness | |
| Which layers were fixed, which relaxed? | |
| In-plane size of the slab cell | |
| Symmetric slab, or dipole correction? | |
| How did they handle a charged defect in a slab? | |

### Hops and barriers

| Question | Answer |
|---|---|
| What exactly is the "axial-to-axial" path: one direct jump, or two jumps through an equatorial site? | |
| Which other paths did they compute (axial-equatorial, equatorial-equatorial)? | |
| How did they define "at the surface" (which layer)? | |
| Did they compute intermediate depths, or only surface and bulk? | |

Barrier table:

| Path | Bulk barrier (eV) | Surface barrier (eV) |
|---|---|---|
| | | |
| | | |
| | | |

### Overlap with us

| Question | Answer |
|---|---|
| Do they report where the vacancy prefers to sit (surface or bulk), with energies? | |
| Anything on interstitials? | |
| What do they name as open questions? | |

**My one-line summary of this paper:**

---

## Paper C. Defect formation energies versus depth (the static picture)

**Modulation of point defect properties near surfaces in metal halide perovskites**
B. Ahmad, M. S. R. Limon and Z. Ahmad, Phys. Rev. Materials 8, 125402 (2024). arXiv: 2407.02249

**Why it matters:** same slab idea as ours, for the same material. Known so far: orthorhombic CsPbI₃ and MAPbI₃, (001) surface, 17-layer slabs, Quantum ESPRESSO with PBE, norm-conserving pseudopotentials and DFT-D3; iodine vacancy and interstitial in charge states +1, 0, −1; formation energy follows a saturating exponential with depth; for CsPbI₃ the surface-to-bulk difference is 0.07 to 0.27 eV. No migration barriers.

### Slab setup

| Question | Answer |
|---|---|
| Termination of the (001) surface (CsI or PbI₂) | |
| In-plane cell size and k-mesh | |
| Vacuum thickness | |
| Which layers fixed? | |
| How did they correct for charged defects in a slab? | |
| Cutoff energy | |

### Results to compare with ours later

| Question | Answer |
|---|---|
| Which iodine site did they remove (apical, equatorial, both)? | |
| Is the vacancy more stable at the surface or in the bulk? | |
| Decay length for the iodine vacancy in CsPbI₃ (Å) | |
| How many layers until bulk behaviour is recovered? | |
| Stable interstitial configuration in the bulk, and at the surface | |

Formation energy table for CsPbI₃ (copy what they give):

| Defect and charge | Surface (eV) | Bulk (eV) | Difference (eV) |
|---|---|---|---|
| V_I, +1 | | | |
| V_I, 0 | | | |
| I_i, −1 | | | |
| I_i, 0 | | | |

### Overlap with us

| Question | Answer |
|---|---|
| Do they say anything about migration or kinetics, even in the outlook? | |
| What do they name as open questions? | |

**My one-line summary of this paper:**

---

## Decisions for the next run

Fill this last. Each row is a choice that your reading settles.

| Decision | What the papers suggest | My choice |
|---|---|---|
| Which vacancy hops to compute in the bulk | | |
| How to label hops in our files and figures | | |
| Charge state(s) for the barriers | | |
| Number of NEB images, climbing image or not | | |
| Add dispersion correction or spin-orbit coupling for comparison? | | |
| Slab termination | | |
| Slab thickness and vacuum | | |
| Which slab layers to fix | | |
| How many depths to sample | | |
| Include the interstitial now or later | | |

**Is our bulk stage already published in Paper A?** (yes / partly / no, and what is left):

**What is still open after these three papers, in my own words:**

**Anything that surprised me or that I did not understand:**
