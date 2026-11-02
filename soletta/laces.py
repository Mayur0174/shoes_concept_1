"""Round laces: criss-cross lacing through the 6+6 eyelets with over/under
crossings, a toe-end bar, and a tied bow (knot, two loops, two tails with
aglets). Paths are draped over the finished body surface."""
import numpy as np

from .sdf import Scene, Feature, CapsuleChain, Frame, ellipsoid, normals
from .body import project_top


def build_laces(m, log=print):
    prof = m.prof
    lp = prof.p["laces"]
    sx = prof.sx
    r = lp["diameter"] / 2
    sc_body = m.scene
    upto = m.mark_final
    PL, NL = m.eyelets["L"]
    PR, NR = m.eyelets["R"]
    eyelets_xy = np.vstack([PL[:, :2], PR[:, :2]])
    ex_lo, ex_hi = PL[:, 0].min(), PL[:, 0].max()

    def lace_zone(xy):
        """1 over the lacing area (where laces stack), fading to 0 outside."""
        x, y = xy[:, 0], xy[:, 1]
        e = prof.phw(x) - lp["eyelet_edge_inset"]
        dy = np.abs(y - prof.cy(x)) - (e + 4.0)
        wy = np.clip(1.0 - dy / 6.0, 0.0, 1.0)
        wx = np.clip(1.0 - np.maximum(ex_lo - 6 - x, x - ex_hi - 6) / 6.0, 0.0, 1.0)
        return wy * wx

    def drape(xy, clearance, extra=None):
        S, N, ok = project_top(sc_body, upto, xy)
        de = np.min(np.linalg.norm(xy[:, None, :] - eyelets_xy[None, :, :], axis=2), axis=1)
        c = clearance + 2.0 * np.clip((8.0 - de) / 3.0, 0.0, 1.0)
        if extra is not None:
            c = c + extra
        return S + N * (r + c)[:, None]

    def eyelet_ends(P, N):
        dip = P - N * 2.0
        rise = P + N * (r + 2.4)
        return dip, rise

    chains = []

    def segment(a_idx, b_idx, a_side, b_side, bump):
        Pa, Na = (PL, NL) if a_side == "L" else (PR, NR)
        Pb, Nb = (PL, NL) if b_side == "L" else (PR, NR)
        A, An = Pa[a_idx], Na[a_idx]
        B, Bn = Pb[b_idx], Nb[b_idx]
        dist = np.linalg.norm(B[:2] - A[:2])
        s = np.linspace(0.0, 1.0, max(6, int(dist / 1.5)))[1:-1]
        xy = A[:2] + (B[:2] - A[:2]) * s[:, None]
        mid = drape(xy, lp["clearance"], bump * np.sin(np.pi * s) ** 2)
        da, ra = eyelet_ends(A, An)
        db, rb = eyelet_ends(B, Bn)
        pts = np.vstack([da, ra, mid, rb, db])
        chains.append(pts)

    n = len(PL)
    bump = lp["crossing_bump"]
    for i in range(n - 1):
        over = (i % 2 == 0)
        segment(i, i + 1, "L", "R", bump if over else 0.0)
        segment(i, i + 1, "R", "L", 0.0 if over else bump)
    segment(n - 1, n - 1, "L", "R", 0.0)          # toe-end bar

    # ---- bow ----------------------------------------------------------------
    stack = r * 2 + bump + 0.6
    xk = PL[0, 0] - 6.0 * sx
    K_surf, K_n, _ = project_top(sc_body, upto, np.array([[xk, float(prof.cy(xk))]]))
    K = K_surf[0] + K_n[0] * (r + lp["clearance"] + stack)
    for P, N in ((PL, NL), (PR, NR)):
        da, ra = eyelet_ends(P[0], N[0])
        dist = np.linalg.norm(K[:2] - ra[:2])
        s = np.linspace(0.0, 1.0, max(5, int(dist / 1.5)))[1:-1]
        xy = ra[:2] + (K[:2] - ra[:2]) * s[:, None]
        mid = drape(xy, lp["clearance"], stack * s)
        chains.append(np.vstack([da, ra, mid, K]))

    def bow_curve(xy_rel):
        xy = K[:2] + xy_rel
        z_zone = lace_zone(xy)
        return drape(xy, lp["clearance"], stack * z_zone)

    loop_len, loop_w = lp["bow_loop_length"], lp["bow_loop_width"]
    tails = []
    for side in (1.0, -1.0):
        t = np.linspace(0.0, 2 * np.pi, 44)[1:-1]
        yy = side * loop_len / 2 * (1 - np.cos(t))
        xx = -loop_w * np.sin(t) * side - 0.25 * np.abs(yy)
        pts = bow_curve(np.c_[xx, yy])
        chains.append(np.vstack([K, pts, K]))
        u = np.linspace(0.0, 1.0, 26)[1:]
        tx = 4.0 + lp["bow_tail_length"] * u
        ty = side * (3.0 + 14.0 * u ** 1.3)
        tpts = bow_curve(np.c_[tx, ty])
        chains.append(np.vstack([K, tpts]))
        tails.append(tpts)

    sc = Scene("laces")
    first = True
    for pts in chains:
        f = CapsuleChain(pts, r, "lace")
        sc.add("base" if first else "smooth_union", f, 0.3)
        first = False
    for tpts in tails:                                 # aglets
        seg = tpts[-7:]
        sc.add("smooth_union", CapsuleChain(seg, r + 0.45, "aglet"), 0.6)
    kfr = Frame(K, K_n[0], ex_hint=(1.0, 0.0, 0.0))
    knot = Feature(lambda X, Y, Z: ellipsoid(*kfr.local(X, Y, Z), 6.0, 7.0, 4.2), kfr.bbox(9), "knot")
    sc.add("smooth_union", knot, 1.0)
    sc.chains = chains
    allp = np.vstack(chains)
    sc.domain = (allp.min(0) - 6.0, allp.max(0) + 6.0)
    log("laces: %d lace chains" % len(chains))
    return sc
