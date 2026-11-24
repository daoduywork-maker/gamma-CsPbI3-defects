#!/bin/bash
# copy the relaxed structures into vasp/08_fnv (run from ~/cspbi3/vasp)
set -e
cp 06_strain/super/eps-1.0/pristine/CONTCAR 08_fnv/eps-1.0/perfect/POSCAR
cp 06_strain/super/eps-1.0/q+1/vac_I_equatorial/CONTCAR 08_fnv/eps-1.0/vac/POSCAR
cp 06_strain/super/eps-0.5/pristine/CONTCAR 08_fnv/eps-0.5/perfect/POSCAR
cp 06_strain/super/eps-0.5/q+1/vac_I_apical/CONTCAR 08_fnv/eps-0.5/vac/POSCAR
cp 02_pristine/CONTCAR 08_fnv/eps+0.0/perfect/POSCAR
cp 03_vacancies/q+1/vac_I_apical/CONTCAR 08_fnv/eps+0.0/vac/POSCAR
cp 06_strain/super/eps+0.5/pristine/CONTCAR 08_fnv/eps+0.5/perfect/POSCAR
cp 06_strain/super/eps+0.5/q+1/vac_I_equatorial/CONTCAR 08_fnv/eps+0.5/vac/POSCAR
cp 06_strain/super/eps+1.0/pristine/CONTCAR 08_fnv/eps+1.0/perfect/POSCAR
cp 06_strain/super/eps+1.0/q+1/vac_I_equatorial/CONTCAR 08_fnv/eps+1.0/vac/POSCAR
ls -la 08_fnv/*/*/POSCAR | wc -l   # expect 10
