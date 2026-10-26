"""One-line audit per binary STL: size, open/non-manifold edges, winding errors, components, Euler, volume.
Usage: python audit_dir.py file.stl [...]"""
import sys, numpy as np
from analyze import load

for path in sys.argv[1:]:
    tri = load(path)
    pts, inv = np.unique(tri.reshape(-1, 3).round(5), axis=0, return_inverse=True)
    f = inv.reshape(-1, 3)
    de = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    e = np.sort(de, axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    _, dcnt = np.unique(de, axis=0, return_counts=True)
    par = np.arange(len(pts))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in e:
        ra, rb = find(a), find(b)
        if ra != rb: par[ra] = rb
    comps = len({find(i) for i in range(len(pts))})
    v0, v1, v2 = tri[:, 0], tri[:, 1], tri[:, 2]
    vol = np.einsum('ij,ij->i', v0, np.cross(v1, v2)).sum() / 6
    area = np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1)
    lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
    print(f"{path.split(chr(92))[-1]:<16} size={np.round(hi - lo, 3)} min={np.round(lo, 3)} edges!=2:{int((cnt != 2).sum())}"
          f" wind:{int((dcnt > 1).sum())} degen:{int((area < 1e-9).sum())} comps:{comps}"
          f" euler:{len(pts) - len(cnt) + len(f)} vol:{vol:.0f}")
