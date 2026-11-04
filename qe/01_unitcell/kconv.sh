#!/usr/bin/env bash
# k-point and cutoff convergence for gamma-CsPbI3.
# Runs single-point SCF calculations on the fixed starting structure
# (no relaxation), then prints total energy per atom for each setting.
#
# Usage:  bash kconv.sh            (edit PW and NP below first)
# Needs:  gamma_CsPbI3_vcrelax.in in the same folder.

set -euo pipefail

PW="pw.x"          # path to pw.x
NP=6              # MPI processes
BASE="gamma_CsPbI3_vcrelax.in"
NAT=20

mkdir -p conv

make_input () {    # $1 = tag, $2 = "kx ky kz", $3 = ecutwfc
  local tag=$1 kpts=$2 ecut=$3
  local erho
  erho=$(awk -v e="$ecut" 'BEGIN{printf "%.1f", 8*e}')
  # Take everything above K_POINTS, switch to scf, set cutoffs and prefix
  sed '/^K_POINTS/,$d' "$BASE" \
    | sed "s/calculation *= *'vc-relax'/calculation   = 'scf'/" \
    | sed "s/prefix *= *'[^']*'/prefix        = 'conv_${tag}'/" \
    | sed "s/ecutwfc *= *[0-9.]*/ecutwfc     = ${ecut}/" \
    | sed "s/ecutrho *= *[0-9.]*/ecutrho     = ${erho}/" \
    > "conv/${tag}.in"
  printf 'K_POINTS automatic\n%s  0 0 0\n' "$kpts" >> "conv/${tag}.in"
}

run () {           # $1 = tag
  if [ ! -f "conv/$1.out" ] || ! grep -q "JOB DONE" "conv/$1.out"; then
    mpirun -np "$NP" "$PW" -in "conv/$1.in" > "conv/$1.out"
  fi
}

report () {        # $1 = tag, $2 = label
  local e
  e=$(grep '^!' "conv/$1.out" | tail -1 | awk '{print $5}')
  awk -v e="$e" -v n="$NAT" -v l="$2" \
    'BEGIN{printf "%-14s %16.8f Ry   %12.3f meV/atom\n", l, e, e*13605.698/n}'
}

echo "== k-point convergence at ecutwfc = 50 Ry =="
for k in "2 2 1" "3 3 2" "4 4 3" "5 5 4" "6 6 4"; do
  tag="k$(echo "$k" | tr -d ' ')"
  make_input "$tag" "$k" 50
  run "$tag"
  report "$tag" "k = $k"
done

echo
echo "== cutoff convergence at k = 4 4 3 =="
for e in 40 50 60 70 80; do
  tag="e${e}"
  make_input "$tag" "4 4 3" "$e"
  run "$tag"
  report "$tag" "ecutwfc = $e"
done

echo
echo "Converged when the meV/atom column changes by less than about 1"
echo "between one setting and the next."