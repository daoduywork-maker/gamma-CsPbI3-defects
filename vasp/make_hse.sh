#!/bin/bash
# HSE06 + spin-orbit coupling single point at Gamma on a relaxed VASP structure (no Python needed).
#   bash ~/cspbi3/vasp/make_hse.sh 02_pristine 03_vacancies/q+1/vac_I_apical ...
# For each folder: writes <folder>/hse_soc/ with POSCAR (the relaxed structure: soc_relax/CONTCAR
# if that relaxation exists and FROM_SOC=1, otherwise the PBEsol CONTCAR), POTCAR, a Gamma-only
# KPOINTS and an INCAR made from the folder's INCAR (relaxation, spin and parallel tags removed):
#   HSE06 (GGA = PE, AEXX = 0.25, HFSCREEN = 0.2) on the PBEsol geometry, LSORBIT, NSW = 0.
# As in the group's workflow (Xu 2017/2019): relaxed geometry, then HSE+SOC single points at Gamma.
# Run with the non-collinear build, one cell per job:
#   cd <folder>/hse_soc && qsub -N hse -l walltime=96:00:00 -v VASP_EXE=vasp_ncl ~/cspbi3/vasp/run_vasp.pbs
# AEXX can be changed: AEXX=0.35 bash make_hse.sh ...  (HSE06 with SOC tends to underestimate
# the CsPbI3 gap; a larger fraction is a common fix, to be agreed with the supervisor).

AEXX="${AEXX:-0.25}"
for d in "$@"; do
  src="$d/CONTCAR"
  [ "${FROM_SOC:-0}" = 1 ] && [ -s "$d/soc_relax/CONTCAR" ] && src="$d/soc_relax/CONTCAR"
  [ -s "$src" ] || { echo "$d: no $src"; continue; }
  [ -f "$d/POTCAR" ] || { echo "$d: no POTCAR"; continue; }
  s="$d/hse_soc"; mkdir -p "$s"
  cp "$src" "$s/POSCAR"; cp "$d/POTCAR" "$s/"
  printf "Gamma only\n0\nGamma\n1 1 1\n0 0 0\n" > "$s/KPOINTS"
  n=$(sed -n 7p "$s/POSCAR" | awk '{t=0; for(i=1;i<=NF;i++) t+=$i; print t}')
  {
    sed -e 's/;.*$//' "$d/INCAR" | grep -v -E '^ *(IBRION|ISIF|NSW|EDIFFG|POTIM|ISPIN|MAGMOM|KPAR|NCORE|GGA|ALGO|NELM|EDIFF) *=' \
      | grep -v -E '^# *(Relaxation|Odd electron|Parallelisation)'
    echo ""
    echo "# HSE06 + spin-orbit coupling single point at Gamma (geometry from $src)"
    echo "GGA      = PE                ! HSE06 is built on PBE"
    echo "LHFCALC  = .TRUE."
    echo "HFSCREEN = 0.2"
    echo "AEXX     = $AEXX"
    echo "PRECFOCK = Fast              ! coarser grid for the exchange term (saves memory)"
    echo "ALGO     = Damped"
    echo "TIME     = 0.4"
    echo "NELM     = 150"
    echo "EDIFF    = 1E-5              ! eV; enough for meV differences, saves HSE iterations"
    echo "NSW      = 0"
    echo "IBRION   = -1"
    echo "LSORBIT  = .TRUE."
    echo "MAGMOM   = $((3*n))*0"
    echo "GGA_COMPAT = .FALSE."
    echo "LMAXMIX  = 4"
    echo "NCORE    = 1                 ! hybrid functionals: one band per core"
  } > "$s/INCAR"
  sed -i "s/^SYSTEM = \(.*\)$/SYSTEM = \1, HSE06+SOC Gamma/" "$s/INCAR"
  echo "$s: $n atoms, from $src, AEXX = $AEXX"
done
