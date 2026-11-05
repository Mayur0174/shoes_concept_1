"""Cable lacing (reference: dial-driven closure without laces).

Each of the three side dials drives one zone of the lacing opening:

    dial port A -> lateral guide (a) -> across the tongue -> medial U-guide
    (a -> b) -> across the tongue -> lateral guide (b) -> dial port B

Turning the dial shortens the loop and pulls the medial U-guide toward the
lateral guides, closing the opening over the tongue.  The guides are
moulded tubes on the shoe with a bore for the line; between guides the line
runs exposed over the upper and across the tongue.
"""
import numpy as np

from .sdf import CapsuleChain, ray_hit, normals, project, unit


def _top(sc, upto, xy):
    xy = np.atleast_2d(np.asarray(xy, float))
    O = np.c_[xy, np.full(len(xy), 220.0)]
    P, hit, _ = ray_hit(sc, O, np.tile([0.0, 0.0, -1.0], (len(O), 1)), 220.0, 0.2, upto)
    return P, normals(sc, P, upto), hit


def _on_skin(sc, upto, a, b, lift, step=2.5):
    """Points from a to b lying on the skin, lifted along the normal."""
    n = max(3, int(np.linalg.norm(b - a) / step))
    Q = a[None, :] + (b - a)[None, :] * np.linspace(0, 1, n)[:, None]
    for _ in range(2):
        Q = project(sc, Q, 0.0, upto, 5)
        N = normals(sc, Q, upto)
        Q = Q + N * lift
    return Q


def add_cable_lacing(m, sc, prof, log=print, ports=None):
    """Add the guides to the body scene and record the cable paths.

    ports: optional {dial index: [mouthA, mouthB, inner_ext_A, inner_ext_B]}
    from the printable dial pods; without it the cable leaves the dial ring."""
    p = prof.p
    lp = p["lacing"]
    up = p["upper"]
    sx = prof.sx
    upto = sc.mark()
    half = up["slot_width"] / 2 + lp["guide_offset"]
    r_t, r_b, lift = lp["guide_tube_r"], lp["bore_r"], lp["cable_lift"]
    m.bore_r = r_b
    m.cable_paths, m.bores, m.bore_paths, m.cables = [], [], [], []
    m.lacing_zones = []
    for zi, z in enumerate(lp["zones"]):
        d = m.dials[z["dial"]]
        xa, xb = z["x"][0] * sx, z["x"][1] * sx
        La, Na, _ = _top(sc, upto, [[xa, prof.cy(xa) + half]])
        Lb, Nb, _ = _top(sc, upto, [[xb, prof.cy(xb) + half]])
        La, Lb = La[0] + Na[0] * lift, Lb[0] + Nb[0] * lift
        # medial U-guide: bulges outward between the two medial points
        t = np.linspace(0.0, 1.0, 13)
        xs = xa + (xb - xa) * t
        ys = prof.cy(xs) - (half + lp["medial_arc_out"] * np.sin(np.pi * t))
        U, NU, ok = _top(sc, upto, np.c_[xs, ys])
        U = U + NU * lift
        Ma, Mb = U[0], U[-1]

        # where the line leaves the dial
        fr = d["frame"]
        if ports is not None:
            mA, mB, eA, eB = ports[z["dial"]]
            if np.linalg.norm(mA - La) > np.linalg.norm(mB - La):
                mA, mB, eA, eB = mB, mA, eB, eA
        else:
            r_exit = lp.get("display_exit_r", 16.5)
            out = []
            for target in (La, Lb):
                lx, ly, _ = fr.local(*target)
                th = np.arctan2(ly, lx)
                out.append(fr.world(np.cos(th) * r_exit, np.sin(th) * r_exit, d["seat"] + 4.0))
            mA, mB = out
            eA, eB = mA, mB
        # the line itself is fitted afterwards; keep only its key points
        run_a = np.array([mA, La])
        run_b = np.array([Lb, mB])
        cross_a = La[None, :] + (Ma - La)[None, :] * np.linspace(0, 1, 8)[1:-1, None]
        cross_b = Mb[None, :] + (Lb - Mb)[None, :] * np.linspace(0, 1, 8)[1:-1, None]
        path = np.vstack([eA, run_a, cross_a, U, cross_b, run_b, eB])
        m.cable_paths.append(path)

        # guide tubes: a bend at each lateral guide and the medial U
        def bend(P0, P_in, P_out):
            u_in, u_out = unit(P0 - P_in), unit(P_out - P0)
            return np.array([P0 - u_in * lp["lateral_guide_len"] * 0.6, P0,
                             P0 + u_out * lp["lateral_guide_len"] * 0.4])
        ga = bend(La, run_a[max(0, len(run_a) - 3)], Ma)
        gb = bend(Lb, Mb, run_b[min(2, len(run_b) - 1)])[::-1]
        gb = gb[::-1]
        for g in (ga, gb, U):
            sc.add("smooth_union", CapsuleChain(g, r_t, "guide"), 0.8)
            m.bore_paths.append(np.vstack([g[0] - unit(g[1] - g[0]) * 2.0, g, g[-1] + unit(g[-1] - g[-2]) * 2.0]))
        if ports is not None:
            for e, mo, nxt in ((eA, mA, run_a[min(2, len(run_a) - 1)]), (eB, mB, run_b[max(0, len(run_b) - 3)])):
                m.bore_paths.append(np.vstack([e, mo, mo + unit(nxt - mo) * 3.0]))
        m.lacing_zones.append(dict(dial=d["name"], La=La, Lb=Lb, Ma=Ma, Mb=Mb,
                                   length=float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())))
    m.hardware = []
    log("lacing: %d cable zones, guides on both edges of the opening" % len(lp["zones"]))
