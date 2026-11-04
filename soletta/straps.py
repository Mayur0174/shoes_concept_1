"""Medial-side strap system (reference sheet, "Strap System (Interior Side)").

Three webbing straps run from a loop at the lace-panel edge (the collar for
the rear strap) down to a two-slot ladder-lock buckle moulded on the top edge
of the midsole.  Thread the strap down through the outer slot, back up
through the inner slot, and pull the free end to tighten: friction on the
centre bar holds it.

Moulded into the body: the buckles and the top loops.
Separate parts: the straps themselves (15 mm nylon webbing, or the printable
TPU strips this module also generates).
"""
import numpy as np

from .sdf import Scene, Feature, Frame, StrapChain, box, smax, ray_hit, normals, project, unit


def _frame_feature(fr, fn_local, radius, name):
    def fn(X, Y, Z):
        return fn_local(*fr.local(X, Y, Z))
    return Feature(fn, fr.bbox(radius), name)


def _hit_side(sc, upto, prof, x, z, side):
    O = np.array([[x, float(prof.cy(x)) + side * 150.0, z]])
    D = np.array([[0.0, -side, 0.0]])
    P, hit, _ = ray_hit(sc, O, D, 150.0, 0.25, upto)
    return P[0], normals(sc, P, upto)[0], bool(hit[0])


def _hit_top(sc, upto, x, y):
    O = np.array([[x, y, 200.0]])
    D = np.array([[0.0, 0.0, -1.0]])
    P, hit, _ = ray_hit(sc, O, D, 200.0, 0.25, upto)
    return P[0], normals(sc, P, upto)[0], bool(hit[0])


def buckle_fn(sp, slots=2):
    """Ladder-lock frame standing off the surface (local w = surface normal,
    u = along the strap, v = across).  Webbing passes through the gap."""
    W = sp["webbing_width"]
    gap = sp["webbing_gap"]
    t = sp["frame_thickness"]
    post = sp["post_width"]
    hv = W / 2 + 1.5 + post                    # half width over the posts
    win_hv = W / 2 + 1.0
    bar = sp["bar_width"]
    win_u = sp["slot_width"]
    if slots == 2:
        hu = win_u + bar / 2 + 2.2             # outer rails 2.2 mm
        wins = [(+(bar / 2 + win_u / 2)), -(bar / 2 + win_u / 2)]
    else:
        hu = win_u / 2 + 2.6
        wins = [0.0]
    wc = gap + t / 2

    def fn(lu, lv, lw):
        plate = box(lu, lv, lw - wc, hu, hv, t / 2, 0.8)
        for c in wins:
            plate = smax(plate, -box(lu - c, lv, lw - wc, win_u / 2, win_hv, t, 0.4), 0.4)
        posts = np.minimum(box(lu, lv - (hv - post / 2), lw - (gap / 2 - 0.6), hu, post / 2, gap / 2 + 0.7, 0.5),
                           box(lu, lv + (hv - post / 2), lw - (gap / 2 - 0.6), hu, post / 2, gap / 2 + 0.7, 0.5))
        return np.minimum(plate, posts)

    return fn, max(hu, hv) + gap + t + 2


def buckle_dims(sp):
    W, post = sp["webbing_width"], sp["post_width"]
    hu = sp["slot_width"] + sp["bar_width"] / 2 + 2.2
    hv = W / 2 + 1.5 + post
    pins = [(su * (hu - 2.2), sv * (hv - post / 2)) for su in (-1, 1) for sv in (-1, 1)]
    return dict(hu=hu, hv=hv, pins=pins, pin_r=1.1, pin_len=4.0, hole_r=1.3, hole_depth=5.0)


def make_buckle(sp):
    """Separate PETG ladder-lock buckle (exact B-rep).  Local frame: x along
    the strap, y across, z = shoe surface normal; posts stand on the flat
    seat at z = 0 and four pins press (and glue) into the seat's holes."""
    import cadquery as cq
    bd = buckle_dims(sp)
    hu, hv = bd["hu"], bd["hv"]
    gap, t, post = sp["webbing_gap"], sp["frame_thickness"], sp["post_width"]
    W = sp["webbing_width"]
    plate = cq.Workplane("XY").workplane(offset=gap).rect(2 * hu, 2 * hv).extrude(t)
    plate = plate.edges("|Z").fillet(1.0)
    for c in (sp["bar_width"] / 2 + sp["slot_width"] / 2, -(sp["bar_width"] / 2 + sp["slot_width"] / 2)):
        plate = plate.cut(cq.Workplane("XY").workplane(offset=gap - 0.1).center(c, 0)
                          .rect(sp["slot_width"], W + 2.0).extrude(t + 0.2))
    b = plate
    for sv in (-1, 1):
        b = b.union(cq.Workplane("XY").center(0, sv * (hv - post / 2)).rect(2 * hu, post).extrude(gap + 0.01))
    for pu, pv in bd["pins"]:
        b = b.union(cq.Workplane("XY").workplane(offset=-bd["pin_len"]).center(pu, pv)
                    .circle(bd["pin_r"]).extrude(bd["pin_len"] + 0.01))
    return b.val()


def add_strap_hardware(m, sc, prof, upto, log=print):
    """Mould buckles and top loops on the medial side; record strap paths."""
    p = prof.p
    sp = p["medial"]
    side = sp["side"]
    sx, sz = prof.sx, prof.sz
    m.straps = []
    for i, x in enumerate(sp["strap_x"]):
        x = x * sx
        # bottom buckle on the midsole top edge, facing out
        zb = float(prof.zline(x)) + sp["buckle_z_offset"] * sz
        B, BN, ok_b = _hit_side(sc, upto, prof, x, zb, side)
        # top loop: lace-panel edge in front of the throat, collar behind it
        if x > p["upper"]["throat_x"] * sx:
            y = float(prof.cy(x)) + side * (float(prof.phw(x)) + sp["top_loop_outset"])
            T0, _, ok0 = _hit_top(sc, upto, x, y)
            # put the loop on the side wall just below the panel edge
            T, TN, ok_t = _hit_side(sc, upto, prof, x, float(T0[2]) - sp["panel_drop"] * sz, side)
            ok_t = ok_t and ok0
        else:
            T, TN, ok_t = _hit_side(sc, upto, prof, x, float(prof.Zc(x)) - sp["collar_drop"] * sz, side)
        if not (ok_b and ok_t):
            raise RuntimeError(f"strap {i}: projection missed")
        # strap path on the surface between them
        n = 24
        s = np.linspace(0.0, 1.0, n)
        Q = T[None, :] * (1 - s[:, None]) + B[None, :] * s[:, None]
        Q[:, 1] += side * 25.0 * np.sin(np.pi * s)            # bias outward, then project
        Q = project(sc, Q, offset=0.0, upto=upto, iters=6)
        QN = normals(sc, Q, upto)
        down = unit(B - T)
        bfr = Frame(B, BN, ex_hint=-down)                      # u points up the strap
        tfr = Frame(T, TN, ex_hint=down)
        tfn, trad = buckle_fn(sp, slots=1)
        sc.add("smooth_union", _frame_feature(tfr, tfn, trad, "buckle"), 0.6)
        # bottom: flat seat with 4 pin holes for the separate PETG buckle
        bd = buckle_dims(sp)
        hu, hv = bd["hu"], bd["hv"]
        pad = lambda lu, lv, lw, hu=hu, hv=hv: box(lu, lv, lw + 2.0, hu + 2.0, hv + 2.0, 2.0, 1.0)
        sc.add("smooth_union", _frame_feature(bfr, pad, hv + 12, "buckle_seat"), 1.0)
        # flatten at most 2 mm proud of the seat point (never digs into the wall)
        flat = lambda lu, lv, lw, hu=hu, hv=hv: box(lu, lv, lw - 1.0, hu + 1.2, hv + 1.2, 1.0, 0.4)
        sc.add("subtract", _frame_feature(bfr, flat, hv + 12, "buckle_seat_cut"))
        for pu, pv in bd["pins"]:
            hole = (lambda lu, lv, lw, pu=pu, pv=pv: np.maximum(
                np.hypot(lu - pu, lv - pv) - bd["hole_r"], np.maximum(-lw - bd["hole_depth"], lw - 1.0)))
            sc.add("subtract", _frame_feature(bfr, hole, hv + 12, "buckle_pin_hole"))
        # clear webbing passage behind the bars (the shoe surface is curved,
        # the frames are flat): carve a shallow channel under each frame
        for fr, slots in ((tfr, 1),):
            hu_l = (sp["slot_width"] + sp["bar_width"] / 2 + 2.2) if slots == 2 else (sp["slot_width"] / 2 + 2.6)
            # only 0.6 mm into the surface: the upper wall here is ~3.7 mm
            pas = (lambda lu, lv, lw, hu=hu_l: box(lu, lv, lw - (sp["webbing_gap"] - 0.6) / 2,
                                                 hu + 3.0, sp["webbing_width"] / 2 + 0.8,
                                                 (sp["webbing_gap"] + 0.6) / 2, 0.4))
            sc.add("subtract", _frame_feature(fr, pas, hu_l + 14, "strap_passage"))
        m.straps.append(dict(index=i, top=T, top_n=TN, bottom=B, bottom_n=BN, path=Q, path_n=QN,
                             buckle_frame=bfr, loop_frame=tfr,
                             length=float(np.linalg.norm(np.diff(Q, axis=0), axis=1).sum())))
    log("straps: %d buckles and top loops moulded on the medial side" % len(m.straps))


def build_strap_display(m, prof):
    """Webbing as fitted (for renders / assembly): lies on the surface from the
    top loop to the buckle, passing outside the loop/buckle bars."""
    sp = prof.p["medial"]
    sc = Scene("straps")
    first = True
    off = sp["webbing_gap"] + sp["frame_thickness"] + sp["webbing_thickness"] / 2 + 0.3
    for st in m.straps:
        Q, N = st["path"], st["path_n"]
        # lift the band clear of the surface, and over the bars at both ends
        s = np.linspace(0.0, 1.0, len(Q))
        lift = 0.6 + sp["webbing_thickness"] / 2 + (off - 0.6) * np.clip(1 - np.minimum(s, 1 - s) / 0.12, 0, 1)
        P = Q + N * lift[:, None]
        f = StrapChain(P, N, sp["webbing_width"], sp["webbing_thickness"], "webbing", round_r=0.5)
        sc.add("base" if first else "union", f)
        first = False
        # free end hanging from the buckle
        bfr = st["buckle_frame"]
        tail = np.array([bfr.world(-u, 0.0, off) for u in np.linspace(0.0, sp["tail_length"], 8)])
        tn = np.tile(bfr.ez, (len(tail), 1))
        sc.add("union", StrapChain(tail, tn, sp["webbing_width"], sp["webbing_thickness"], "webbing", round_r=0.5))
    allp = np.vstack([st["path"] for st in m.straps])
    sc.domain = (allp.min(0) - 25.0, allp.max(0) + 25.0)
    return sc


def strap_strip_lengths(m, prof):
    sp = prof.p["medial"]
    return [round(st["length"] + sp["fold_allowance"] + sp["tail_length"], 0) for st in m.straps]
