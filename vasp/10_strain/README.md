# Step 10, biaxial (001) strain

Method of Xu et al. (2019, SI Note 1): a and b fixed at a0(1+ε) and b0(1+ε), c scanned, atoms relaxed at fixed cell; the minimum of a fit of E(c) gives c(ε).

## 10a. Unit-cell E(c) scans (`unit/`)

Built by `python3 vasp/build_vasp.py strain`: ε = −1.0, 0.0, +0.5, +1.0% on a and b; c from −2.0% to +2.0% around c0 = 12.4020 Å in 0.5% steps (9 cells per ε, 36 in total). 20 atoms, 4×4×3 k-mesh, 500 eV, ISIF = 2. Memory a few GB per run (the unrelaxed unit cell used 0.39 GB per process).

Run, from `~/cspbi3/vasp` (one std40 node per ε, the nine cells one after the other):

```bash
bash make_potcar.sh 10_strain/unit/eps*/c*
C="c-2.0 c-1.5 c-1.0 c-0.5 c+0.0 c+0.5 c+1.0 c+1.5 c+2.0"
for e in -1.0 +0.0 +0.5 +1.0; do (cd 10_strain/unit/eps$e && qsub -N v_str$e -l nodes=1:ppn=40 -l walltime=48:00:00 -v DIRS="$C" ~/cspbi3/vasp/run_vasp.pbs); done
```

Collect the energies (column 4 = 1 if the relaxation converged):

```bash
cd ~/cspbi3/vasp/10_strain/unit
for e in eps*; do for c in $e/c*; do echo "${e#eps} ${c#*/c} $(grep F= $c/OSZICAR | tail -n 1 | awk '{print $3}') $(grep -c 'reached required accuracy' $c/OUTCAR)"; done; done > energies.txt
cat energies.txt
```

Fit (laptop): `python3 tools/fit_strain_c.py vasp/10_strain/unit/energies.txt --c0 12.4020 --out assets/strain_unit_Ec.png`

## Next

10b: δ-CsPbI₃ under the same strain (needs the δ structure). 10c: strained 2×2×2 supercells (perfect, V_I⁺ on 4c and 8d) at c(ε). 10d: NEBs S1, S2, S6 at each ε.
