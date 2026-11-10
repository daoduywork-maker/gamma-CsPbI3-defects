# Working notes

Practical details that are not in the README: where things live, how jobs were run, decisions and their reasons, open checks, and commands that work. The README holds the science, the plan and the results.

Last updated: 2026-10-31

**For Claude:** read this file again after every context reset or chat compaction, before giving cluster commands. The cluster facts below are the reference; do not rely on memory of earlier turns.

## Where things are

| Place | Path | Role |
|---|---|---|
| Main repository (WSL) | `~/Project-1` | The copy that pushes to GitHub (`origin`) |
| Desktop copy (Windows) | `C:\Users\ACER\OneDrive\Desktop\Project-1` = `/mnt/c/Users/ACER/OneDrive/Desktop/Project-1` | Shared with Claude for reading and editing. In WSL it is the remote `desktop` of the main repository |
| GitHub | `daoduywork-maker/gamma-CsPbI3-defects` (public) | Backup and sharing |
| Cluster work folder | `/public/home/daomduy/cspbi3` | Calculations |
| Cluster pseudopotentials | `/public/home/daomduy/cspbi3/pseudo_pbesol` | The three SSSP PBEsol files |
| Cluster job script | `/public/home/daomduy/cspbi3/run_qe.pbs` | Same file as `qe/run_qe.pbs` in the repository |
| Own Quantum ESPRESSO build | `/public/home/daomduy/apps/q-e-qe-6.5/bin/` | `pw.x`, `neb.x`, `pp.x`, version 6.5 |

Change flow: edit in the Desktop copy, review with `git diff`, commit there, then in WSL `cd ~/Project-1 && git pull desktop main && git push origin main`. To refresh the Desktop copy after work in WSL: `git pull` inside it.

## Cluster folder layout (since 31 Oct)

`~/cspbi3/` mirrors the repository: `01_unitcell/tight` (was `unitcell_tight`), `02_pristine` (was `pristine_222`), `03_vacancies/q+1`, `03_vacancies/q0`, `03_vacancies/kmesh221_test` (was `kmesh_test`), `04_bulk_neb`, `05_reference_phases`, `vasp/`, `pseudo_pbesol/` (keep this path: QE inputs point to it), `run_qe.pbs`, `run_neb.pbs`. Older job logs and notes use the old names.

**Repository layout (since 4 Nov) differs from the cluster.** In the repository the QE step folders and job scripts are under `qe/` (`qe/01_unitcell` … `qe/05_reference_phases`, `qe/run_qe.pbs`, `qe/run_neb.pbs`), the scripts for both codes (`build_neb.py`, `hop_network.py`, `plot_neb.py`) are in `tools/`, and the empty step 6 and 7 folders were removed. On the cluster the QE folders stay directly in `~/cspbi3/`, so a QE file at `qe/<path>` in the repository is at `~/cspbi3/<path>` on the cluster; `vasp/` is the same in both. Scripts run from the repository root, e.g. `python3 tools/build_neb.py S2 --charge q+1 --code vasp`.

## The cluster

- Login node is called `master`. Never run calculations there; compiling with `make -j 4` and one-second tests are acceptable.
- Scheduler: Torque/PBS with Maui. 44 nodes, 1984 cores: 40 nodes of 40 cores (queue `std40`) and 4 larger ones.
- Home and `/public/apps` are on a shared disk, visible from every node.
- `qstat` shows only your own jobs. Use `showq` to see everyone's, `checkjob <id>` for why a job waits, `showstart <id>` for the scheduler's estimate (pessimistic: it assumes every running job uses its full time limit).
- The cluster is usually 100% full with 160-core jobs that have 30 to 40 day limits. Nodes free up four at a time. The queue is first come, first served. The first one-node job waited about one day.
- Modules for Quantum ESPRESSO: `module load intel/intel2020` then `module load qe/qe-6.5`. The cluster's module has only `pw.x`. `neb.x` and `pp.x` come from the build in the home folder.
- Do not use `disk_io = 'nowf'` with QE 6.5.
- Jobs start with a clean environment, so the job script must load the modules itself.
- Login node has **no Python**: build all inputs on the laptop (WSL or the Desktop copy) and copy them over.
- File transfer: **drag and drop** in the GUI file-transfer window (scp from the terminal does not work for Duy).
- Bash history expansion breaks `grep "^!"` in an interactive shell ("event not found"): run `set +H` first, or use single quotes.

**Node types and memory (check before every submission)**

| Queue | Cores per node | Memory per node | Plan for | Notes |
|---|---|---|---|---|
| `std40` | 40 | 92 GB | at most about 75 GB | Nodes come in groups of four: long jobs take 4 or 8 nodes (senior's advice) |
| `fat96` | 96 | about 251–263 GB | at most about 210 GB | Shared and in demand: do not hold it for long; split work into smaller batches |

Measured memory (use these to size jobs):

| Calculation | Setup | Memory |
|---|---|---|
| QE 160-atom supercell, closed shell (pristine, +1) | 2 std40 nodes, `NK=2` | 62 GB per node (QE estimate 137 GB in total) |
| QE 159-atom neutral (spin-polarised) | 3 std40 nodes, `NK=2` | QE estimate 193 GB in total |
| QE NEB +1, 2 images at once | 4 std40 nodes, `NI=2, NK=2` | 88 GB + swap on one node: **does not fit** |
| QE NEB +1, 1 image at a time | 4 std40 nodes, `NI=1, NK=2` | **33 GB per node, no swap** (job 217856) |
| VASP 159-atom +1 vacancy | 4 std40 nodes | 14 GB per node, max 0.62 GB per process |
| VASP 159-atom neutral (ISPIN = 2) | 4 std40 nodes | 20 GB per node, max 0.73 GB per process |

**VASP on the cluster**

- Modules: `vasp/vasp541scala`, `vasp544elpa`, `vasp544mod`, `vasp544scala`, `vasp632`, `vasp632vaspsol`, `vasp632vaspsol.vtst`, `vasp632vtst`, `vasp632wannier90`, `vasp643`. This project uses **`vasp/vasp632vtst`** for every step (VTST is needed for NEB).
- The VASP module only adds `/public/apps/vasp632vtst` to `PATH` (programs `vasp_std`, `vasp_gam`, `vasp_ncl`; `vasp_ncl` checked 6 Nov, for spin–orbit coupling). It loads no MPI or MKL: **load `intel/intel2020` first**, otherwise `vasp_std` misses the MKL libraries. Checked 31 Oct: `module load intel/intel2020 vasp/vasp632vtst` gives 0 missing libraries. `vasp/run_vasp.pbs` does this.
- POTCARs: `/public/shared-data/pot/vasp/544/PAW_PBE/` (hyphen in `shared-data`). `Cs_sv`, `Pb_d` and `I` are present (checked 31 Oct). PBEsol comes from `GGA = PS` in INCAR with these PBE potentials; there is no separate PBEsol POTCAR set. `vasp/make_potcar.sh` builds POTCAR from the POSCAR species line and checks ZVAL (9, 14, 7).

How the home build was made:

```bash
module purge && module load intel/intel2020
cd ~/apps/q-e-qe-6.5
./configure MPIF90=mpiifort F90=ifort F77=ifort CC=icc --with-scalapack=no
make -j 4 pw neb pp
```

`make.inc` shows `DFLAGS = -D__DFTI -D__MPI`. Source: `https://gitlab.com/QEF/q-e/-/archive/qe-6.5/q-e-qe-6.5.tar.gz`.

## Jobs run so far

| Job | What | Outcome |
|---|---|---|
| 217362 `unit_tight` | Tight vc-relax of the 20-atom cell, 1 node, 4 pools | Done 7 Oct, node32, 14 steps, 1 h 32 min, about 5 min per step |
| 217376–217380, five supercell jobs | `pristine`, `qp1_apical`, `qp1_equatorial`, `q0_apical`, `q0_equatorial`, 1 node each | **Failed 9 Oct: out of memory** (see below). About two days of queue time lost |
| 217406 `pristine` | 2 nodes (80 cores), `NK=2` | **Done 11 Oct 01:28.** Started 10 Oct 22:21 after about 32 h in the queue. Converged on the first SCF (17 iterations), 0 BFGS steps, 3 h 6 min. E = −65326.88713687 Ry, total force 0.0022 Ry/Bohr, highest occupied level 3.4105 eV. Memory 62 GB used per node, no swap. Keep `tmp/` for the potential alignment |
| 217407 `qp1_apical` | 2 nodes, `NK=2` | **Done 14 Oct 09:26.** 47 SCF cycles, 46 BFGS steps, 3 d 11 h wall (about 1.8 h per step). E = −64954.16973158 Ry, largest force 3.1×10⁻⁴ Ry/Bohr, highest occupied level 3.3779 eV. Memory 1.71 GB per process, no swap |
| 217408 `qp1_equatorial` | 2 nodes, `NK=2` | **Done 16 Oct.** 59 SCF cycles, 58 BFGS steps. E = −64954.16980915 Ry, largest force 3.7×10⁻⁴ Ry/Bohr |
| 217409 `q0_apical` | 3 nodes, `NK=2` | **Done 21 Oct 06:29, converged** (`bfgs converged`, 69 SCF cycles, 68 BFGS steps; checked 4 Nov). E = −64953.80113061 Ry, largest force 3.3×10⁻⁴ Ry/Bohr, magnetisation 0. **E(8d) − E(4c) = +40.4 meV** (4c lower; 70% on 4c at 300 K) |
| 217410 `q0_equatorial` | 3 nodes, `NK=2` | **Done 18 Oct.** 54 SCF cycles, 53 BFGS steps. E = −64953.79815909 Ry, largest force 3.6×10⁻⁴ Ry/Bohr, magnetisation 0. Final coordinates printed; then aborted while writing `tmp/` (`seqopn` error 90, could not open `restart89`, `/public` 94% full but 4.1 TB free). Result valid, `tmp/` likely incomplete |
| `kmesh221` | SCF of the relaxed +1 apical structure with a 2×2×1 mesh (4 k-points), 2 nodes | **Done 14 Oct.** 1.50 GB per process. E = −64954.14911857 Ry: +0.28 eV per cell (1.8 meV/atom) above 2×2×2; largest force 1.2×10⁻³ Ry/Bohr (0.031 eV/Å) against 3.1×10⁻⁴ at 2×2×2. Fails; see Decisions |
| 217708 `ref_phases` | Step 5: Cs, Pb, solid I₂, CsI, PbI₂, I₂ molecule side by side, 4 std40 nodes (`05_reference_phases/run_refs.pbs`) | **Done 23 Oct 21:15**, under 1 h. All six converged. E (Ry): Cs −62.89427877, Pb −859.43397176, I₂ (4 atoms) −1491.69347976, CsI −436.04489173, PbI₂ −1605.41570805, I₂ molecule −745.79685350. Cells: PbI₂ a 4.535, c 7.018 Å (−0.5%, +0.6%); CsI 4.502 Å (−1.4%); I₂ a 7.504, b 4.365, c 9.612 Å (+5.2%, −6.8%, −1.8%; volume −4%). Results in the README |
| `S1_qp1` (NEB, first try) | 4 std40 nodes, `NI=2, NK=2` | **Stopped 23 Oct 22:05 by the swap guard** in the first NEB step: node28 88 GB used + 4 GB swap. neb.x needs about 1.4× the memory of a plain relaxation (62 GB per node expected) |
| `S2_qp1` (NEB, first try) | 4 std40 nodes, `NI=2, NK=2` | **Crashed at start** (`PMPI_Init`, rank 80): started on node28 while S1 was still shutting down. Input fine; resubmit |
| 217856 `S1_qp1` (NEB, second try) | 4 std40 nodes, `NI=1, NK=2`, 360 h | **Stopped 3 Nov 19:49 by the swap guard** after about 4.3 days (node11 60 GB used + 3 GB swap; memory grew from 33 GB per node over the run). Last state: climbing image 3, barrier 0.364 eV; image errors 0.25, 0.042, 0.051, 0.035 eV/Å (image 2 not yet below 0.05). Restart from the saved path with `restart_mode = 'restart'` and a looser swap limit (10 GB) |
| 217909 `v_conv`, 217910 `v_unit`, 217911 `v_refs` | VASP V1a cutoff/k tests, V1b unit-cell relaxation (`STAGES=2`), V5 reference phases; 1 std40 node each | **Finished by 3 Nov.** V1b: both stages reached the force limit; E = −60.79013171 eV (20 atoms); cell 8.3705 × 8.9497 × 12.4020 Å (QE +0.10%, −0.12%, +0.42%; volume +0.4%); pressure −0.07 kbar; `GGA = PS` confirmed; 0.39 GB per process. The "Terminated … while true" text at the end of each job log is only the memory watch being stopped, not an error. V1a: cutoff converged already at 350 eV (all 350–650 eV within 0.08 meV/atom); k-mesh 2×2×1/3×3×2/4×4×3/5×5×4 at +45.2/+2.48/+0.22/+0.004 meV/atom above 6×6×4, the same as QE (45.5/2.5/0.23/0.004). V5 (eV per formula unit, CsPbI₃ from the unit cell ÷ 4): ΔH_f CsI −3.079, PbI₂ −1.827, CsPbI₃ −4.985 (QE −3.092, −1.837, −4.991); CsPbI₃ stable vs CsI + PbI₂ by 79 meV (QE 63 meV, from the supercell); solid I₂ 0.314 eV per atom below the molecule (QE 0.339). V2–V3 inputs built 3 Nov from the VASP CONTCAR (same vacancy atoms as QE) |
| 217923 `S1_qp1` (NEB, restart) | 4 std40 nodes, `NI=1, NK=2`, `SWAP_LIMIT_GB=10`, `restart_mode = 'restart'` | **Done 4 Nov 17:06 — converged** (`neb: convergence achieved in 27 iterations`, about 9 h after the restart). **Barrier S1 (+1) = 0.361 eV**, the same in both directions. 34 GB per node, no swap. First run saved as `neb.out.run1`, `mem.log.run1` |
| 217924 `v_pristine` | VASP perfect supercell, 4 std40 nodes | **Done 4 Nov.** Reached the force limit. E = −486.51068279 eV. **14 GB per node** (0.52 GB per process): a VASP supercell needs about 55 GB in total, far less than QE (137 GB) |
| 217925 `v_qp1_apical`, 217926 `v_qp1_equatorial` | VASP +1 vacancy cells, 4 std40 nodes each | **Done 5 Nov**, both reached the force limit. E(4c) = −485.98408 eV (33 steps), E(8d) = −485.98322 eV (31 steps): **E(8d) − E(4c) = +0.9 meV** (QE −1.06 meV). Both codes: the sites are degenerate within ±1 meV (last ionic steps still changed E by 0.3–0.7 meV). Max 0.62 GB per process, about 14 GB per node. CONTCARs copied to the repository |
| 217927 `v_q0_apical`, 217928 `v_q0_equatorial` | VASP neutral vacancy cells (ISPIN = 2), 4 std40 nodes each | **Done 6 Nov**, both reached the force limit. E(4c) = −482.55124 eV (40 steps, mag 0.000), E(8d) = −482.51776 eV (38 steps, mag 0.002): **E(8d) − E(4c) = +33.5 meV** (QE +40.4 meV; 65% on 4c at 300 K). Max 0.73 GB per process, about 20 GB per node |
| 217951 `v_slab2`, 217952 `v_L11vac` | Slabs L13, L15, L17 (1 node); L11 2×2 slab with +1 vacancies at the centre (4 nodes, 96 h) | Queued |
| 217936 `v_slab` | VASP step 8: slabs L07, L09, L11 one after the other, 1 std40 node, 72 h | **Done 7 Nov**, all converged. E = −102.11665 (L07), −132.51860 (L09), −162.91790 eV (L11). Energy test: E(L09) − E(L07) and E(L11) − E(L09) are 6.9 and 4.2 meV from 2 f.u. of bulk (−30.39507 eV). Geometry (`tools/slab_geometry.py`): bonds and equatorial angles reach the bulk by the second PbI₂ layer (11-layer middle 148.46° vs 148.50°), but the **apical Pb–I–Pb angle stays 0.9° too straight (157.1° vs 156.2°) and the inner PbI₂ spacing 0.45% too long (6.229 vs 6.201 Å)** in the 11-layer middle, almost unchanged from 9 layers. Read as surface untilting reaching deeper than 1.5 nm (cf. Pols 2022, ~2 nm cubic-like shell); comparable to ~0.5% strain in Zhang 2025, so possibly 10–30 meV on hops through CsI layers. Next: 13, 15, 17 layers. 17 GB on the node |
| 217939 `v_S1_qp1`, 217940 `v_S2_qp1` | VASP NEB +1, 4 moving images, 4 std40 nodes (one image per node); walltime changed to 96 h with `qalter` | **Converged 9 Nov** (all 4 images below 0.03 eV/Å; 25 and 27 steps, about 2 h per step). **S1 = 0.345 eV** (images 0.180, 0.345, 0.225, 0.093). **S2 = 0.326 eV from 8d, 0.327 eV from 4c** (images 0.065, 0.237, 0.326, 0.154; climbing image 3). 30–31 GB per node, no swap. Energies and tangent forces in `vasp/04_bulk_neb/q+1/<hop>/neb_data.txt` |
| 217941 `v_L3_qp1`, 217942 `v_S6_qp1` | VASP NEB +1, as above | **Converged 10 Nov**: **L3 = 0.777 eV** (33 steps; images 0.081, 0.426, 0.777, 0.254), **S6 = 0.434 eV** (39 steps; 0.235, 0.434, 0.297, 0.104). S6 − S1 = 0.09 eV: barriers of one path type differ |
| 217944 `v_soc` | SOC single points | **Done 10 Nov**, all converged (17–21 electronic steps). Gap (EIGENVAL, Γ): 1.619 eV PBEsol, **0.703 eV with SOC**. +1: E(8d) − E(4c) = +1.0 meV (−516.28976 / −516.29072 eV), max force 0.012/0.015 eV/Å. **q0: −71.0 meV** (8d lower; −513.38890 / −513.31794 eV), max force 0.092 (8d) / 0.271 eV/Å (4c): neutral not converged with SOC |
| 217961, 217962 `v_socrel_apical`, `v_socrel_equatorial` | SOC relaxations of the two neutral cells (`RELAX=1 make_soc.sh`, `vasp_ncl`, 96 h) | Queued 10 Nov. Check E(8d) − E(4c) and whether two Pb next to the vacancy move together (electron localising) |

**Incident, 9 Oct: jobs submitted without a memory check.** A std40 node has 92 GB. QE's estimate (printed in the first minute, `Estimated total dynamical RAM`) was 137 GB for the pristine and +1 supercells and 193 GB for the spin-polarised neutral ones. On one node the jobs ran out of memory: node32 showed 92 GB used plus 45 GB of swap, 92% of CPU time waiting on the disk, pw.x in state `D`. The +1 jobs were killed, the pristine one never finished its first SCF iteration. Fix: resubmit on 2 or 3 nodes; the job script takes the process count from the node list, so only `-l nodes=N:ppn=40` changes.

**Node rule (from a senior, 10 Oct):** the std40 nodes are grouped in fours and most jobs take whole groups. Long jobs use 4 or 8 nodes; 1 or 3 nodes leave nodes of a group idle.

**Before every submission (memory checklist)**

1. Node limit: 92 GB per std40 node; plan for at most about 75 GB per node.
2. Job memory: from an earlier run of the same size, or start the job, read `grep "Estimated total dynamical RAM" *.out` within a minute or two, and stop it if total ÷ nodes is over about 75 GB.
3. Nodes = total ÷ 75 GB, rounded up. Spin-polarised (neutral) runs need about 1.4× the closed-shell ones.
4. After the start: `ssh <node> free -g`; swap use must stay near 0.
5. NEB: memory per image × images run at once (`-ni`). With about 136 GB per +1 image, running 7 images at once would need about 14 nodes; run fewer at a time, use fewer images, or test a lighter k-mesh first.

Submit command used for the five (9 Oct, old cluster layout; since 31 Oct the folders are `02_pristine` and `03_vacancies/q+1`, `03_vacancies/q0`):

```bash
PBS=~/cspbi3/run_qe.pbs
for d in pristine_222 q+1/vac_I_apical q+1/vac_I_equatorial q0/vac_I_apical q0/vac_I_equatorial; do
  name=$(echo "$d" | sed 's|/vac_I_|_|; s|pristine_222|pristine|; s|+|p|')
  (cd "$d" && qsub -N "$name" -l nodes=2:ppn=40 -l walltime=360:00:00 -v INPUT=relax.in,NK=2 "$PBS")   # use nodes=3 for the q0 jobs
done
```

The job runs in the folder `qsub` was typed in. Options on the `qsub` line override the script: `-N` the name, `-l walltime=` the limit, `-v INPUT=...,NK=...` the input file and k-point pools. The script's defaults (`vcrelax.in`, 4 pools, 72 h) suit the unit cell only.

## Decisions and why

| Decision | Reason |
|---|---|
| Unit-cell k-mesh kept at 4×4×3, not 4×4×4 | User's choice. 4×4×4 would match the 2×2×2 supercell mesh exactly. To be checked on the first step of `pristine_222` |
| NEB keeps the 2×2×2 supercell mesh, not 2×2×1 | 2×2×1 test on the relaxed +1 apical cell: forces 4× larger (0.031 eV/Å) and 1.8 meV/atom energy shift, so end points and barriers would change. Memory per process fell only from 1.71 to 1.50 GB, so the coarse mesh would save time (about 2×) but not nodes |
| Nodes per job: 2 for the pristine and +1 supercells, 3 for the neutral ones; from now on 4 or 8 | Memory: 137 GB (+1) and 193 GB (neutral, spin-polarised) do not fit one 92 GB node (incident, 9 Oct). Nodes come in groups of four, so long jobs take 4 or 8 to leave none idle |
| Five separate jobs, not one merged job | Same queue wait, run simultaneously, one failure does not stop the others |
| Walltime 360 h for supercells | Step time unknown; estimated a few hours per step. A killed job loses its run |
| Charge +1 first | Closed shell; the usual state of the iodine vacancy; least sensitive to spin-orbit coupling |
| Hop inputs removed from `build_defects.py` | Grouping hops by length may merge distinct hops. To be rebuilt after the literature is read |
| Tight relaxation done before building supercells | Soft result still had a and b drifting by 0.2 to 0.3% |
| All production runs with QE 6.5 on the cluster | One code version. QE 7.6 (laptop) and 6.5 gave the same total force on the same structure |
| No GitHub write access for Claude | User reviews and pushes every change |
| Scope extended (23 Oct): Part A defect thermodynamics, Part B diffusion, Part C surface | Supervisor's feedback: follow the group's earlier work (Xu 2017, Xu 2019, Zhou 2021): which defects dominate and in which charge state, then how fast they move. Slab stage kept as the novelty |
| Step 6 defect set: V_I, V_Pb, V_Cs, I_i (not all ~20 intrinsic defects) | These set the Fermi level and include the likely mobile species; full set only if the supervisor asks |
| Relaxations and NEB stay PBEsol without SOC; SOC (and HSE if affordable) as single points | Consistent with all runs so far and with paper A. Group's SI: barriers within 0.02 eV across PBE+SOC, HSE+SOC, HSE. But their compounds have no lead, so SOC is checked on our own cells |
| Potential alignment by core levels; image-charge term estimated separately | The group's method; image term for V_I⁺ about 0.06 eV (ε ≈ 18, L ≈ 19.5 Å) |
| Folders renumbered: 05 reference phases, 06 defect formation, 07 diffusion, 08–10 slab | Steps in the order they will be run; the old 05–07 slab folders were empty |
| Step 5 set: Cs, Pb, solid I₂, CsI, PbI₂ (vc-relax), plus an isolated I₂ molecule as a cross-check of μ_I | Elements and binaries bound the region in every published CsPbX₃ diagram. Same PBEsol settings as CsPbI₃; metals with MV smearing and a denser k-mesh. Cs₄PbI₆ and CsPb₂I₅ wait for a CIF (no structure database reachable from here) |
| CsPbI₃ energy for ΔH_f: perfect 160-atom supercell ÷ 32 | Same cell and k-mesh as the defect cells, so errors cancel |
| NEB on 4 std40 nodes: one image at a time (`-v NI=1,NK=2`) | Two images at once overflowed 92 GB nodes (88 GB + swap, 23 Oct). One image on 160 cores: about 40–50 GB per node, each step about 15% slower than two at once |
| VASP counterpart of steps 1–5 in `vasp/` (supervisor's request) | Same physics as QE (PBEsol, no SOC, same k-meshes, cells, sites and force limit); PAW Cs_sv, Pb_d, I at 500 eV as in Arber 2025, so barriers compare one-to-one. One build (vasp632vtst) for all steps because NEB needs VTST. LREAL = Auto only in the 159/160-atom cells. Memory measured on the first job of each kind |
| Solid I₂ as the iodine reference; the molecule only as a check | Standard choice. Solid lies 0.34 eV per atom below the molecule (measured sublimation about 0.32 eV): PBEsol binds the solid correctly without dispersion |

## Open checks

1. **Mesh consistency.** Passed on forces: `pristine_222` converged on its first SCF, so every force component was below 0.010 eV/Å. Pressure not printed in a `relax` run.
2. **Time per supercell step.** About 10 min per SCF iteration on 2 nodes; first SCF 17 iterations, about 3 h.
3. **Final-state energies.** Each hop end point is a vacancy on a neighbouring site and should match the corresponding vacancy energy to a few meV.
4. **Distinct hops.** Settled: 10 symmetry-distinct bulk hops, 6 short (S1–S6, 4.41–4.60 Å) and 4 long (L1–L4, 4.80–5.93 Å), from the tight structure. Checked by symmetry and by a neighbour-graph fingerprint (544 I–I pairs fall into 10 classes). Table and figure in the README.
5. **Finite-size error.** One vacancy per 96 iodine sites. Affects absolute formation energies; cancels in site differences and barriers. Needs a correction (and the dielectric constant) or one larger-cell test.
6. **Spin-orbit coupling.** Not included. Planned single-point check on the vacancy cells in step 6 (SOC moves the Pb-6p conduction band by about 1 eV, so transition levels may shift). Neutral (`q0`) results are the least reliable.
7. **Comparison with Arber 2025** (Chem. Mater. 37, 4416), now read and the anchor paper. It gives one barrier per type of path: 0.34 eV (8d–8d), 0.35 eV (8d–4c), about 0.77 eV (4c–4c), and 4c 0.03 eV above 8d; the charge state is not stated. Our +1 result (both relaxations done, 16 Oct): E(8d) − E(4c) = −1.06 meV, same sign as Arber (8d lower) but about 30× smaller. q0 (converged 21 Oct): E(8d) − E(4c) = +40.4 meV, apical lower, opposite in sign to Arber. Compare both against the +0.03 eV, since Arber's charge state is unclear. Caveat (16 Oct): Arber's relaxed cell is nearly square in-plane (8.68 / 8.71 Å, 0.3% apart), unlike experiment (8.58 / 8.86) and every other 0 K relaxation (LDA, PBEsol, SCAN, PBE: 4–13% apart; ours 7.2%, matching Seidu's PBEsol). Less tilt can change the 4c/8d difference, so their +0.03 eV may not be a clean benchmark. Table in `Literatures/literature_review.md`. Possible test: our +1 pair on their lattice.
8. **Shallow donor.** Neutral cells: magnetisation 0; Fermi level 1.56 eV (4c) and 1.68 eV (8d) above the pristine VBM; rough ε(+/0) = E(0) − E(+1) − E_VBM = 1.61 eV (4c), 1.65 eV (8d), gap about 1.6 eV. Uncorrected; proper value in step 6.
9. **Paper C formation energies.** Not compared yet: needs step 5–6 (chemical potentials, alignment). Expect differences of a few tenths of an eV from settings alone (PBE+D3, experimental cell, 80 atoms).
10. **Questions for the supervisor.** Defect set for step 6 (four or all intrinsic); SOC in relaxations or as single points; whether the cubic α no-tilt reference is wanted.

## Commands that work

Use single quotes around patterns containing `!` or `$` in an interactive shell.

Progress table for a variable-cell relaxation (change `n`; for fixed-cell `relax` there is no pressure line):

```bash
awk -v n=6 '
/^!/           {e=$5}
/Total force/  {f=$4}
/P=/           {i++; E[i]=e; F[i]=f; P[i]=$6}
END {
  printf "%5s %18s %10s %12s %10s %9s\n","step","energy (Ry)","dE (meV)","F (Ry/Bohr)","F (eV/A)","P (kbar)"
  for (k=(i>n?i-n+1:1); k<=i; k++)
    printf "%5d %18.8f %10.3f %12.6f %10.4f %9.2f\n", k, E[k], (k>1?(E[k]-E[k-1])*13605.7:0), F[k], F[k]*25.711, P[k]
}' vcrelax.out
```

"Total force" is over all atoms and is larger than the largest single component, which is what the convergence test uses. Largest component of the last force block (replace 20 by the number of atoms):

```bash
grep -E "atom +[0-9]+ +type" relax.out | tail -20 | awk '{for(i=7;i<=9;i++){v=($i<0)?-$i:$i;if(v>m)m=v}}END{printf "%.6f Ry/Bohr = %.4f eV/A\n",m,m*25.711}'
```

Other checks:

```bash
grep -c '^!' relax.out                                   # geometry steps done
grep -E "bfgs converged|JOB DONE|convergence NOT achieved" relax.out
grep -E "running on|K-points division|number of k points" relax.out
grep "WALL" relax.out | tail -1
cat <job_name>.o<job_number>                             # job log, appears when the job ends
```

Turn a finished vc-relax into an input with the final structure:

```bash
awk '/^CELL_PARAMETERS/{exit} {print}' vcrelax.in > relaxed.in
awk '/Begin final coordinates/{f=1;next} /End final coordinates/{f=0} f && !/volume|density/' vcrelax.out >> relaxed.in
printf "\nK_POINTS automatic\n4 4 3  0 0 0\n" >> relaxed.in
```

Rebuild the supercell and vacancy inputs (needs Python with NumPy and ASE; run in WSL):

```bash
python3 qe/03_vacancies/build_defects.py qe/01_unitcell/tight/unit_tight_relaxed.in --out qe --pseudo-dir /public/home/daomduy/cspbi3/pseudo_pbesol   # from the repository root
```

NEB launch line, for later (images in parallel with `-ni`):

```bash
module load intel/intel2020
mpirun -np "$NP" -machinefile "$PBS_NODEFILE" ~/apps/q-e-qe-6.5/bin/neb.x -ni <images> -inp neb.in > neb.out
```

## Units

| From | To | Multiply by |
|---|---|---|
| Ry/Bohr | eV/Å | 25.711 |
| Ry | eV | 13.6057 |
| kbar | GPa | 0.1 |

Forces are quoted in eV/Å with Ry/Bohr in brackets.

## Working conventions

- Claude asks before writing or changing anything in this folder, and adds no files unless asked.
- Figures share one style. The two in `assets/` are 2720 × 1280 px, transparent background, Pb `#7F77DD`, I `#D85A30`, Cs `#1D9E75`, bonds `#888780`. Plots use `project_figures.mplstyle` (kept outside this folder so far).
- Viewing structures: VESTA. Boundary and Orientation are in the top **Objects** menu. To see the cubic skeleton of the γ cell, hide Cs and I and project along [1 1 0].
- Other documents made along the way and kept outside this folder: a general computing guide, a workflow guide for the convergence and relaxation scripts, and the reading-notes template for the three papers.
