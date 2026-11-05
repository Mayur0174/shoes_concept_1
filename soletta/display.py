"""High-detail display model features (not for printing).

Everything here is traced from the reference photographs (side view of the
dial side, top view, sole view and the labelled sheet) and stored in
params_display.json as (x from heel, z above ground) millimetres:

* dial cradles: midsole bosses with a lip running toward the strap guide
* flat webbing straps in the reference layout, a plastic keeper bar on the
  lace-panel edge, small strap guides at each dial
* a rolled, padded collar, a round heel badge, sweeping sidewall grooves
"""
import numpy as np

from .sdf import Feature, Frame, CapsuleChain, StrapChain, box, cylinder, capsule, ray_hit, normals, project, unit


def _ff(fr, fn, radius, name):
    return Feature(lambda X, Y, Z: fn(*fr.local(X, Y, Z)), fr.bbox(radius), name)


def _side_points(sc, upto, prof, xz, side):
    xz = np.atleast_2d(np.asarray(xz, float))
    O = np.c_[xz[:, 0], prof.cy(xz[:, 0]) + side * 150.0, xz[:, 1]]
    D = np.tile([0.0, -side, 0.0], (len(xz), 1))
    P, hit, _ = ray_hit(sc, O, D, 150.0, 0.2, upto)
    return P, normals(sc, P, upto), hit


def _densify(xz, step=3.0):
    xz = np.asarray(xz, float)
    out = [xz[0]]
    for a, b in zip(xz[:-1], xz[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for t in np.linspace(0, 1, n + 1)[1:]:
            out.append(a + (b - a) * t)
    return np.array(out)


def _strap_on_side(sc, upto, prof, xz, side, width, thick, lift=0.35):
    P, N, ok = _side_points(sc, upto, prof, _densify(xz), side)
    P, N = P[ok], N[ok]
    if len(P) < 2:
        return None, None
    if len(P) >= 4:                                     # light smoothing, then back onto the skin
        Q = P.copy()
        Q[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
        P = project(sc, Q, 0.0, upto, 4)
        N = normals(sc, P, upto)
    P = P + N * (thick / 2 + lift - 0.6)
    return P, N


def add_display_lateral(m, sc, prof, log=print):
    p = prof.p
    dp = p["display_features"]
    side = +1
    upto0 = sc.mark()

    # ---- dial cradles ------------------------------------------------------
    pod = dp["pod"]
    for d in m.dials:
        fr, t_pt = d["frame"], d["seat"]
        r, lip = pod["radius"], pod["lip"]

        def boss(lx, ly, lz, t_pt=t_pt, r=r, lip=lip):
            b = cylinder(lx, ly, lz, r, -10.0, t_pt, 2.5)
            tail = capsule(lx, ly, lz, np.array([0.0, 0.0, t_pt - 4.0]),
                           np.array([lip[0], lip[1], t_pt - 5.5]), lip[2])
            return np.minimum(b, tail)

        sc.add("smooth_union", _ff(fr, boss, r + 30, "pod"), pod["blend"])
    for d in m.dials:
        fr, t_pt = d["frame"], d["seat"]
        # flat seat for the dial and a small clearance above it
        sc.add("subtract", _ff(fr, lambda lx, ly, lz, t_pt=t_pt: cylinder(lx, ly, lz, pod["radius"] - 1.0,
                                                                       t_pt, t_pt + 30.0, 0.0),
                               pod["radius"] + 32, "seat"))
    # sculpted sidewall pockets (deep, rounded lens openings on both sides)
    from .body import tunnel_feature
    for spec in p["midsole"]["chambers"]:
        tf = tunnel_feature(prof, spec)
        depth = spec.get("depth", 0.0)
        if depth > 0:
            def pocket(X, Y, Z, tf=tf, depth=depth):
                slab = (prof.hw(X) - depth) - np.abs(Y - prof.cy(X))
                return np.maximum(tf.fn(X, Y, Z), slab)
            sc.add("smooth_subtract", Feature(pocket, tf.bbox, "pocket"), spec.get("fillet", p["midsole"]["chamber_fillet"]))
        else:
            sc.add("smooth_subtract", tf, p["midsole"]["chamber_fillet"])
    # sweeping sidewall grooves (both sides)
    for g in dp["grooves"]:
        for s_ in (+1, -1):
            P, N, ok = _side_points(sc, sc.mark(), prof, _densify(g["xz"], 2.0), s_)
            P = P[ok]
            if len(P) >= 2:
                # centre the groove outside the skin so it is only `depth` deep
                off = g["radius"] - g.get("depth", 2.0)
                sc.add("smooth_subtract", CapsuleChain(P + N[ok] * off, g["radius"], "groove"), 1.2)
    upto = sc.mark()

    # ---- webbing straps ------------------------------------------------------
    st = dp["straps"]
    m.display_straps = []
    for path in st["lateral"]:
        P, N = _strap_on_side(sc, upto, prof, path, side, st["width"], st["thickness"])
        if P is not None:
            sc.add("smooth_union", StrapChain(P, N, st["width"], st["thickness"], "cable", round_r=0.5), 0.4)
            m.display_straps.append(P)
    # straps traced in the top view (toe centre strap, toe V, over the instep)
    for path in st["top"] + ([st["over_top"]] if st.get("over_top") else []):
        xy = _densify(path, 2.0)
        O = np.c_[xy[:, 0], prof.cy(xy[:, 0]) + xy[:, 1], np.full(len(xy), 220.0)]
        P, hit, _ = ray_hit(sc, O, np.tile([0, 0, -1.0], (len(O), 1)), 220.0, 0.2, upto)
        P = P[hit]
        if len(P) > 3:
            N = normals(sc, P, upto)
            P = P + N * (st["thickness"] / 2 - 0.25)
            sc.add("smooth_union", StrapChain(P, N, st["width"], st["thickness"], "cable", round_r=0.5), 0.4)

    # ---- keeper bar on the lace-panel edge -----------------------------------
    k = dp.get("keeper")
    P, N, ok = _side_points(sc, upto, prof, [k["center"]], side) if k else (None, None, [False])
    if ok[0]:
        a, b = np.array(k["axis_from"], float), np.array(k["axis_to"], float)
        axis = np.array([b[0] - a[0], 0.0, b[1] - a[1]])
        kfr = Frame(P[0] + N[0] * (k["size"][2] / 2 + 1.0), N[0], ex_hint=axis)
        hx, hy, hz = k["size"][0] / 2, k["size"][1] / 2, k["size"][2] / 2

        def keeper(lx, ly, lz):
            body = box(lx, ly, lz, hx, hy, hz, 1.6)
            emb = box(lx, ly, lz - hz, hx * 0.62, 1.1, 0.5, 0.3)        # embossed logo strip
            return np.maximum(body, -emb)

        sc.add("smooth_union", _ff(kfr, keeper, hx + 8, "guide"), 0.5)

    # ---- strap guides at the dials --------------------------------------------
    gd = dp["dial_guides"]
    for d, ang in zip(m.dials, gd["angles_deg"]):
        fr, t_pt = d["frame"], d["seat"]
        a = np.radians(ang)
        c = np.array([np.cos(a), np.sin(a)]) * (pod["radius"] - 1.5)

        def guide(lx, ly, lz, c=c, a=a, t_pt=t_pt):
            ca, sa = np.cos(a), np.sin(a)
            u = (lx - c[0]) * ca + (ly - c[1]) * sa
            v = -(lx - c[0]) * sa + (ly - c[1]) * ca
            g = box(u, v, lz - (t_pt + 1.5), 3.2, 5.0, 2.6, 0.8)
            slot = box(u, v, lz - (t_pt + 1.5), 1.0, 3.8, 4.0, 0.2)
            return np.maximum(g, -slot)

        sc.add("smooth_union", _ff(fr, guide, pod["radius"] + 14, "guide"), 0.4)

    # ---- rolled collar ----------------------------------------------------------
    cl = dp["collar"]
    rr = cl["radius"]
    xs = np.arange(cl["x_range"][1], cl["x_range"][0], -cl["step"])
    rim = []
    for s_ in (+1, -1):
        pts = []
        for x in xs:
            z = float(prof.Zc(x)) - rr * 0.55
            P, N, ok = _side_points(sc, upto, prof, [[x, z]], s_)
            if ok[0]:
                pts.append(P[0] - np.array([0.0, s_ * rr * 0.45, 0.0]))
        rim.append(pts if s_ > 0 else pts[::-1])
    # close the loop around the heel: an arc between the two rim ends, each
    # point found by a ray aimed at the arc centre from outside the shoe
    back = []
    if rim[0] and rim[1]:
        A, Bm = np.array(rim[0][-1]), np.array(rim[1][0])
        c = 0.5 * (A + Bm)
        for th in np.linspace(0.15, np.pi - 0.15, 9):
            d = np.array([-np.sin(th), np.cos(th), 0.0])
            # z follows the collar line at the receded heel
            zq = float(prof.Zc(max(c[0] - 12 * np.sin(th), 2.0))) - rr * 0.55
            O = np.array([[c[0] + 90 * d[0], c[1] + 90 * d[1], zq]])
            Pb, hb, _ = ray_hit(sc, O, -d[None, :], 120.0, 0.2, upto)
            if hb[0]:
                back.append(Pb[0] - d * rr * 0.45)
    path = np.array(rim[0] + back + rim[1])
    if len(path) > 4:
        sm = path.copy()
        sm[1:-1] = (path[:-2] + 2 * path[1:-1] + path[2:]) / 4
        # padded collar: thick at the heel, tapering toward the tongue
        rx = np.interp(sm[:, 0], *np.array(cl["radius_by_x"]).T)
        for i in range(len(sm) - 1):
            r_seg = 0.5 * (rx[i] + rx[i + 1])
            a_, b_ = sm[i].copy(), sm[i + 1].copy()
            # keep the roll seated: drop each point by its extra radius
            a_[2] -= 0.5 * (rx[i] - rr); b_[2] -= 0.5 * (rx[i + 1] - rr)
            sc.add("smooth_union", CapsuleChain([a_, b_], r_seg, "collar_roll"), 2.5)
        m.collar_path = sm

    # ---- heel badge ---------------------------------------------------------------
    hb_ = dp["heel_badge"]
    O = np.array([[-60.0, float(prof.cy(0.0)), hb_["z"]]])
    Pb, hit, _ = ray_hit(sc, O, np.array([[1.0, 0.0, 0.0]]), 150.0, 0.2, sc.mark())
    if hit[0]:
        Nb = normals(sc, Pb, sc.mark())[0]
        bfr = Frame(Pb[0], Nb, ex_hint=(0, 0, 1))

        def badge(lx, ly, lz):
            disc = cylinder(lx, ly, lz, hb_["radius"], -2.0, hb_["thickness"], 1.2)
            ring = cylinder(lx, ly, lz, hb_["radius"] - 3.0, hb_["thickness"] - 0.6, hb_["thickness"] + 2, 0.3)
            return np.maximum(disc, -ring)

        sc.add("smooth_union", _ff(bfr, badge, hb_["radius"] + 6, "guide"), 0.8)

    m.bores, m.hardware = [], []
    log("display: cradles, %d straps, keeper, guides, rolled collar, heel badge" % len(m.display_straps))


def make_display_dial(dd):
    """Dial as seen in the reference: ring housing, knurled knob, domed metal
    cap with an index notch (exact B-rep, for display)."""
    import cadquery as cq
    R, r = dd["ring_r"], dd["knob_r"]
    ring = cq.Workplane("XY").circle(R).extrude(dd["ring_h"]).faces(">Z").edges().fillet(1.2)
    ring = ring.cut(cq.Workplane("XY").workplane(offset=dd["ring_h"] - 1.2).circle(r + 0.8).extrude(2))
    knob = cq.Workplane("XY").workplane(offset=dd["ring_h"] - 1.2).circle(r).extrude(dd["knob_h"])
    knob = knob.faces(">Z").edges().chamfer(0.9)
    flutes = (cq.Workplane("XY").workplane(offset=dd["ring_h"] - 0.2)
              .polarArray(r + 0.1, 0, 360, dd["knurls"]).circle(0.45).extrude(dd["knob_h"] - 1.6))
    knob = knob.cut(flutes)
    top = dd["ring_h"] - 1.2 + dd["knob_h"]
    knob = knob.cut(cq.Workplane("XY").workplane(offset=top - 0.8).circle(dd["cap_r"] + 0.4).extrude(1.0))
    cap = (cq.Workplane("XY").workplane(offset=top - 0.8).circle(dd["cap_r"]).extrude(1.3)
           .faces(">Z").edges().fillet(1.0))
    cap = cap.cut(cq.Workplane("XY").workplane(offset=top + 0.2).center(dd["cap_r"] * 0.35, 0)
                  .rect(dd["cap_r"] * 0.6, 0.7).extrude(1.0))
    return ring.union(knob).union(cap).val()
