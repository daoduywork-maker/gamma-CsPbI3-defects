#!/bin/bash
# Build POTCAR from the species line of POSCAR, on the cluster (no Python needed).
#   bash ~/cspbi3/vasp/make_potcar.sh                 (in one folder)
#   bash ~/cspbi3/vasp/make_potcar.sh dir1 dir2 ...   (several folders; NEB: the hop folder,
#                                                     POTCAR goes next to 00 ... 05)
# Potentials: Cs_sv, Pb_d, I (PBE PAW; GGA = PS in INCAR turns them into PBEsol).
POT="${POT:-/public/shared-data/pot/vasp/544/PAW_PBE}"
declare -A MAP=([Cs]=Cs_sv [Pb]=Pb_d [I]=I)
declare -A ZEXP=([Cs]=9 [Pb]=14 [I]=7)

for d in "${@:-.}"; do
  P="$d/POSCAR"; [ -f "$P" ] || P="$d/00/POSCAR"
  [ -f "$P" ] || { echo "$d: no POSCAR"; continue; }
  species=$(sed -n 6p "$P")
  : > "$d/POTCAR"
  for s in $species; do
    f="$POT/${MAP[$s]}/POTCAR"
    [ -f "$f" ] || { echo "missing $f"; exit 1; }
    cat "$f" >> "$d/POTCAR"
    z=$(awk '/ZVAL/{print int($6); exit}' "$f")
    [ "$z" = "${ZEXP[$s]}" ] || echo "WARNING: $s ZVAL = $z, expected ${ZEXP[$s]} (NELECT in INCAR assumes ${ZEXP[$s]})"
  done
  echo "$d: POTCAR for $species ($(grep -c TITEL "$d/POTCAR") potentials)"
done
