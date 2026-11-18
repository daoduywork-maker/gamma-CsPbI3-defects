#!/usr/bin/env python3
"""
All +1 NEB profiles in one figure (2 x 4 panels, shared energy axis), ordered by barrier.

    python3 tools/plot_neb_all.py            # -> assets/neb_all_qp1_vasp.png

Reads vasp/04_bulk_neb/q+1/<hop>/neb_data.txt and the image CONTCARs through tools/plot_neb.py.
A hop without neb_data.txt gets an empty panel marked "data not copied yet".
Energies relative to the start image (8d for the 4c-8d hops).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from plot_neb import vasp_profile, CM, TXT, MUT, OR, PU

ROOT = "vasp/04_bulk_neb/q+1"
HOPS = [("S2", "4c–8d"), ("S4", "4c–8d"), ("S1", "8d–8d"), ("S5", "4c–8d"),
        ("S6", "8d–8d"), ("S3", "4c–8d"), ("L3", "4c–4c")]

fig, axs = plt.subplots(2, 4, figsize=(17 * CM, 8.2 * CM), sharey=True)
for ax, (hop, ends) in zip(axs.flat, HOPS):
    d = os.path.join(ROOT, hop)
    ax.set_title("%s  (%s)" % (hop, ends), fontsize=8.5, fontweight="semibold", loc="left", pad=3)
    if not os.path.exists(os.path.join(d, "neb_data.txt")):
        ax.text(0.5, 0.5, "data not\ncopied yet", transform=ax.transAxes, ha="center", va="center", color=MUT, fontsize=8)
        ax.set_xticks([])
        continue
    xs, e, xc, ec = vasp_profile(d)
    k = int(np.argmax(e))
    ax.plot(xc, ec, color=TXT, lw=0.9)
    ax.plot(xs, e, "o", ms=3.2, color=PU, zorder=3)
    ax.plot(xs[k], e[k], "o", ms=5.5, mfc="none", mec=OR, mew=1.1, zorder=4)
    ax.axhline(0, color=MUT, lw=0.5, ls=(0, (3, 2)))
    ax.text(0.04, 0.95, "%.3f eV" % e[k], transform=ax.transAxes, ha="left", va="top", color=TXT, fontsize=8.5)
    ax.set_xlim(xs[0] - 0.05 * xs[-1], xs[-1] * 1.05)
    print("%s %.3f eV" % (hop, e[k]))
last = axs.flat[-1]
last.axis("off")
last.plot([], [], "o", ms=3.2, color=PU, label="NEB images")
last.plot([], [], "o", ms=5.5, mfc="none", mec=OR, mew=1.1, label="highest image")
last.legend(frameon=False, loc="center", fontsize=8)
axs[0, 0].set_ylim(-0.05, 0.9)
for ax in axs[:, 0]:
    ax.set_ylabel("Energy (eV)")
for ax in axs[1, :3]:
    ax.set_xlabel("Reaction coordinate (Å)")
fig.tight_layout(pad=0.3, w_pad=0.6, h_pad=0.8)
fig.savefig("assets/neb_all_qp1_vasp.png", dpi=500, facecolor="white")
print("written assets/neb_all_qp1_vasp.png")
