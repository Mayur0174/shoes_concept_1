"""Separate tongue.

Printing the tongue in place under the lacing throat does not work on FDM:
the nearly flat quarters 1 mm above it sag and fuse to it, and a tongue
joined to both quarters at the throat would stop them closing.  So the tongue
is its own part: printed flat in TPU, bent into place through the throat and
glued to the inside of the vamp in front of the slot (like a sewn-in tongue).

`tongue_display_scene` gives the tongue as fitted (renders, assembly, checks);
`flat_tongue_mesh` gives the printable flat part.
"""
import numpy as np
import trimesh

from .sdf import Scene, Feature, smax
from .body import upper_field, round_intersect, tongue_feature


def fitted_tongue_field(prof, X, Y, Z):
    """Band under the slot following the inside of the upper with a gap,
    closing to zero gap over the glue flap under the vamp."""
    up = prof.p["upper"]
    tg = up["tongue"]
    fu = upper_field(prof, X, Y, Z)
    depth = -fu
    root0 = up["slot_x"][1] * prof.sx
    flap = tg["glue_flap"]
    s = np.clip((X - root0) / 6.0, 0.0, 1.0)
    d0 = up["inner_wall"] + tg["gap"] * (1.0 - s * s * (3 - 2 * s))
    band = np.abs(depth - (d0 + tg["thickness"] / 2)) - tg["thickness"] / 2
    x0 = tg["x"][0] * prof.sx
    band = np.maximum(band, np.maximum(x0 - X, X - (root0 + flap)))
    w = np.abs(Y - prof.cy(X)) - tg["half_width"]
    zb = np.maximum(prof.ztop(X) + 10.0 - Z, Z - tg["z_max"] * prof.sz)
    return round_intersect(round_intersect(band, w, 3.0), zb, 2.0)


def tongue_display_scene(m, prof):
    body = m.scene
    gap = prof.p["upper"]["tongue"]["gap"]
    pad, _ = tongue_feature(prof)
    sc = Scene("tongue")
    sc.add("base", Feature(lambda X, Y, Z: fitted_tongue_field(prof, X, Y, Z), None, "tongue_band"))
    sc.add("smooth_union", pad, 3.0)

    # keep the padded top clear of the shoe body (it is a separate part)
    def clip(X, Y, Z):
        X, Y, Z = np.broadcast_arrays(X, Y, Z)
        P = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
        return (body.points(P) - gap * 0.6).reshape(X.shape)    # < 0 near/inside the body
    lo, hi = pad.bbox
    sc.add("subtract", Feature(clip, (lo - 4, hi + 4), "tongue_clip"))
    tg = prof.p["upper"]["tongue"]
    x0 = tg["x"][0] * prof.sx - 25
    x1 = prof.p["upper"]["slot_x"][1] * prof.sx + tg["glue_flap"] + 5
    cy = float(prof.cy(0.5 * (x0 + x1)))
    sc.domain = (np.array([x0, cy - tg["half_width"] - 30, float(prof.ztop(x1)) + 5]),
                 np.array([x1, cy + tg["half_width"] + 30, prof.H + 15]))
    return sc


def flat_length(prof):
    """Developed length of the fitted tongue along its centre line."""
    up = prof.p["upper"]
    tg = up["tongue"]
    xs = np.linspace(tg["x"][0] * prof.sx, up["slot_x"][1] * prof.sx + tg["glue_flap"], 200)
    zs = np.array([float(prof.Zt(x)) for x in xs]) - up["inner_wall"] - tg["gap"]
    zs = np.minimum(zs, tg["z_max"] * prof.sz)
    return float(np.hypot(np.diff(xs), np.diff(zs)).sum()) + 30.0      # + padded top


def flat_tongue_mesh(prof):
    import manifold3d as m3d
    tg = prof.p["upper"]["tongue"]
    L = flat_length(prof)
    W = 2 * tg["half_width"]
    r = 6.0

    def rounded(l, w, rr):
        cs = [m3d.CrossSection.circle(rr, 48).translate((x, y))
              for x in (rr, l - rr) for y in (rr, w - rr)]
        return m3d.CrossSection.batch_hull(cs)

    band = m3d.Manifold.extrude(rounded(L, W, r), tg["thickness"])
    pad = m3d.Manifold.extrude(rounded(30.0, W - 4, r).translate((L - 31.0, 2.0)), tg["pad_thickness"])
    man = band + pad
    mm = man.to_mesh()
    t = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)
    if t.volume < 0:
        t.invert()
    return t, L
