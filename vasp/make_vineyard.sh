#!/bin/bash
# Vineyard prefactor inputs (moving ion only, as Smolders et al. 2024) for converged VASP NEB hops.
#   cd ~/cspbi3/vasp/04_bulk_neb/q+1 && bash ~/cspbi3/vasp/make_vineyard.sh S1:84 S2:114 S4:66 S5:79
# <hop>:<moving atom, 1-based POSCAR order, from the hop's report.txt>
# For each hop: <hop>/vib/start (= 00/POSCAR), end (= 05/POSCAR), saddle (CONTCAR of the highest
# image 01-04 by its last OSZICAR energy). Only the moving iodine is free (selective dynamics);
# finite differences IBRION = 5, NFREE = 2, POTIM = 0.015 A give its 3 frequencies.
# nu* = (nu1 nu2 nu3 at the start) / (nu1 nu2 at the saddle, the real ones); tools/vineyard.py.
for arg in "$@"; do
  h=${arg%%:*}; k=${arg##*:}
  [ -f "$h/INCAR" ] || { echo "$h: no INCAR"; continue; }
  best=""; emax=-1e9
  for i in 01 02 03 04; do
    e=$(grep F= "$h/$i/OSZICAR" 2>/dev/null | tail -n 1 | awk '{print $5}')
    [ -n "$e" ] && awk -v e="$e" -v m="$emax" 'BEGIN{exit !(e+0>m+0)}' && { emax=$e; best=$i; }
  done
  [ -n "$best" ] && [ -s "$h/$best/CONTCAR" ] || { echo "$h: no converged image CONTCAR"; continue; }
  for t in start saddle end; do
    case $t in start) src=$h/00/POSCAR;; end) src=$h/05/POSCAR;; saddle) src=$h/$best/CONTCAR;; esac
    d=$h/vib/$t; mkdir -p "$d"
    awk -v k="$k" 'NR<=7{print; if(NR==7){n=0; for(i=1;i<=NF;i++) n+=$i}; next}
        NR==8 && $0 ~ /^[Ss]/ {next}
        !c && /^[DdCc]/ {print "Selective dynamics"; print; c=1; next}
        c && j<n {j++; printf "  %s  %s  %s  %s\n", $1, $2, $3, (j==k ? "T T T" : "F F F")}' "$src" > "$d/POSCAR"
    cp "$h/KPOINTS" "$h/POTCAR" "$d/" 2>/dev/null || cp "$h/KPOINTS" "$d/"
    { sed -e 's/;.*$//' "$h/INCAR" | grep -v -E '^ *(IMAGES|SPRING|LCLIMB|ICHAIN|IBRION|POTIM|IOPT|EDIFFG|NSW|ISIF|EDIFF|NCORE|KPAR) *=' \
        | grep -v -E '^# *(NEB|Parallelisation)'
      echo ""
      echo "# Vineyard: frequencies of the moving iodine (atom $k), finite differences"
      echo "IBRION   = 5"
      echo "NFREE    = 2"
      echo "POTIM    = 0.015"
      echo "NSW      = 1"
      echo "ISIF     = 2"
      echo "EDIFF    = 1E-7"
      echo "NCORE    = 10"
    } > "$d/INCAR"
    sed -i "s/^SYSTEM = \(.*\)$/SYSTEM = \1, Vineyard $t/" "$d/INCAR"
    nT=$(grep -c 'T T T' "$d/POSCAR")
    echo "$d: from $src, free atoms $nT (atom $k)"
  done
done
