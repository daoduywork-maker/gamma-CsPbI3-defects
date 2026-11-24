#!/bin/bash
# tight-force restarts of S2 (run from ~/cspbi3/vasp)
set -e
for i in 00 05; do mkdir -p 09_convergence/S2_tight/eps-1.0/$i; cp 06_strain/neb/eps-1.0/q+1/S2/$i/POSCAR 09_convergence/S2_tight/eps-1.0/$i/; done
for i in 01 02 03 04; do mkdir -p 09_convergence/S2_tight/eps-1.0/$i; cp 06_strain/neb/eps-1.0/q+1/S2/$i/CONTCAR 09_convergence/S2_tight/eps-1.0/$i/POSCAR; done
cp 06_strain/neb/eps-1.0/q+1/S2/POTCAR 09_convergence/S2_tight/eps-1.0/
for i in 00 05; do mkdir -p 09_convergence/S2_tight/eps+0.0/$i; cp 04_bulk_neb/q+1/S2/$i/POSCAR 09_convergence/S2_tight/eps+0.0/$i/; done
for i in 01 02 03 04; do mkdir -p 09_convergence/S2_tight/eps+0.0/$i; cp 04_bulk_neb/q+1/S2/$i/CONTCAR 09_convergence/S2_tight/eps+0.0/$i/POSCAR; done
cp 04_bulk_neb/q+1/S2/POTCAR 09_convergence/S2_tight/eps+0.0/
for i in 00 05; do mkdir -p 09_convergence/S2_tight/eps+1.0/$i; cp 06_strain/neb/eps+1.0/q+1/S2/$i/POSCAR 09_convergence/S2_tight/eps+1.0/$i/; done
for i in 01 02 03 04; do mkdir -p 09_convergence/S2_tight/eps+1.0/$i; cp 06_strain/neb/eps+1.0/q+1/S2/$i/CONTCAR 09_convergence/S2_tight/eps+1.0/$i/POSCAR; done
cp 06_strain/neb/eps+1.0/q+1/S2/POTCAR 09_convergence/S2_tight/eps+1.0/
grep EDIFFG 09_convergence/S2_tight/*/INCAR
