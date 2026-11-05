"""Outsole: base plate, perimeter block lugs, heel/forefoot traction pods with
directional chevrons and cross-hatched floors, midfoot web with shank
diamond and open cells exposing the midsole."""
import numpy as np

from .sdf import Scene, Feature, smin, smax, round_intersect, vesica_x, capsule2d


def build_outsole(prof):
    p = prof.p["outsole"]
    sx, sy = prof.sx, prof.sy
    base_t = p["base_thickness"]
    per_h = p["perimeter_lug_height"]
    chev_h = p["chevron_lug_depth"]
    pad_h = p["center_pad_height"]
    band = p["perimeter_band_width"]
    pitch0 = p["perimeter_lug_pitch"]
    groove = p["perimeter_lug_gap"]
    n_lugs = max(8, int(round(prof.sole2d.perimeter / pitch0)))
    pitch = prof.sole2d.perimeter / n_lugs
    cham = p["lug_edge_round"]

    fore = dict(x=228 * sx, a=52 * sx, b=36 * sy)
    heel = dict(x=58 * sx, a=46 * sx, b=24 * sy)
    xm = 140 * sx
    fore_chev = [262, 242, 222, 202]
    heel_chev = [22, 42, 62, 82]

    def pod(X, dy, s):
        return vesica_x(X - s["x"], dy, s["a"], s["b"])

    def tri(u, period):
        f = u / period
        return np.abs(f - np.floor(f) - 0.5) * 2.0       # 0 at groove centre .. 1

    def field(X, Y, Z):
        zg = prof.zg(X)
        d2 = prof.sole2d(X, Y)
        dy = Y - prof.cy(X)
        q = -d2
        podF = np.maximum(pod(X, dy, fore), d2 + band + 2.0)
        podH = np.maximum(pod(X, dy, heel), d2 + band + 2.0)
        pods = np.minimum(podF, podH)

        # cross-hatched floor inside the pods (0.5 mm grooves)
        u1 = (X + dy) * 0.70710678
        u2 = (X - dy) * 0.70710678
        g1 = np.clip(1.0 - tri(u1, 1.8) / 0.35, 0.0, 1.0)
        g2 = np.clip(1.0 - tri(u2, 1.8) / 0.35, 0.0, 1.0)
        inpod = np.clip(-pods / 1.5, 0.0, 1.0)
        tex = p["texture_depth"] * np.maximum(g1, g2) * inpod

        # midfoot web: shank diamond + ribs, open cells in between
        da, db = 17.0 * sx, 11.0 * sy
        diamond = (np.abs(X - xm) * db + np.abs(dy) * da - da * db) / np.hypot(da, db)
        hwq = lambda x: prof.hw(x) - band
        ribs = np.minimum(
            capsule2d(X, dy, heel["x"] + heel["a"], 0.0, xm - da, 0.0, 2.5),
            capsule2d(X, dy, xm + da, 0.0, fore["x"] - fore["a"], 0.0, 2.5))
        for sgn in (1.0, -1.0):
            for xe in (118 * sx, 162 * sx):
                ribs = np.minimum(ribs, capsule2d(X, dy, xm, sgn * db, xe, sgn * float(hwq(xe)), 2.5))
        rims = np.abs(pods + 1.6) - 1.6
        web = np.minimum(np.minimum(ribs, diamond), rims)
        midzone = np.maximum(np.maximum(d2 + band + 1.5, np.abs(X - xm) - 38.0 * sx), 1.5 - pods)
        opening = smax(midzone, 2.2 - web, 1.5)

        # base plate (top flush with midsole bottom)
        # closed midfoot: the cells stay as recesses between the web ribs
        plate2d = d2 if p.get("closed_midfoot", False) else smax(d2, -opening, 1.0)
        z_top = zg + per_h + base_t
        plate_z = np.maximum(zg + per_h + tex - Z, Z - z_top)
        out = round_intersect(plate2d, plate_z, 1.0)

        below = np.maximum(zg + per_h - Z, 0.0)          # draft grows toward the ground
        # perimeter block lugs
        th = prof.sole2d.theta(X, Y)
        phase = th * n_lugs / (2 * np.pi)
        phc = phase - np.round(phase)
        dt = np.abs(phc) * pitch - (pitch - groove) / 2
        dn = np.abs(q - (band - 1.0) / 2) - (band + 1.0) / 2
        rr = 1.5
        lug2d = (np.sqrt(np.maximum(dt + rr, 0) ** 2 + np.maximum(dn + rr, 0) ** 2)
                 + np.minimum(np.maximum(dt, dn) + rr, 0.0) - rr)
        lugs = round_intersect(lug2d + 0.18 * below, np.maximum(zg - Z, Z - (zg + per_h + 0.4)), cham)
        out = smin(out, lugs, 0.8)

        # chevrons (forefoot point to the toe, heel point to the back)
        chev = None
        for xa_list, dirn, podc, span, back in ((fore_chev, 1.0, podF, 26.0, 16.0),
                                                 (heel_chev, -1.0, podH, 20.0, 13.0)):
            c = None
            for xa in xa_list:
                xa = xa * sx
                px = (X - xa) * dirn
                py = np.abs(dy)
                d = capsule2d(px, py, 0.0, 0.0, -back * sx, span * sy, p["chevron_width"] / 2)
                c = d if c is None else np.minimum(c, d)
            c = np.maximum(c, podc + 2.5)
            chev = c if chev is None else np.minimum(chev, c)
        chev3 = round_intersect(chev + 0.15 * below,
                                np.maximum(zg + per_h - chev_h - Z, Z - (zg + per_h + 0.4)), cham)
        out = smin(out, chev3, 0.8)

        # pod rims, shank diamond with raised micro-ridges, web ribs (3 mm pads)
        pad_lo = zg + per_h - pad_h
        rim3 = round_intersect(rims + 0.1 * below, np.maximum(pad_lo - Z, Z - (zg + per_h + 0.4)), cham)
        out = smin(out, rim3, 0.6)
        ridge = tri((X - xm) * 0.866 + dy * 0.5, 1.6)
        dia3 = round_intersect(diamond, np.maximum(pad_lo + 0.5 * ridge - Z, Z - (zg + per_h + 0.4)), cham)
        out = smin(out, dia3, 0.6)
        rib3 = round_intersect(ribs + 0.1 * below,
                               np.maximum(zg + per_h - 2.5 - Z, Z - (zg + per_h + 0.4)), cham)
        out = smin(out, rib3, 0.6)
        return out

    sc = Scene("outsole")
    sc.add("base", Feature(field, None, "outsole"))
    return sc
