"""Main shoe body: midsole with through-chambers, upper, wraps, tongue,
collar, heel counter, dial pods and brackets, tension cables, guides,
anchors and eyelets, all as one SDF program."""
import numpy as np

from .sdf import (Scene, Feature, CapsuleChain, StrapChain, Frame, smin, smax, round_intersect,
                  box, cylinder, torus, rbox2d, ray_hit, normals, project, unit)


class BodyModel:
    pass


# ----------------------------------------------------------------------------
# Core analytic fields
# ----------------------------------------------------------------------------

def upper_field(prof, X, Y, Z, n_lo=3.5, n_hi=2.4):
    """Outer upper: superelliptic sections swept along x, normalised by the
    gradient so the value approximates Euclidean distance near the surface."""

    def rho_parts(Xs):
        Wu = np.maximum(prof.Wu(Xs), 1e-3)
        zb = prof.zb(Xs)
        zt = prof.Zt(Xs)
        zc = zb + 0.42 * (zt - zb)
        hlo = np.maximum(zc - zb, 1e-3)
        hhi = np.maximum(zt - zc, 1e-3)
        u = np.abs(Y - prof.cy(Xs)) / Wu
        dz = Z - zc
        upper_half = dz > 0
        h = np.where(upper_half, hhi, hlo)
        v = np.abs(dz) / h
        n = np.where(upper_half, n_hi, n_lo)
        un = u ** n
        vn = v ** n
        rho = np.maximum((un + vn) ** (1.0 / n), 1e-6)
        return rho, u, v, n, Wu, h

    rho, u, v, n, Wu, h = rho_parts(X)
    r1n = rho ** (1.0 - n)
    gy = u ** (n - 1.0) * r1n / Wu
    gz = v ** (n - 1.0) * r1n / h
    dx = 0.5
    rp = rho_parts(X + dx)[0]
    rm = rho_parts(X - dx)[0]
    gx = (rp - rm) / (2 * dx)
    g = np.sqrt(gx * gx + gy * gy + gz * gz)
    d = (rho - 1.0) / np.maximum(g, 1e-3)
    # The normalised superellipse degenerates where Wu -> 0 (toe/heel tips);
    # bound it by the exact planform distance so it can never leak outside.
    bound = np.maximum(prof.upper2d(X, Y), np.maximum(Z - prof.Zt(X), prof.zb(X) - Z))
    return np.maximum(d, bound)


def midsole_field(prof, X, Y, Z):
    d2 = prof.sole2d(X, Y)
    top = Z - prof.ztop(X)
    bot = prof.zmid_bottom(X) - Z
    a = round_intersect(d2, top, 6.0 * prof.sz)
    return round_intersect(a, bot, 1.0)


def panel_region(prof, X, Y):
    q = np.abs(Y - prof.cy(X)) - prof.phw(X)
    x0 = (prof.p["upper"]["throat_x"] - 12.0) * prof.sx
    return round_intersect(q, x0 - X, 3.0)


def quarter_region(prof, X, Z):
    sx = prof.sx
    zl = prof.zline(X) + 7.0 * prof.sz
    zh = prof.zquarter(X)
    a = np.maximum(zl - Z, Z - zh)
    b = np.maximum(58.0 * sx - X, X - prof.p["upper"]["throat_x"] * sx)
    return round_intersect(a, b, 4.0)


def core_parts(prof, X, Y, Z):
    fu = upper_field(prof, X, Y, Z)
    ms = midsole_field(prof, X, Y, Z)
    tw = prof.p["upper"]["wrap_thickness"]
    wrap = round_intersect(fu - tw, Z - prof.zline(X), 1.5)
    panel = round_intersect(fu - prof.p["upper"]["lace_panel_thickness"], panel_region(prof, X, Y), 1.0)
    quarter = round_intersect(fu - prof.p["upper"]["quarter_panel_thickness"], quarter_region(prof, X, Z), 1.0)
    return dict(upper=fu, midsole=ms, wrap=wrap, panel=panel, quarter=quarter)


def core_field(prof, X, Y, Z):
    c = core_parts(prof, X, Y, Z)
    d = smin(c["midsole"], c["wrap"], 6.0)
    d = smin(d, c["upper"], 1.0)
    d = np.minimum(d, c["panel"])
    d = np.minimum(d, c["quarter"])
    return d


def well_field(prof, X, Y, Z):
    """Foot opening: vertical-walled well above the footbed behind the throat."""
    x_throat = prof.p["upper"]["throat_x"] * prof.sx
    d2 = prof.upper2d(X, Y) + prof.twall(X)
    d2 = smax(d2, X - x_throat, 8.0)
    return smax(d2, prof.ztop(X) - Z, 2.0)


def foot_cavity_field(prof, X, Y, Z):
    """Hollow toe box / vamp: the upper offset inward by the wall thickness,
    above the footbed, joining the heel well behind the throat."""
    up = prof.p["upper"]
    fu = upper_field(prof, X, Y, Z)
    d = fu + up["inner_wall"]
    d = smax(d, prof.ztop(X) - Z, 2.0)
    return smax(d, (up["throat_x"] - 25.0) * prof.sx - X, 6.0)


def throat_slot_field(prof, X, Y, Z):
    """Lacing opening along the instep: the two eyelet rows can be pulled
    together over the tongue."""
    up = prof.p["upper"]
    x0, x1 = up["slot_x"][0] * prof.sx, up["slot_x"][1] * prof.sx
    a = np.abs(Y - prof.cy(X)) - up["slot_width"] / 2
    b = np.maximum(x0 - X, X - x1)
    c = prof.ztop(X) + 8.0 - Z
    return round_intersect(round_intersect(a, b, 1.5), c, 0.5)


def inner_tongue_field(prof, X, Y, Z):
    """Tongue under the slot, following the inside of the upper with a gap so
    the quarters slide over it; rooted to the vamp at the front of the slot."""
    up = prof.p["upper"]
    tg = up["tongue"]
    fu = upper_field(prof, X, Y, Z)
    depth = -fu
    d0 = up["inner_wall"] + tg["gap"]
    band = np.abs(depth - (d0 + tg["thickness"] / 2)) - tg["thickness"] / 2
    x0, x1 = tg["x"][0] * prof.sx, tg["x"][1] * prof.sx
    root0 = up["slot_x"][1] * prof.sx - 1.0
    root = np.maximum(fu, depth - (d0 + tg["thickness"]))
    root = np.maximum(root, np.maximum(root0 - X, X - (root0 + 8.0)))
    band = np.maximum(band, np.maximum(x0 - X, X - root0 - 0.5))
    w = np.abs(Y - prof.cy(X)) - tg["half_width"]
    zb = np.maximum(prof.ztop(X) + 10.0 - Z, Z - tg["z_max"] * prof.sz)
    return round_intersect(round_intersect(np.minimum(band, root), w, 3.0), zb, 2.0)


def collar_cut_field(prof, X, Y, Z):
    return prof.Zc(X) - Z + 0.0 * Y


# ----------------------------------------------------------------------------
# Local features
# ----------------------------------------------------------------------------

def tongue_feature(prof):
    sx, sz = prof.sx, prof.sz
    ang = np.radians(65.0)
    axis = np.array([-np.cos(ang), 0.0, np.sin(ang)])
    nrm = np.array([np.sin(ang), 0.0, np.cos(ang)])
    xt = (prof.p["upper"]["throat_x"] - 2.0) * sx
    c = np.array([xt, float(prof.cy(xt)), float(prof.Zc(xt)) - 14.0 * sz])
    fr = Frame(c, nrm, ex_hint=axis)
    half_len, half_w, half_t = 22.0 * sz, 22.0 * prof.sy, 3.6

    def fn(X, Y, Z):
        lx, ly, lz = fr.local(X, Y, Z)
        lz = lz + 0.010 * ly * ly          # edges curl back over the instep
        return box(lx, ly, lz, half_len, half_w, half_t, 2.5)

    return Feature(fn, fr.bbox(max(half_len, half_w) + 8), "tongue"), fr


def pull_tab_feature(prof):
    p = prof.p["heel"]
    tilt = np.radians(8.0)
    top = prof.H
    hz = p["pull_tab_height"] / 2
    c = np.array([-1.2 * prof.sx, float(prof.cy(0.0)), top - hz])
    up = np.array([-np.sin(tilt), 0.0, np.cos(tilt)])
    fr = Frame(c, np.array([np.cos(tilt), 0.0, np.sin(tilt)]), ex_hint=up)
    t = p["pull_tab_thickness"] / 2
    w = p["pull_tab_width"] / 2

    def fn(X, Y, Z):
        lx, ly, lz = fr.local(X, Y, Z)       # lx: up, ly: across, lz: through
        tab = box(lx, ly, lz, hz, w, t, 1.5)
        hole = box(lx - (hz - 6.5), ly, lz, 3.0, w - 5.0, t + 3, 1.0)
        return smax(tab, -hole, 0.8)

    return Feature(fn, fr.bbox(hz + w + 4), "pull_tab")


def tunnel_feature(prof, spec):
    """Through-chamber in the midsole: lofted superelliptic cross-section that
    pinches at the centre line and flares at both openings."""
    sx, sz = prof.sx, prof.sz
    xc, zc = spec["x"] * sx, spec["z"] * sz
    a, b = spec["half_length"] * sx, spec["half_height"] * sz
    tilt = np.radians(spec.get("tilt_deg", 0.0))
    ct, st = np.cos(tilt), np.sin(tilt)
    n = 2.6

    def fn(X, Y, Z):
        dx = X - xc
        dz = Z - zc
        lx = dx * ct + dz * st
        lz = -dx * st + dz * ct
        yy = np.abs(Y - prof.cy(X))
        s = 0.78 + 0.22 * np.clip((yy - 8.0) / 30.0, 0.0, 1.0) ** 2   # loft: pinch -> flare
        s = s + 0.18 * np.clip((yy - 30.0) / 18.0, 0.0, 1.0) ** 2
        u = np.abs(lx) / (a * s)
        v = np.abs(lz) / (b * s)
        rho = np.maximum((u ** n + v ** n) ** (1.0 / n), 1e-6)
        return (rho - 1.0) * np.minimum(a, b) * s

    big = 1.6
    lo = (xc - a * big - 2, -200.0, zc - b * big - 2)
    hi = (xc + a * big + 2, 200.0, zc + b * big + 2)
    return Feature(fn, (lo, hi), "tunnel")


def frame_feature(fr, fn_local, radius, name):
    def fn(X, Y, Z):
        return fn_local(*fr.local(X, Y, Z))
    return Feature(fn, fr.bbox(radius), name)


# ----------------------------------------------------------------------------
# Surface projection helpers
# ----------------------------------------------------------------------------

def project_side(scene, upto, prof, xz, side):
    """Hit the shoe from the side (+y side=+1, -y side=-1) at given (x, z)."""
    xz = np.atleast_2d(xz)
    cy = prof.cy(xz[:, 0])
    O = np.c_[xz[:, 0], cy + side * 150.0, xz[:, 1]]
    D = np.tile([0.0, -side, 0.0], (len(xz), 1))
    P, hit, _ = ray_hit(scene, O, D, 150.0, 0.25, upto)
    N = normals(scene, P, upto)
    return P, N, hit


def project_top(scene, upto, xy):
    xy = np.atleast_2d(xy)
    O = np.c_[xy, np.full(len(xy), 200.0)]
    D = np.tile([0.0, 0.0, -1.0], (len(xy), 1))
    P, hit, _ = ray_hit(scene, O, D, 200.0, 0.25, upto)
    N = normals(scene, P, upto)
    return P, N, hit


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

def build_body(prof, log=print):
    p = prof.p
    sx, sz = prof.sx, prof.sz
    m = BodyModel()
    sc = Scene("body")
    m.scene = sc
    m.prof = prof

    sc.add("base", Feature(lambda X, Y, Z: core_field(prof, X, Y, Z), None, "core"))
    for spec in p["midsole"]["chambers"]:
        sc.add("smooth_subtract", tunnel_feature(prof, spec), p["midsole"]["chamber_fillet"])
    sc.add("smooth_subtract", Feature(lambda X, Y, Z: well_field(prof, X, Y, Z), None, "well"), 2.0)
    sc.add("smooth_subtract", Feature(lambda X, Y, Z: collar_cut_field(prof, X, Y, Z), None, "collar_cut"), 2.5)
    sc.add("smooth_subtract", Feature(lambda X, Y, Z: foot_cavity_field(prof, X, Y, Z), None, "foot_cavity"), 2.0)
    sc.add("smooth_subtract", Feature(lambda X, Y, Z: throat_slot_field(prof, X, Y, Z), None, "throat_slot"), 1.0)
    # the tongue is a separate part (see tongue.py)
    m.tongue_pad, m.tongue_frame = tongue_feature(prof)
    sc.add("smooth_union", pull_tab_feature(prof), 1.5)
    m.mark_base = sc.mark()
    log("body: base program ready, placing dials")

    # ---- dials -------------------------------------------------------------
    dp = p["dials"]
    R = dp["diameter"] / 2
    m.dials = []
    straps_medial = p.get("medial", {}).get("system") == "straps"
    dial_sides = (+1,) if straps_medial else (+1, -1)
    for side in dial_sides:
        for i, (x, z) in enumerate(dp["positions_xz"]):
            x, z = x * sx, z * sz
            P, N, hit = project_side(sc, m.mark_base, prof, [[x, z]], side)
            if not hit[0]:
                raise RuntimeError(f"dial ray missed at x={x} z={z} side={side}")
            n = N[0].copy()
            # keep the dial face near-vertical: the hit can land on the
            # under-curve of the upper, whose normal points steeply down
            n[0] *= 0.3
            n[1] = side * max(abs(n[1]), 0.6)
            n[2] = float(np.clip(n[2] * 0.5, -0.08, 0.35))
            n /= np.linalg.norm(n)
            fr = Frame(P[0], n, ex_hint=(1.0, 0.0, 0.0))
            # seat height: highest body point under the dial footprint (+ margin)
            pts = [(0.0, 0.0)]
            for r in (6.0, 11.0, 15.0, 19.0, 23.0, 26.5):
                for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
                    pts.append((r * np.cos(a), r * np.sin(a)))
            pts = np.array(pts)
            O = np.array([fr.world(lx, ly, 40.0) for lx, ly in pts])
            D = np.tile(-fr.ez, (len(O), 1))
            _, h_ok, t = ray_hit(sc, O, D, 80.0, 0.25, m.mark_base)
            heights = 40.0 - t[h_ok]
            t_pt = max(dp["pod_height"], float(heights.max()) + 2.0) if h_ok.any() else dp["pod_height"]
            t_pt = min(t_pt, dp.get("max_seat_height", 9.0))
            name = ("L" if side > 0 else "R") + str(i + 1)
            m.dials.append(dict(name=name, side=side, index=i, frame=fr, seat=t_pt,
                                origin=fr.world(0, 0, t_pt + 16.0)))

    # ---- dial pods for the printed ratchet mechanism -------------------------
    # Each pod is a flat seat for the mechanism housing (2 x M2 pilot holes),
    # cleared above for the knob, with two posts carrying the cable channel
    # mouths in line with the housing's cable ports.
    from .mechanism import seat_info
    si = seat_info(dp)
    pod_r = si["ear_r"] + si["ear_lobe_r"] + 1.6
    clear_r = pod_r + 0.5
    mouth_r = clear_r + 1.2
    m.seat_info = si
    for d in m.dials:
        fr, t_pt = d["frame"], d["seat"]
        sc.add("smooth_union", frame_feature(
            fr, lambda lx, ly, lz, t_pt=t_pt: cylinder(lx, ly, lz, pod_r, -9.0, t_pt, 2.2),
            pod_r + 12, "pod"), 4.0)
    # the midsole through-chambers stay open below the pods (reference side view)
    for spec in p["midsole"]["chambers"]:
        sc.add("smooth_subtract", tunnel_feature(prof, spec), p["midsole"]["chamber_fillet"])
    for d in m.dials:
        fr, t_pt = d["frame"], d["seat"]
        # flat seat for the housing flange and ears, then a knob-sized clearance
        sc.add("subtract", frame_feature(
            fr, lambda lx, ly, lz, t_pt=t_pt: np.minimum(
                cylinder(lx, ly, lz, clear_r, t_pt, t_pt + 2.0, 0.0),
                cylinder(lx, ly, lz, si["wall_ro"] + 1.0, t_pt, t_pt + si["stack"] + 3.0, 0.0)),
            clear_r + 26, "seat"))

    m.mark_pods = sc.mark()
    targets = p["cables"]["targets_xz"]
    cp = p["cables"]
    r_sh, r_bore = cp["sheath_diameter"] / 2, cp["bore_diameter"] / 2
    lift = cp["bore_center_above_surface"]
    for d in m.dials:
        fr, t_pt = d["frame"], d["seat"]
        tx, tz = targets[d["index"]]
        tx, tz = tx * sx, tz * sz
        T, TN, hit = project_side(sc, m.mark_pods, prof, [[tx, tz]], d["side"])
        d["target"] = T[0]
        d["target_normal"] = TN[0]
        lx, ly, _ = fr.local(*T[0])
        theta_t = np.arctan2(ly, lx)
        d["theta"] = theta_t
        d["port_angles"] = [theta_t + np.radians(a) * si["port_angle"] / 24.0 for a in (-24.0, 24.0)]
        zp = t_pt + si["port_z"]
        d["mouths"] = [fr.world(np.cos(pa) * mouth_r, np.sin(pa) * mouth_r, zp) for pa in d["port_angles"]]

        def bracket(lx, ly, lz, t_pt=t_pt, pas=tuple(d["port_angles"]), zp=zp):
            out = None
            for pa in pas:
                a = np.array([np.cos(pa) * (mouth_r + 1.0), np.sin(pa) * (mouth_r + 1.0), t_pt - 4.0])
                b = np.array([np.cos(pa) * (mouth_r + 1.0), np.sin(pa) * (mouth_r + 1.0), zp])
                post = cylinder_seg(lx, ly, lz, a, b, r_sh + 1.2)
                out = post if out is None else np.minimum(out, post)
            return out

        sc.add("smooth_union", frame_feature(fr, bracket, clear_r + 16, "bracket"), 1.0)
        # housing screw pilot holes (ears opposite the ports)
        for ex_, ey_ in si["ears"]:
            ca, sa = np.cos(theta_t), np.sin(theta_t)
            hx, hy = ex_ * ca - ey_ * sa, ex_ * sa + ey_ * ca
            sc.add("subtract", frame_feature(
                fr, lambda lx, ly, lz, hx=hx, hy=hy, t_pt=t_pt: cylinder(
                    lx - hx, ly - hy, lz, si["screw_pilot_d"] / 2, t_pt - 7.0, t_pt + 1.0, 0.0),
                clear_r + 16, "pilot"))
    m.mark_brackets = sc.mark()
    log("body: dial pods and channel posts placed; routing cable channels")

    # ---- cable channels ------------------------------------------------------
    # Each dial pulls one loop of 1 mm braided line: housing port A -> channel
    # -> U-turn guide at the target -> channel -> housing port B.
    m.cables = []
    m.bores = []
    m.hardware = []
    upto = m.mark_brackets
    for d in m.dials:
        fr, t_pt, side = d["frame"], d["seat"], d["side"]
        T, TN = d["target"], unit(d["target_normal"])
        strands = []
        for P0 in d["mouths"]:
            dist = np.hypot(T[0] - P0[0], T[2] - P0[2])
            s_ = np.linspace(0.0, 1.0, max(6, int(dist / 2.0)))
            xz = np.c_[P0[0] + (T[0] - P0[0]) * s_, P0[2] + (T[2] - P0[2]) * s_]
            S, SN, ok = project_side(sc, upto, prof, xz, side)
            lx, ly, _ = fr.local(S[:, 0], S[:, 1], S[:, 2])
            keep = ok & (np.hypot(lx, ly) > mouth_r + 5.0)
            keep &= np.linalg.norm(S - T, axis=1) > 7.0
            S = S[keep]
            if len(S) >= 3:
                Sm = S.copy()
                Sm[1:-1] = (S[:-2] + 2 * S[1:-1] + S[2:]) / 4.0
                S = project(sc, Sm, offset=lift, upto=upto, iters=3)
            strands.append(np.vstack([P0, S]))
        # U-turn at the target, in the surface tangent plane
        approach = np.mean([T - st[-1] for st in strands], axis=0)
        u = unit(approach - np.dot(approach, TN) * TN)
        v = unit(np.cross(TN, u))
        C = T + TN * lift
        rho = cp["uturn_radius"]
        if np.dot(strands[0][-1] - C, v) > np.dot(strands[1][-1] - C, v):
            strands = strands[::-1]                   # strand 0 on the -v side
        phi = np.linspace(0.0, np.pi, 13)
        arc = C[None, :] + rho * (-np.cos(phi)[:, None] * v + np.sin(phi)[:, None] * u)
        loop = np.vstack([strands[0], arc, strands[1][::-1]])
        d["strands"] = [np.vstack([strands[0], arc[:7]]), np.vstack([strands[1], arc[::-1][:7]])]
        d["loop"] = loop
        ln = normals(sc, loop, upto)
        sc.add("smooth_union", StrapChain(loop, ln, cp["strap_width"], cp["strap_thickness"], "cable"), 0.6)
        m.cables.extend(d["strands"])
        m.bores.append(loop)
        # U-turn guide boss
        gfr = Frame(T, TN, ex_hint=u)
        sc.add("smooth_union", frame_feature(
            gfr, lambda lx, ly, lz, rho=rho: box(lx - rho * 0.3, ly, lz - lift * 0.5,
                                                 rho + 1.2, rho + 1.6, cp["strap_thickness"] / 2 + 0.8, 1.2),
            rho + 10, "anchor"), 1.0)
        m.hardware.append(("anchor", gfr))
    # cosmetic webbing V across the toe box (reference top view)
    for side in (+1, -1):
        xa, xb = 186.0 * sx, 256.0 * sx
        t_ = np.linspace(0.0, 1.0, 24)
        xs_ = xa + (xb - xa) * t_
        off = (prof.Wu(xs_) - 5.0) * (1 - t_) + 3.0 * t_
        xy = np.c_[xs_, prof.cy(xs_) + side * off]
        S, SN, ok = project_top(sc, upto, xy)
        S, SN = S[ok], SN[ok]
        if len(S) >= 4:
            S = S + SN * (cp["strap_thickness"] / 2 - 0.4)
            sc.add("smooth_union", StrapChain(S, SN, cp["strap_width"] * 0.85, cp["strap_thickness"] * 0.7,
                                              "cable"), 0.6)
    m.mark_cables = sc.mark()
    m.straps = []
    if straps_medial:
        from .straps import add_strap_hardware
        add_strap_hardware(m, sc, prof, sc.mark(), log)

    # mid-span guide sleeves (cosmetic clips over the channel)
    for d in m.dials:
        for pts in d["strands"]:
            if len(pts) < 9:
                continue
            i = int(len(pts) * 0.45)
            c = pts[i]
            tan = pts[i + 1] - pts[i - 1]
            nn = normals(sc, (c - unit(normals(sc, c[None, :], m.mark_brackets)[0]) * lift)[None, :],
                         m.mark_brackets)[0]
            gfr = Frame(c, nn, ex_hint=tan)
            sc.add("smooth_union", frame_feature(
                gfr, lambda lx, ly, lz: box(lx, ly, lz, 2.6, cp["strap_width"] / 2 + 1.2, cp["strap_thickness"] / 2 + 0.7, 0.7), 8, "guide"), 0.5)
            m.hardware.append(("guide", gfr))
    # bore paths (opened last, after the eyelets, so nothing can block them)
    m.bore_paths = []
    for d, loop in zip(m.dials, m.bores):
        fr = d["frame"]
        ext = [fr.world(np.cos(pa) * (mouth_r - 3.0), np.sin(pa) * (mouth_r - 3.0), d["seat"] + si["port_z"])
               for pa in d["port_angles"]]
        if np.linalg.norm(ext[0] - loop[0]) > np.linalg.norm(ext[1] - loop[0]):
            ext = ext[::-1]
        path = np.vstack([ext[0], loop, ext[1]])
        m.bore_paths.append(path)
    m.mark_guides = sc.mark()
    log("body: cable channels, U-turn guides and bores added; placing eyelets")

    # ---- eyelets -------------------------------------------------------------
    lp = p["laces"]
    xs_e = np.linspace(lp["eyelet_x_start"], lp["eyelet_x_end"], lp["eyelets_per_side"]) * sx
    off = prof.phw(xs_e) - lp["eyelet_edge_inset"]
    cy = prof.cy(xs_e)
    m.eyelets = {}
    for side, key in ((+1, "L"), (-1, "R")):
        xy = np.c_[xs_e, cy + side * off]
        P, N, ok = project_top(sc, m.mark_guides, xy)
        m.eyelets[key] = (P, N)
    for key in ("L", "R"):
        P, N = m.eyelets[key]
        for c, nn in zip(P, N):
            efr = Frame(c, nn)
            sc.add("smooth_union", frame_feature(
                efr, lambda lx, ly, lz: torus(lx, ly, lz - 0.4, lp["eyelet_ring_R"], lp["eyelet_ring_r"]),
                10, "eyelet"), 0.5)
    for key in ("L", "R"):
        P, N = m.eyelets[key]
        for c, nn in zip(P, N):
            efr = Frame(c, nn)
            sc.add("subtract", frame_feature(
                efr, lambda lx, ly, lz: cylinder(lx, ly, lz, lp["eyelet_hole_r"], -5.0, 4.0, 0.0),
                10, "eyelet_hole"))
    for path in m.bore_paths:
        sc.add("subtract", CapsuleChain(path, r_bore, "bore"))
    m.mark_final = sc.mark()
    log("body: program complete (%d ops)" % len(sc.ops))
    return m


def cylinder_seg(px, py, pz, a, b, r):
    """Flat-capped cylinder between points a and b (local coords)."""
    ab = b - a
    L = np.linalg.norm(ab)
    ax = ab / L
    qx, qy, qz = px - a[0], py - a[1], pz - a[2]
    t = qx * ax[0] + qy * ax[1] + qz * ax[2]
    rx, ry, rz = qx - t * ax[0], qy - t * ax[1], qz - t * ax[2]
    rad = np.sqrt(rx * rx + ry * ry + rz * rz)
    dx = rad - r
    dz = np.abs(t - L / 2) - L / 2
    return np.minimum(np.maximum(dx, dz), 0.0) + np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dz, 0) ** 2)


# ----------------------------------------------------------------------------
# Material labels for colouring renders / GLB
# ----------------------------------------------------------------------------

def body_labels(m, P):
    """Return an int label per vertex:
    0 camo upper, 1 midsole/wrap, 2 lace panel, 3 collar/lining, 4 tongue,
    5 pod/bracket, 6 cable, 7 guide/anchor (black), 8 eyelet."""
    prof = m.prof
    X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
    c = core_parts(prof, X, Y, Z)
    grey = smin(c["midsole"], c["wrap"], 6.0)
    lab = np.zeros(len(P), np.int32)
    eps = 0.35

    lab[c["panel"] < eps] = 2
    collar = (Z > prof.Zc(X) - 13.0) & (X < (prof.p["upper"]["throat_x"] - 4.0) * prof.sx)
    lab[collar] = 3
    well = well_field(prof, X, Y, Z)
    lab[np.abs(well) < 0.6] = 3
    lab[(grey < eps) & (lab != 3)] = 1

    groups = {"pod": 5, "bracket": 5, "cable": 6, "guide": 7, "anchor": 7, "eyelet": 8, "buckle": 7,
              "pull_tab": 7}

    for kind, f, k in m.scene.ops:
        g = groups.get(f.name)
        if g is None:
            continue
        lo, hi = f.bbox[0] - 2, f.bbox[1] + 2
        mask = np.all((P >= lo) & (P <= hi), axis=1)
        if not mask.any():
            continue
        idx = np.nonzero(mask)[0]
        d = f.points(P[idx], 1.0)
        lab[idx[d < 0.3]] = g
    return lab
