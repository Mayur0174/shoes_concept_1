"""Meshing, validation, mesh booleans and exports (STL/3MF/GLB/STEP)."""
import numpy as np
import trimesh
from skimage import measure


def domain_axes(lo, hi, h):
    lo = np.floor(np.asarray(lo) / h) * h - 2 * h
    hi = np.ceil(np.asarray(hi) / h) * h + 2 * h
    return [np.arange(lo[i], hi[i] + h * 0.5, h) for i in range(3)]


def mesh_from_volume(V, axes, step=1):
    """Marching cubes on a padded SDF volume -> closed, outward-facing mesh."""
    V = V.copy()
    V[0, :, :] = V[-1, :, :] = 1.0
    V[:, 0, :] = V[:, -1, :] = 1.0
    V[:, :, 0] = V[:, :, -1] = 1.0
    h = axes[0][1] - axes[0][0]
    verts, faces, _, _ = measure.marching_cubes(V, level=0.0, spacing=(h, h, h),
                                                step_size=step, allow_degenerate=False)
    verts += np.array([axes[0][0], axes[1][0], axes[2][0]])
    m = trimesh.Trimesh(verts, faces, process=True)
    if m.volume < 0:
        m.invert()
    return m


def keep_largest(m):
    parts = m.split(only_watertight=False)
    if len(parts) <= 1:
        return m, 0
    parts = sorted(parts, key=lambda p: abs(p.volume), reverse=True)
    dropped = len(parts) - 1
    return parts[0], dropped


def validate(name, m, min_wall=None, wall_stats=None):
    r = dict(name=name,
             triangles=int(len(m.faces)),
             vertices=int(len(m.vertices)),
             watertight=bool(m.is_watertight),
             winding_consistent=bool(m.is_winding_consistent),
             volume_mm3=float(m.volume),
             area_mm2=float(m.area),
             bodies=int(len(m.split(only_watertight=False))),
             euler=int(m.euler_number),
             bounds_mm=[[round(float(v), 2) for v in b] for b in m.bounds])
    ext = m.bounds[1] - m.bounds[0]
    r["extents_mm"] = [round(float(v), 2) for v in ext]
    # FDM overhang check (printed upright, outsole on the bed)
    fn = m.face_normals
    cz = m.triangles_center[:, 2]
    a = m.area_faces
    above_bed = cz > m.bounds[0][2] + 0.6
    down = fn[:, 2] < -np.cos(np.radians(45))
    r["overhang_area_fraction_gt45"] = float(a[down & above_bed].sum() / a.sum())
    if wall_stats is not None:
        r["wall_thickness"] = wall_stats
    return r


def wall_thickness(scene, mesh, upto=None, n=4000, seed=1):
    """Sample surface points, march inward along -normal until the SDF
    turns positive again: local material thickness."""
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(mesh.vertices), size=min(n, len(mesh.vertices)), replace=False)
    P = mesh.vertices[idx]
    N = mesh.vertex_normals[idx]
    O = P - N * 0.05
    # march inside-out: invert scene sign by checking d > 0
    ts = np.arange(0.0, 40.0, 0.1)
    out = np.full(len(P), np.nan)
    for b0 in range(0, len(P), 500):
        Q = O[b0:b0 + 500, None, :] - N[b0:b0 + 500, None, :] * ts[None, :, None]
        d = scene.points(Q.reshape(-1, 3), upto).reshape(-1, len(ts))
        outside = d > 0
        first = np.argmax(outside, axis=1)
        ok = outside.any(axis=1) & (first > 0)
        out[b0:b0 + 500] = np.where(ok, ts[first] + 0.05, np.nan)
    v = out[np.isfinite(out)]
    if len(v) == 0:
        return {}
    return dict(samples=int(len(v)),
                p01=round(float(np.percentile(v, 1)), 2),
                p05=round(float(np.percentile(v, 5)), 2),
                median=round(float(np.median(v)), 2),
                frac_below_2_5mm=round(float((v < 2.5).mean()), 4),
                points_below_2_5mm=int((v < 2.5).sum()))


def _clean(d):
    d.merge_vertices()
    d.update_faces(d.nondegenerate_faces())
    d.update_faces(d.unique_faces())
    d.remove_unreferenced_vertices()
    if not d.is_winding_consistent:
        trimesh.repair.fix_winding(d)
    if not d.is_watertight:
        trimesh.repair.fill_holes(d)
    if d.is_watertight and d.volume < 0:
        d.invert()
    return d


def _ok(d):
    return d is not None and len(d.faces) > 0 and d.is_watertight and d.is_winding_consistent


def _fast_simplify(m, target_faces):
    import fast_simplification
    reduction = 1.0 - target_faces / len(m.faces)
    V, F = fast_simplification.simplify(np.asarray(m.vertices, np.float32),
                                        np.asarray(m.faces, np.int32), reduction)
    return _clean(trimesh.Trimesh(V, F, process=True))


def _manifold_simplify(m, target_faces):
    """Manifold-preserving simplification: raise tolerance until under target."""
    man = to_manifold(m)
    best = None
    tol = 0.02
    for _ in range(14):
        r = from_manifold(man.simplify(tol))
        if _ok(r):
            best = r
            if len(r.faces) <= target_faces * 1.15:
                return r
        tol *= 1.6
    return best


def decimate(m, target_faces):
    """Return a watertight decimated copy near target_faces, or None."""
    if len(m.faces) <= target_faces:
        return m
    # 1) quadric in a few gentle passes (big single-pass reductions tear thin lugs)
    try:
        d = m
        for _ in range(6):
            if len(d.faces) <= target_faces * 1.1:
                break
            step = max(target_faces, int(len(d.faces) * 0.35))
            nd = _fast_simplify(d, step)
            if not _ok(nd):
                break
            d = nd
        if _ok(d) and d is not m and len(d.faces) <= target_faces * 1.5:
            return d
    except Exception as e:  # noqa: BLE001
        print("quadric decimate failed:", e)
    # 2) manifold3d simplify (topology safe)
    try:
        d = _manifold_simplify(m, target_faces)
        if _ok(d):
            return d
    except Exception as e:  # noqa: BLE001
        print("manifold simplify failed:", e)
    return None


def to_manifold(m):
    import manifold3d as m3d
    mesh = m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                    tri_verts=np.asarray(m.faces, np.uint32))
    return m3d.Manifold(mesh)


def from_manifold(man, min_volume=1.0):
    # drop zero-volume slivers left by coplanar contacts
    parts = man.decompose()
    keep = [q for q in parts if abs(q.volume()) >= min_volume]
    if keep and len(keep) < len(parts):
        import manifold3d as m3d
        man = m3d.Manifold.compose(keep) if hasattr(m3d.Manifold, "compose") else sum(keep[1:], keep[0])
    mm = man.to_mesh()
    V = np.asarray(mm.vert_properties)[:, :3]
    F = np.asarray(mm.tri_verts)
    # process=False: manifold output is already indexed; merging nearby
    # vertices here would break its topology
    return trimesh.Trimesh(V, F, process=False)


def boolean(a, b, op):
    """Robust mesh boolean via manifold3d; returns None on failure."""
    try:
        ma, mb = to_manifold(a), to_manifold(b)
        if op == "union":
            r = ma + mb
        elif op == "difference":
            r = ma - mb
        else:
            r = ma ^ mb
        out = from_manifold(r)
        if len(out.faces) == 0:
            return None
        return out
    except Exception as e:  # noqa: BLE001
        print("boolean failed:", e)
        return None


# ----------------------------------------------------------------------------
# STEP (faceted B-rep for the organic bodies, exact B-rep for dials)
# ----------------------------------------------------------------------------

def mesh_to_occ_solid(m):
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Shell, TopoDS_Wire
    from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeVertex, BRepBuilderAPI_MakeEdge,
                                    BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeSolid)
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_IN
    from OCP.gp import gp_Pnt

    V = np.asarray(m.vertices, float)
    F = np.asarray(m.faces, np.int64)
    verts = [BRepBuilderAPI_MakeVertex(gp_Pnt(*v)).Vertex() for v in V]
    edges = {}

    def edge(i, j):
        key = (i, j) if i < j else (j, i)
        e = edges.get(key)
        if e is None:
            e = BRepBuilderAPI_MakeEdge(verts[key[0]], verts[key[1]]).Edge()
            edges[key] = e
        return e if i < j else e.Reversed()

    bld = BRep_Builder()
    shell = TopoDS_Shell()
    bld.MakeShell(shell)
    for a, b, c in F:
        w = TopoDS_Wire()
        bld.MakeWire(w)
        bld.Add(w, edge(a, b))
        bld.Add(w, edge(b, c))
        bld.Add(w, edge(c, a))
        mf = BRepBuilderAPI_MakeFace(w, True)
        if mf.IsDone():
            bld.Add(shell, mf.Face())
    shell.Closed(True)
    solid = BRepBuilderAPI_MakeSolid(shell).Solid()
    cls = BRepClass3d_SolidClassifier(solid)
    cls.PerformInfinitePoint(1e-6)
    if cls.State() == TopAbs_IN:
        solid.Reverse()
    return solid


def export_mesh(m, path, colors=None):
    if colors is not None:
        m = m.copy()
        m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=colors)
    m.export(path)
