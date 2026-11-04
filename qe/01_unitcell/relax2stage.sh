#!/usr/bin/env bash
# Two-stage variable-cell relaxation of gamma-CsPbI3 with Quantum ESPRESSO.
#
#   Stage 1: coarse k-mesh (3x3x2), starts from the base input structure.
#   Stage 2: converged k-mesh (4x4x3), starts from the stage-1 result.
#
# Usage (from the folder that holds the base input):
#     bash relax2stage.sh
#
# Produces:
#     stage1_k332/   input, output and scratch of stage 1
#     stage2_k443/   input, output and scratch of stage 2
#     final/         relaxed structure: ready-to-run scf input, structure
#                    blocks, and a CIF if ASE is installed
#     relax_summary.txt
#
# Safe to re-run: a stage that already finished is skipped.

set -euo pipefail

# ---------------- settings you may need to edit ----------------
PW="${PW:-pw.x}"                         # path to pw.x
NP="${NP:-6}"                            # MPI processes
LAUNCH="${LAUNCH-mpirun -np $NP}"        # set LAUNCH="" to run pw.x directly
BASE="${BASE:-gamma_CsPbI3_vcrelax.in}"  # base input (structure + settings)
ECUTWFC=60.0                             # from the convergence test
ECUTRHO=480.0
K1="3 3 2"                               # stage 1 mesh
K2="4 4 3"                               # stage 2 mesh
# Experimental cell (Sutton et al. 2018, 293 K), for comparison only
EXP_A=8.5766; EXP_B=8.8561; EXP_C=12.4722
# ----------------------------------------------------------------

TOP="$PWD"
S1="stage1_k332"
S2="stage2_k443"
SUMMARY="$TOP/relax_summary.txt"

[ -f "$BASE" ] || { echo "Base input '$BASE' not found in $TOP"; exit 1; }

# Make pseudo_dir absolute so it still works from the stage folders
PSEUDO=$(grep -E "^\s*pseudo_dir" "$BASE" | sed -E "s/.*=\s*'([^']*)'.*/\1/")
case "$PSEUDO" in
  /*) ;;
  *)  PSEUDO="$TOP/${PSEUDO#./}" ;;
esac
[ -d "$PSEUDO" ] || { echo "pseudo_dir '$PSEUDO' does not exist"; exit 1; }

# ---- helpers -----------------------------------------------------

header () {   # $1 = prefix ; prints namelists + ATOMIC_SPECIES from BASE
  sed '/^CELL_PARAMETERS/,$d' "$BASE" \
    | sed -E "s|calculation *= *'[^']*'|calculation   = '$2'|" \
    | sed -E "s|prefix *= *'[^']*'|prefix        = '$1'|" \
    | sed -E "s|pseudo_dir *= *'[^']*'|pseudo_dir    = '$PSEUDO'|" \
    | sed -E "s|outdir *= *'[^']*'|outdir        = './tmp'|" \
    | sed -E "s|ecutwfc *= *[0-9.]+|ecutwfc     = $ECUTWFC|" \
    | sed -E "s|ecutrho *= *[0-9.]+|ecutrho     = $ECUTRHO|"
}

structure_from_input () {   # CELL_PARAMETERS + ATOMIC_POSITIONS of an input
  sed -n '/^CELL_PARAMETERS/,/^K_POINTS/p' "$1" | sed '/^K_POINTS/d'
}

structure_from_output () {  # last cell + last positions printed in an output
  local out=$1
  local unit
  unit=$(grep "^CELL_PARAMETERS" "$out" | tail -1)
  case "$unit" in
    *angstrom*) ;;
    *) echo "Unexpected cell units in $out: '$unit'" >&2; return 1 ;;
  esac
  echo "CELL_PARAMETERS angstrom"
  awk '/^CELL_PARAMETERS/{n=NR} {l[NR]=$0} END{for(i=n+1;i<=n+3;i++)print l[i]}' "$out"
  echo
  echo "ATOMIC_POSITIONS crystal"
  awk '/^ATOMIC_POSITIONS/{n=NR} {l[NR]=$0}
       END{for(i=n+1;i<=NR;i++){split(l[i],f," "); if(length(f)<4)break; print l[i]}}' "$out"
  echo
}

finished () {  # $1 = output file
  [ -f "$1" ] && grep -q "JOB DONE" "$1" && grep -q "End final coordinates" "$1"
}

run_stage () {  # $1 = folder
  ( cd "$1"
    echo "[$(date '+%F %T')] running $1 ..."
    $LAUNCH "$PW" -in vcrelax.in > vcrelax.out
    echo "[$(date '+%F %T')] $1 ended" )
}

cell_lengths () {  # reads a structure block on stdin, prints "a b c volume"
  awk '/^CELL_PARAMETERS/{r=1;next}
       r>=1&&r<=3&&NF==3{v[r,1]=$1;v[r,2]=$2;v[r,3]=$3;r++}
       END{
         for(i=1;i<=3;i++)L[i]=sqrt(v[i,1]^2+v[i,2]^2+v[i,3]^2)
         vol=v[1,1]*(v[2,2]*v[3,3]-v[2,3]*v[3,2]) \
            -v[1,2]*(v[2,1]*v[3,3]-v[2,3]*v[3,1]) \
            +v[1,3]*(v[2,1]*v[3,2]-v[2,2]*v[3,1])
         if(vol<0)vol=-vol
         printf "%.4f %.4f %.4f %.3f\n",L[1],L[2],L[3],vol}'
}

stage_report () {  # $1 = label, $2 = output file
  local out=$2
  local nsteps e_first e_last p_last f_last wall conv
  nsteps=$(grep -c '^!' "$out" || true)
  e_first=$(grep '^!' "$out" | head -1 | awk '{print $5}')
  e_last=$(grep '^!' "$out" | tail -1 | awk '{print $5}')
  p_last=$(grep 'P=' "$out" | tail -1 | awk '{print $NF}')
  f_last=$(grep 'Total force' "$out" | tail -1 | awk '{print $4}')
  wall=$(grep 'PWSCF.*WALL' "$out" | tail -1 | sed -E 's/.*CPU *//; s/ *WALL.*//')
  if grep -q "bfgs converged" "$out"; then conv="yes"; else conv="NO"; fi
  {
    echo "$1"
    echo "  output file            : $out"
    echo "  converged (bfgs)       : $conv"
    echo "  energy evaluations     : $nsteps"
    echo "  first energy (Ry)      : $e_first"
    echo "  final energy (Ry)      : $e_last"
    awk -v a="$e_first" -v b="$e_last" \
      'BEGIN{printf "  energy gained (meV/atom): %.3f\n",(a-b)*13605.698/20}'
    echo "  final pressure (kbar)  : $p_last"
    echo "  final total force (Ry/Bohr): $f_last"
    echo "  wall time              : $wall"
    echo
  } >> "$SUMMARY"
}

# ---- stage 1 -----------------------------------------------------

mkdir -p "$S1" "$S2" final

if finished "$S1/vcrelax.out"; then
  echo "Stage 1 already finished, skipping."
else
  { header "cspbi3_gamma_s1" "vc-relax"
    structure_from_input "$BASE"
    printf 'K_POINTS automatic\n%s  0 0 0\n' "$K1"
  } > "$S1/vcrelax.in"
  run_stage "$S1"
fi

if ! finished "$S1/vcrelax.out"; then
  echo "Stage 1 did not finish cleanly. See $S1/vcrelax.out (last lines):"
  tail -15 "$S1/vcrelax.out" || true
  exit 1
fi

# ---- stage 2 -----------------------------------------------------

if finished "$S2/vcrelax.out"; then
  echo "Stage 2 already finished, skipping."
else
  { header "cspbi3_gamma_s2" "vc-relax"
    structure_from_output "$S1/vcrelax.out"
    printf 'K_POINTS automatic\n%s  0 0 0\n' "$K2"
  } > "$S2/vcrelax.in"
  run_stage "$S2"
fi

if ! finished "$S2/vcrelax.out"; then
  echo "Stage 2 did not finish cleanly. See $S2/vcrelax.out (last lines):"
  tail -15 "$S2/vcrelax.out" || true
  exit 1
fi

# ---- export final structure -------------------------------------

structure_from_output "$S2/vcrelax.out" > final/structure_blocks.txt

{ header "cspbi3_gamma_relaxed" "scf"
  cat final/structure_blocks.txt
  printf 'K_POINTS automatic\n%s  0 0 0\n' "$K2"
} > final/gamma_CsPbI3_relaxed_scf.in

CIF_NOTE="not written (python3 with ASE not found)"
if command -v python3 >/dev/null 2>&1 && python3 -c "import ase" >/dev/null 2>&1; then
  if python3 - <<'PY' >/dev/null 2>&1
from ase.io import read, write
a = read("final/gamma_CsPbI3_relaxed_scf.in", format="espresso-in")
write("final/gamma_CsPbI3_relaxed.cif", a)
PY
  then CIF_NOTE="final/gamma_CsPbI3_relaxed.cif"; fi
fi

# ---- summary ------------------------------------------------------

read -r A0 B0 C0 V0 < <(structure_from_input "$BASE" | cell_lengths)
read -r A1 B1 C1 V1 < <(structure_from_output "$S1/vcrelax.out" | cell_lengths)
read -r A2 B2 C2 V2 < <(cell_lengths < final/structure_blocks.txt)

{
  echo "gamma-CsPbI3 two-stage variable-cell relaxation"
  echo "written: $(date '+%F %T')"
  echo "folder : $TOP"
  echo
  echo "Settings"
  echo "  ecutwfc / ecutrho : $ECUTWFC / $ECUTRHO Ry"
  echo "  stage 1 k-mesh    : $K1"
  echo "  stage 2 k-mesh    : $K2"
  echo "  pseudo_dir        : $PSEUDO"
  echo
} > "$SUMMARY"

stage_report "Stage 1 (k = $K1)" "$S1/vcrelax.out"
stage_report "Stage 2 (k = $K2)" "$S2/vcrelax.out"

{
  echo "Lattice parameters (Angstrom) and cell volume (Angstrom^3)"
  printf "  %-22s %9s %9s %9s %10s\n" "" "a" "b" "c" "volume"
  printf "  %-22s %9.4f %9.4f %9.4f %10.3f\n" "start (base input)" "$A0" "$B0" "$C0" "$V0"
  printf "  %-22s %9.4f %9.4f %9.4f %10.3f\n" "after stage 1" "$A1" "$B1" "$C1" "$V1"
  printf "  %-22s %9.4f %9.4f %9.4f %10.3f\n" "after stage 2 (final)" "$A2" "$B2" "$C2" "$V2"
  awk -v a="$A2" -v b="$B2" -v c="$C2" -v ea="$EXP_A" -v eb="$EXP_B" -v ec="$EXP_C" \
    'BEGIN{printf "  %-22s %+8.2f%% %+8.2f%% %+8.2f%% %+9.2f%%\n","final vs experiment",
           100*(a-ea)/ea,100*(b-eb)/eb,100*(c-ec)/ec,100*(a*b*c-ea*eb*ec)/(ea*eb*ec)}'
  echo "  (experiment: a=$EXP_A b=$EXP_B c=$EXP_C at 293 K; the last column"
  echo "   assumes an orthorhombic cell)"
  echo
  awk -v a="$A1" -v b="$B1" -v c="$C1" -v x="$A2" -v y="$B2" -v z="$C2" \
    'BEGIN{printf "Change from stage 1 to stage 2: a %+.3f%%, b %+.3f%%, c %+.3f%%\n",
           100*(x-a)/a,100*(y-b)/b,100*(z-c)/c}'
  echo
} >> "$SUMMARY"

# Pb-I-Pb angles and Pb-I bond lengths (needs python3 + numpy)
if command -v python3 >/dev/null 2>&1 && python3 -c "import numpy" >/dev/null 2>&1; then
python3 - "$BASE" final/gamma_CsPbI3_relaxed_scf.in >> "$SUMMARY" <<'PY'
import sys
import numpy as np

def load(path):
    lines = open(path).read().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith("CELL_PARAMETERS"))
    cell = np.array([[float(x) for x in lines[i + j].split()] for j in (1, 2, 3)])
    j = next(k for k, l in enumerate(lines) if l.startswith("ATOMIC_POSITIONS"))
    sym, frac = [], []
    for l in lines[j + 1:]:
        p = l.split()
        if len(p) < 4:
            break
        sym.append(p[0]); frac.append([float(x) for x in p[1:4]])
    return cell, np.array(sym), np.array(frac)

def geometry(path):
    cell, sym, frac = load(path)
    pb, io = frac[sym == "Pb"], frac[sym == "I"]
    angles, bonds = [], []
    for x in io:
        d = pb - x
        d -= np.round(d)
        # include periodic images so both Pb neighbours are found
        shifts = np.array([[i, j, k] for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)])
        vecs = (d[:, None, :] + shifts[None, :, :]).reshape(-1, 3) @ cell
        dist = np.linalg.norm(vecs, axis=1)
        o = np.argsort(dist)[:2]
        v1, v2 = vecs[o[0]], vecs[o[1]]
        cosang = v1 @ v2 / (dist[o[0]] * dist[o[1]])
        angles.append(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
        bonds += [dist[o[0]], dist[o[1]]]
    return np.array(angles), np.array(bonds)

print("Octahedral geometry")
print("  %-22s %14s %14s %16s" % ("", "Pb-I-Pb min", "Pb-I-Pb max", "Pb-I range (A)"))
for label, path in (("start (base input)", sys.argv[1]), ("final", sys.argv[2])):
    a, b = geometry(path)
    print("  %-22s %13.2f° %13.2f° %8.3f-%.3f" % (label, a.min(), a.max(), b.min(), b.max()))
print("  (180° means no tilt; smaller angles mean stronger tilting)")
print()
PY
else
  echo "Octahedral geometry: skipped (python3 with numpy not found)" >> "$SUMMARY"
  echo >> "$SUMMARY"
fi

{
  echo "Files"
  echo "  relaxed structure, scf-ready input : final/gamma_CsPbI3_relaxed_scf.in"
  echo "  structure blocks only              : final/structure_blocks.txt"
  echo "  CIF                                : $CIF_NOTE"
} >> "$SUMMARY"

echo
cat "$SUMMARY"