# Working notes

Practical details that are not in the README: where things live, how jobs were run, decisions and their reasons, open checks, and commands that work. The README holds the science, the plan and the results.

Last updated: 2026-10-08

## Where things are

| Place | Path | Role |
|---|---|---|
| Main repository (WSL) | `~/Project-1` | The copy that pushes to GitHub (`origin`) |
| Desktop copy (Windows) | `C:\Users\ACER\OneDrive\Desktop\Project-1` = `/mnt/c/Users/ACER/OneDrive/Desktop/Project-1` | Shared with Claude for reading and editing. In WSL it is the remote `desktop` of the main repository |
| GitHub | `daoduywork-maker/gamma-CsPbI3-defects` (public) | Backup and sharing |
| Cluster work folder | `/public/home/daomduy/cspbi3` | Calculations |
| Cluster pseudopotentials | `/public/home/daomduy/cspbi3/pseudo_pbesol` | The three SSSP PBEsol files |
| Cluster job script | `/public/home/daomduy/cspbi3/run_qe.pbs` | Same file as `run_qe.pbs` in the repository root |
| Own Quantum ESPRESSO build | `/public/home/daomduy/apps/q-e-qe-6.5/bin/` | `pw.x`, `neb.x`, `pp.x`, version 6.5 |

Change flow: edit in the Desktop copy, review with `git diff`, commit there, then in WSL `cd ~/Project-1 && git pull desktop main && git push origin main`. To refresh the Desktop copy after work in WSL: `git pull` inside it.

## The cluster

- Login node is called `master`. Never run calculations there; compiling with `make -j 4` and one-second tests are acceptable.
- Scheduler: Torque/PBS with Maui. 44 nodes, 1984 cores: 40 nodes of 40 cores (queue `std40`) and 4 larger ones.
- Home and `/public/apps` are on a shared disk, visible from every node.
- `qstat` shows only your own jobs. Use `showq` to see everyone's, `checkjob <id>` for why a job waits, `showstart <id>` for the scheduler's estimate (pessimistic: it assumes every running job uses its full time limit).
- The cluster is usually 100% full with 160-core jobs that have 30 to 40 day limits. Nodes free up four at a time. The queue is first come, first served. The first one-node job waited about one day.
- Modules for Quantum ESPRESSO: `module load intel/intel2020` then `module load qe/qe-6.5`. The cluster's module has only `pw.x`. `neb.x` and `pp.x` come from the build in the home folder.
- Do not use `disk_io = 'nowf'` with QE 6.5.
- Jobs start with a clean environment, so the job script must load the modules itself.

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
| 217406–217410, the same five | 2 nodes each for `pristine` and +1, 3 nodes each for the neutral jobs | Submitted 9 Oct, queued |

**Incident, 9 Oct: jobs submitted without a memory check.** A std40 node has 92 GB. QE's estimate (printed in the first minute, `Estimated total dynamical RAM`) was 137 GB for the pristine and +1 supercells and 193 GB for the spin-polarised neutral ones. On one node the jobs ran out of memory: node32 showed 92 GB used plus 45 GB of swap, 92% of CPU time waiting on the disk, pw.x in state `D`. The +1 jobs were killed, the pristine one never finished its first SCF iteration. Fix: resubmit on 2 or 3 nodes; the job script takes the process count from the node list, so only `-l nodes=N:ppn=40` changes.

**Before every submission (memory checklist)**

1. Node limit: 92 GB per std40 node; plan for at most about 75 GB per node.
2. Job memory: from an earlier run of the same size, or start the job, read `grep "Estimated total dynamical RAM" *.out` within a minute or two, and stop it if total ÷ nodes is over about 75 GB.
3. Nodes = total ÷ 75 GB, rounded up. Spin-polarised (neutral) runs need about 1.4× the closed-shell ones.
4. After the start: `ssh <node> free -g`; swap use must stay near 0.
5. NEB: memory per image × images run at once (`-ni`). With about 136 GB per +1 image, running 7 images at once would need about 14 nodes; run fewer at a time, use fewer images, or test a lighter k-mesh first.

Submit command for the five (run from `~/cspbi3`, which holds `pristine_222`, `q+1`, `q0`):

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
| One 40-core node per job | Five independent jobs already run side by side; one node is easy to get. More nodes are justified for NEB, where images run in parallel |
| Five separate jobs, not one merged job | Same queue wait, run simultaneously, one failure does not stop the others |
| Walltime 360 h for supercells | Step time unknown; estimated a few hours per step. A killed job loses its run |
| Charge +1 first | Closed shell; the usual state of the iodine vacancy; least sensitive to spin-orbit coupling |
| Hop inputs removed from `build_defects.py` | Grouping hops by length may merge distinct hops. To be rebuilt after the literature is read |
| Tight relaxation done before building supercells | Soft result still had a and b drifting by 0.2 to 0.3% |
| All production runs with QE 6.5 on the cluster | One code version. QE 7.6 (laptop) and 6.5 gave the same total force on the same structure |
| No GitHub write access for Claude | User reviews and pushes every change |

## Open checks

1. **Mesh consistency.** First step of `pristine_222`: largest force component below about 0.01 eV/Å and pressure within about 0.5 kbar means the 4×4×3 choice is harmless.
2. **Time per supercell step.** Needed to judge the walltime and to cost the NEB runs.
3. **Final-state energies.** Each hop end point is a vacancy on a neighbouring site and should match the corresponding vacancy energy to a few meV.
4. **Distinct hops.** Apical iodine lies on a mirror plane, so its 8 neighbours form 4 pairs: up to 4 distinct apical-equatorial hops, not 3. The 4.55 Å group (4 neighbours) is probably two hops. Neighbour distances from the soft structure: apical to equatorial 4.44 (×2), 4.45 (×2), 4.55 (×4) Å; equatorial to equatorial 4.42 (×2), 4.59 (×2) Å. No direct apical-apical hop (over 6 Å).
5. **Finite-size error.** One vacancy per 96 iodine sites. Affects absolute formation energies; cancels in site differences and barriers. Needs a correction (and the dielectric constant) or one larger-cell test.
6. **Spin-orbit coupling.** Not included. Planned single-point check on the two +1 vacancy structures. Neutral (`q0`) results are the least reliable.
7. **Paper A** (Chem. Mater. 37, 4416, 2025) has not been read by Claude; it may already contain the bulk barriers.
8. **Seidu et al. 2021** surface phase diagrams: check coverage before the step 8 analysis.

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
python3 03_vacancies/build_defects.py 01_unitcell/tight/unit_tight_relaxed.in --pseudo-dir /public/home/daomduy/cspbi3/pseudo_pbesol   # from the repository root
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
