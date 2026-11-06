#!/bin/bash
# Spin-orbit coupling (SOC) single point on a relaxed VASP structure (no Python needed).
#   bash ~/cspbi3/vasp/make_soc.sh 02_pristine 03_vacancies/q+1/vac_I_apical ...
# For each folder: writes <folder>/soc/ with POSCAR (= the relaxed CONTCAR), KPOINTS, POTCAR
# and an INCAR made from the folder's INCAR: relaxation and spin tags removed, then
#   NSW = 0, LSORBIT, non-magnetic start (MAGMOM = 3 x N x 0), GGA_COMPAT = .FALSE., LMAXMIX = 4.
# Run with the non-collinear build:
#   cd <folder>/soc && qsub -N soc -v VASP_EXE=vasp_ncl ~/cspbi3/vasp/run_vasp.pbs
# Several folders in one job (one after the other), from ~/cspbi3/vasp:
#   qsub -N soc -v VASP_EXE=vasp_ncl,DIRS="02_pristine/soc 03_vacancies/q+1/vac_I_apical/soc" run_vasp.pbs

for d in "$@"; do
  [ -s "$d/CONTCAR" ] || { echo "$d: no CONTCAR (relaxation not finished?)"; continue; }
  [ -f "$d/POTCAR" ]  || { echo "$d: no POTCAR"; continue; }
  s="$d/soc"; mkdir -p "$s"
  cp "$d/CONTCAR" "$s/POSCAR"; cp "$d/KPOINTS" "$d/POTCAR" "$s/"
  n=$(sed -n 7p "$s/POSCAR" | awk '{t=0; for(i=1;i<=NF;i++) t+=$i; print t}')
  {
    sed -e 's/;.*$//' "$d/INCAR" | grep -v -E '^ *(IBRION|ISIF|NSW|EDIFFG|POTIM|ISPIN|MAGMOM|KPAR|NCORE) *=' \
      | grep -v -E '^# *(Relaxation|Odd electron|Parallelisation)'
    echo ""
    echo "# Spin-orbit coupling single point on the relaxed structure"
    echo "NSW      = 0"
    echo "IBRION   = -1"
    echo "LSORBIT  = .TRUE."
    echo "MAGMOM   = $((3*n))*0       ! non-magnetic start (the collinear runs ended at 0 muB)"
    echo "GGA_COMPAT = .FALSE.         ! recommended with SOC"
    echo "LMAXMIX  = 4                 ! d electrons (Pb_d)"
    echo "NCORE    = 10"
  } > "$s/INCAR"
  sed -i 's/^SYSTEM = \(.*\)$/SYSTEM = \1, SOC single point/' "$s/INCAR"
  echo "$s: $n atoms, INCAR with LSORBIT written"
done
