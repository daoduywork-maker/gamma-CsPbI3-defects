# Step 7, slab thickness test (VASP)

Symmetric CsI-terminated (001) slabs of γ-CsPbI₃, 1×1 in-plane (a, b fixed at the relaxed bulk values), 15 Å vacuum, atoms relaxed (ISIF = 2), k-mesh 4×4×1. Built by `python3 vasp/build_vasp.py slab`; details in `slabs_report.txt`.

| Folder | Layers | Atoms | Composition |
|---|---|---|---|
| L07 | 4 CsI + 3 PbI₂ | 34 | 6 CsPbI₃ + 2 CsI |
| L09 | 5 CsI + 4 PbI₂ | 44 | 8 CsPbI₃ + 2 CsI |
| L11 | 6 CsI + 5 PbI₂ | 54 | 10 CsPbI₃ + 2 CsI |

Both faces are equivalent by symmetry, so no dipole correction is needed.

Pass criteria (choose the thinnest slab that passes, then build it 2×2 in-plane for the vacancy):
1. E(L09) − E(L07) and E(L11) − E(L09) equal 2 CsPbI₃ of bulk (2 × E_unit/4, E_unit = −60.79013171 eV) to within a few meV.
2. Middle layer: Pb–I bonds and octahedral tilts match the bulk.

Run (from `~/cspbi3/vasp/07_slab`, after `make_potcar.sh`): one std40 node, the three slabs one after the other. Memory: a few GB (54 atoms at most).
