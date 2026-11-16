#!/usr/bin/env python3
"""
Vineyard prefactors from the finite-difference runs made by vasp/make_vineyard.sh.

    nu* = (nu1 nu2 nu3 at a minimum) / (nu1 nu2 at the saddle, real modes only)

Only the moving iodine is free (3 modes), as in Smolders et al. (2024). The saddle must
show exactly one imaginary mode. Reads <hop>/vib/{start,saddle,end}/OUTCAR.
Usage: python3 tools/vineyard.py vasp/04_bulk_neb/q+1/S1 [S2 ...]
"""
import os
import re
import sys


def freqs(outcar):
    real, imag = [], []
    for line in open(outcar):
        m = re.match(r"\s*\d+\s+f(/i)?\s*=\s*([\d.]+)\s+THz", line)
        if m:
            (imag if m.group(1) else real).append(float(m.group(2)))
    return real[-3:] if len(real) >= 3 else real, imag


def main():
    for hop in sys.argv[1:]:
        f = {t: freqs(os.path.join(hop, "vib", t, "OUTCAR")) for t in ("start", "saddle", "end")}
        sr, si = f["saddle"]
        note = "" if len(si) == 1 and len(sr) == 2 else "  WARNING: saddle has %d imaginary, %d real modes" % (len(si), len(sr))
        prod_s = sr[0] * sr[1] if len(sr) >= 2 else float("nan")
        line = "%-4s saddle: imag %s, real %s THz" % (os.path.basename(hop.rstrip("/")),
                                                      " ".join("%.2f" % x for x in si), " ".join("%.2f" % x for x in sr))
        for t in ("start", "end"):
            r, i = f[t]
            if len(r) == 3 and not i:
                line += " | %s %s THz -> nu* %.2f THz" % (t, " ".join("%.2f" % x for x in r), r[0] * r[1] * r[2] / prod_s)
            else:
                line += " | %s: %d real, %d imaginary (check)" % (t, len(r), len(i))
        print(line + note)


if __name__ == "__main__":
    main()
