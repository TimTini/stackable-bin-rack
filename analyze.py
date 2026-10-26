"""Mesh audit for binary STL using numpy only: bounds, topology, components, volume, sections."""
import sys, numpy as np

def load(path):
    raw = open(path, 'rb').read()
    n = int(np.frombuffer(raw, '<u4', 1, 80)[0])
    assert len(raw) == 84 + 50 * n, "not a clean binary STL"
    rec = np.frombuffer(raw, np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), n, 84)
    return rec['v'].astype(np.float64)

def audit(tri):
    pts, inv = np.unique(tri.reshape(-1, 3).round(5), axis=0, return_inverse=True)
    f = inv.reshape(-1, 3)
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    # directed edges: each should appear exactly once if winding consistent
    de = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    _, dcnt = np.unique(de, axis=0, return_counts=True)
    # components via union-find over vertices
    par = np.arange(len(pts))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in e:
        ra, rb = find(a), find(b)
        if ra != rb: par[ra] = rb
    roots = np.array([find(i) for i in range(len(pts))])
    comp = roots[f[:, 0]]
    v0, v1, v2 = tri[:, 0], tri[:, 1], tri[:, 2]
    vol = np.einsum('ij,ij->i', v0, np.cross(v1, v2)).sum() / 6
    area = np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1)
    print(f"tris={len(f)} verts={len(pts)} edges={len(cnt)}")
    print(f"bounds min={tri.reshape(-1,3).min(0)} max={tri.reshape(-1,3).max(0)}")
    print(f"size={np.ptp(tri.reshape(-1,3),0)}")
    print(f"edge use counts: {dict(zip(*np.unique(cnt, return_counts=True)))}")
    print(f"directed edge dup (winding errors)={int((dcnt>1).sum())}")
    print(f"degenerate tris={int((area<1e-9).sum())}")
    print(f"euler V-E+F={len(pts)-len(cnt)+len(f)}")
    print(f"signed volume={vol:.4f} area={area.sum()/2:.4f}")
    u, c = np.unique(comp, return_counts=True)
    print(f"components={len(u)}")
    for r in u[np.argsort(-c)][:20]:
        m = comp == r
        t = tri[m].reshape(-1, 3)
        cv = np.einsum('ij,ij->i', v0[m], np.cross(v1[m], v2[m])).sum() / 6
        print(f"  comp tris={m.sum()} min={t.min(0).round(3)} max={t.max(0).round(3)} vol={cv:.3f}")

def section(tri, axis, h):
    """Return segments of plane axis=h intersecting mesh (projected onto other two axes)."""
    o = [i for i in range(3) if i != axis]
    d = tri[:, :, axis] - h
    segs = []
    for t, dd in zip(tri, d):
        if (dd > 0).all() or (dd < 0).all(): continue
        p = []
        for i in range(3):
            j = (i + 1) % 3
            if (dd[i] > 0) != (dd[j] > 0):
                s = dd[i] / (dd[i] - dd[j]); p.append(t[i] + s * (t[j] - t[i]))
        if len(p) == 2: segs.append([p[0][o], p[1][o]])
    return np.array(segs)

if __name__ == '__main__':
    tri = load(sys.argv[1])
    audit(tri)
