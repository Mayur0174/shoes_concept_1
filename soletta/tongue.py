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
    strip = tg.get("center_strip")
    if strip:
        # webbing strip down the centre of the tongue (reference lacing)
        from .sdf import StrapChain, ray_hit, normals
        x0s = prof.p["upper"]["slot_x"][0] * prof.sx + 3
        x1s = prof.p["upper"]["slot_x"][1] * prof.sx - 4
        xs = np.linspace(x0s, x1s, 40)
        O = np.c_[xs, prof.cy(xs), np.full_like(xs, 220.0)]
        P, hit, _ = ray_hit(sc, O, np.tile([0, 0, -1.0], (len(O), 1)), 220.0, 0.2, sc.mark())
        P = P[hit]
        if len(P) > 4:
            N = normals(sc, P, sc.mark())
            P = P + N * (strip["thickness"] / 2 - 0.3)
            sc.add("smooth_union", StrapChain(P, N, strip["width"], strip["thickness"], "tongue_strip", round_r=0.5), 0.4)
            # keeper loops where the lacing line crosses (line passes through them)
            from .sdf import Frame, box
            k = tg.get("keeper", {"gap": 4.0, "wall": 1.6, "clear": 3.0, "top": 1.2})
            for xk in keeper_xs(m):
                i = int(np.argmin(np.abs(P[:, 0] - xk)))
                c = P[i] + N[i] * strip["thickness"] / 2
                kfr = Frame(c, N[i], ex_hint=(1.0, 0.0, 0.0))
                span, h = k["gap"] / 2 + k["wall"], k["clear"] + k["top"]

                def keeper(X, Y, Z, kfr=kfr, span=span, h=h):
                    lx, ly, lz = kfr.local(X, Y, Z)
                    outer = box(lx, ly, lz - h / 2, span, strip["width"] / 2 + 1.0, h / 2, 0.6)
                    tun = box(lx, ly, lz - k["clear"] / 2, k["gap"] / 2, strip["width"], k["clear"] / 2, 0.3)
                    return np.maximum(outer, -tun)

                sc.add("union", Feature(keeper, kfr.bbox(strip["width"] + 6), "keeper"))
    x0 = tg["x"][0] * prof.sx - 25
    x1 = prof.p["upper"]["slot_x"][1] * prof.sx + tg["glue_flap"] + 5
    cy = float(prof.cy(0.5 * (x0 + x1)))
    sc.domain = (np.array([x0, cy - tg["half_width"] - 30, float(prof.ztop(x1)) + 5]),
                 np.array([x1, cy + tg["half_width"] + 30, prof.H + 15]))
    return sc


def _arc(prof):
    """Unrolled tongue: x along the shoe -> s along the flat part.  s = 0 is
    the padded top (collar end), the glue flap is the far end."""
    up = prof.p["upper"]
    tg = up["tongue"]
    xs = np.linspace(tg["x"][0] * prof.sx, up["slot_x"][1] * prof.sx + tg["glue_flap"], 400)
    zs = np.array([float(prof.Zt(x)) for x in xs]) - up["inner_wall"] - tg["gap"]
    zs = np.minimum(zs, tg["z_max"] * prof.sz)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xs), np.diff(zs)))]) + 30.0    # + padded top
    return xs, s


def flat_length(prof):
    """Developed length of the fitted tongue along its centre line."""
    return float(_arc(prof)[1][-1])


def keeper_xs(m):
    """Where the lacing line crosses the tongue (one keeper loop each)."""
    out = []
    for z in getattr(m, "lacing_zones", []):
        out += [0.5 * (z["La"][0] + z["Ma"][0]), 0.5 * (z["Lb"][0] + z["Mb"][0])]
    return sorted(out)


def flat_tongue_mesh(prof, keepers_x=()):
    import manifold3d as m3d
    tg = prof.p["upper"]["tongue"]
    up = prof.p["upper"]
    L = flat_length(prof)
    xs, ss = _arc(prof)
    s_of = lambda x: float(np.interp(x, xs, ss))
    W = 2 * tg["half_width"]
    r = 6.0
    t0 = tg["thickness"]

    def rounded(l, w, rr):
        cs = [m3d.CrossSection.circle(rr, 48).translate((x, y))
              for x in (rr, l - rr) for y in (rr, w - rr)]
        return m3d.CrossSection.batch_hull(cs)

    band = m3d.Manifold.extrude(rounded(L, W, r), t0)
    # padded top at the collar end (s = 0); the glue flap is the other end
    pad = m3d.Manifold.extrude(rounded(30.0, W - 4, r).translate((1.0, 2.0)), tg["pad_thickness"])
    man = band + pad
    strip = tg.get("center_strip")
    if strip:
        sw, st = strip["width"], strip["thickness"]
        s0 = s_of(up["slot_x"][0] * prof.sx + 3)
        s1 = s_of(up["slot_x"][1] * prof.sx - 4)
        man = man + m3d.Manifold.extrude(rounded(s1 - s0, sw, 2.0).translate((s0, (W - sw) / 2)), t0 + st)
        k = tg.get("keeper", {"gap": 4.0, "wall": 1.6, "clear": 3.0, "top": 1.2})
        for x in keepers_x:
            sc_ = s_of(x)
            span = k["gap"] + 2 * k["wall"]
            h = t0 + st + k["clear"] + k["top"]
            outer = m3d.Manifold.cube((span, sw + 2.0, h)).translate((sc_ - span / 2, (W - sw) / 2 - 1.0, 0.0))
            tunnel = m3d.Manifold.cube((k["gap"], sw + 6.0, k["clear"])).translate(
                (sc_ - k["gap"] / 2, (W - sw) / 2 - 3.0, t0 + st))
            man = man + (outer - tunnel)
    mm = man.to_mesh()
    t = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)
    if t.volume < 0:
        t.invert()
    return t, L
