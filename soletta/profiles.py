"""Master profiles of the shoe: planform, rocker, stack, upper sections.

All control tables are written for the US M10 baseline (290 x 110 x 115 mm)
and are scaled per axis from params.json, so the whole model stays
parametric: change a master dimension and every curve follows.
"""
import numpy as np
from matplotlib.path import Path
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import map_coordinates

BASE_L, BASE_W, BASE_H = 290.0, 110.0, 115.0

# --- planform (top view) -----------------------------------------------------
# sole half-width before the elliptical heel/toe end rounding
HW_CTRL = [(0, 40), (30, 41.5), (60, 42.5), (100, 42), (130, 41.5), (160, 43.5),
           (190, 49), (215, 55), (240, 54), (265, 49), (290, 41)]
# centre line (toe swings medially, waist bows laterally)
CY_CTRL = [(0, 0), (60, 0.5), (130, 3.0), (200, 0.5), (250, -3), (290, -6)]
HEEL_ROUND, TOE_ROUND = 34.0, 48.0

# --- side view ---------------------------------------------------------------
HEEL_BEVEL_CTRL = [(-10, 7), (0, 5), (8, 2.2), (18, 0.6), (30, 0), (300, 0)]
TOE_SPRING_SHAPE = [(-10, 0), (190, 0), (215, 0.04), (240, 0.2), (265, 0.53), (290, 1.0), (300, 1.1)]
# stack blend: 1 -> heel height, 0 -> forefoot height
STACK_BLEND = [(-10, 0.94), (0, 0.94), (40, 1.0), (120, 0.56), (210, 0.0), (260, -0.19), (290, -0.31), (300, -0.31)]
# closed-top height of the upper sections (collar area is cut lower later)
# (reference sheet: the lace line falls from the throat to a low toe box)
UPPER_TOP_CTRL = [(-10, 128), (82, 128), (96, 116), (108, 111), (125, 108), (150, 103), (175, 96),
                  (200, 87), (225, 77), (245, 68), (262, 60), (275, 53), (284, 47), (290, 42), (300, 39)]
# collar top line; values far above the shoe mean "no cut"
COLLAR_CTRL = [(-10, 108), (0, 108), (15, 106), (40, 100), (62, 96), (82, 97), (96, 101),
               (104, 106), (112, 160), (126, 400), (300, 400)]
# top edge of the midsole side-wall wrap (toe cap / heel counter / pods)
WRAP_CTRL = [(-10, 74), (0, 74), (20, 72), (40, 62), (60, 52), (85, 47), (110, 45), (140, 46),
             (170, 43), (200, 40), (225, 39), (245, 43), (262, 51), (278, 57), (290, 58), (300, 58)]
# quarter-panel overlay band (upper edge)
QUARTER_TOP_CTRL = [(30, 74), (58, 74), (80, 76), (100, 80), (120, 82), (170, 82)]
# lace panel half width (top view)
# (reference: cream panel ~40 mm wide at the throat, ~26 mm near its rounded tip)
PANEL_CTRL = [(80, 20.5), (100, 20.5), (140, 20), (175, 18.5), (200, 16), (212, 13.5), (220, 8),
              (224, 0.1), (300, 0.1)]
# inner wall thickness of the foot opening (collar foam is thicker)
TWALL_CTRL = [(-10, 4.5), (100, 4.5), (140, 3.5), (300, 3.5)]


class Curve:
    """Monotone cubic profile, densely tabulated and evaluated by np.interp."""

    def __init__(self, pts, sx=1.0, sv=1.0, n=6001):
        pts = np.asarray(pts, float)
        xs, vs = pts[:, 0] * sx, pts[:, 1] * sv
        f = PchipInterpolator(xs, vs)
        self.xd = np.linspace(xs[0], xs[-1], n)
        self.vd = f(self.xd)

    def __call__(self, x):
        return np.interp(x, self.xd, self.vd)


class Map2D:
    """Exact signed distance to a closed polygon, tabulated on a fine grid."""

    def __init__(self, poly, x0, x1, y0, y1, h, with_phase=False):
        self.x0, self.y0, self.h = x0, y0, h
        xs = np.arange(x0, x1 + h, h)
        ys = np.arange(y0, y1 + h, h)
        PX, PY = np.meshgrid(xs, ys, indexing="ij")
        px, py = PX.ravel(), PY.ravel()
        A = poly
        B = np.roll(poly, -1, axis=0)
        D = B - A
        L2 = (D ** 2).sum(1)
        best = np.full(px.shape, np.inf)
        bi = np.zeros(px.shape, np.int64)
        bt = np.zeros(px.shape)
        for i in np.nonzero(L2 > 1e-12)[0]:
            ax, ay = A[i]
            dx, dy = D[i]
            t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2[i], 0.0, 1.0)
            ex = px - ax - t * dx
            ey = py - ay - t * dy
            d2 = ex * ex + ey * ey
            m = d2 < best
            best[m] = d2[m]
            bi[m] = i
            bt[m] = t[m]
        inside = Path(poly).contains_points(np.c_[px, py])
        d = np.sqrt(best)
        d[inside] *= -1.0
        self.d = d.reshape(PX.shape)
        if with_phase:
            seglen = np.sqrt(L2)
            cum = np.concatenate([[0.0], np.cumsum(seglen)[:-1]])
            s = cum[bi] + bt * seglen[bi]
            self.perimeter = float(seglen.sum())
            theta = 2 * np.pi * s / self.perimeter
            self.cos = np.cos(theta).reshape(PX.shape)
            self.sin = np.sin(theta).reshape(PX.shape)

    def _sample(self, arr, X, Y):
        Xb, Yb = np.broadcast_arrays(X, Y)
        ix = (Xb - self.x0) / self.h
        iy = (Yb - self.y0) / self.h
        out = map_coordinates(arr, [ix.ravel(), iy.ravel()], order=1, mode="nearest")
        return out.reshape(Xb.shape)

    def __call__(self, X, Y):
        return self._sample(self.d, X, Y)

    def theta(self, X, Y):
        return np.arctan2(self._sample(self.sin, X, Y), self._sample(self.cos, X, Y))


class Profiles:
    def __init__(self, p):
        self.p = p
        self.L = float(p["length"])
        self.W = float(p["max_width"])
        self.H = float(p["height"])
        self.sx = self.L / BASE_L
        self.sy = self.W / BASE_W
        self.sz = self.H / BASE_H
        sx, sy, sz = self.sx, self.sy, self.sz
        # control tables can be overridden per model (the display model traces
        # them from the reference photographs)
        T = dict(HW_CTRL=HW_CTRL, CY_CTRL=CY_CTRL, HEEL_BEVEL_CTRL=HEEL_BEVEL_CTRL,
                 TOE_SPRING_SHAPE=TOE_SPRING_SHAPE, STACK_BLEND=STACK_BLEND, UPPER_TOP_CTRL=UPPER_TOP_CTRL,
                 COLLAR_CTRL=COLLAR_CTRL, WRAP_CTRL=WRAP_CTRL, QUARTER_TOP_CTRL=QUARTER_TOP_CTRL,
                 PANEL_CTRL=PANEL_CTRL, TWALL_CTRL=TWALL_CTRL, HEEL_ROUND=HEEL_ROUND, TOE_ROUND=TOE_ROUND)
        T.update(p.get("tables", {}))
        self.T = T
        self.heel_round, self.toe_round = float(T["HEEL_ROUND"]), float(T["TOE_ROUND"])

        self._hw = Curve(T["HW_CTRL"], sx, sy)
        self.cy = Curve(T["CY_CTRL"], sx, sy)
        self._bevel = Curve(T["HEEL_BEVEL_CTRL"], sx, sz)
        self._spring = Curve(T["TOE_SPRING_SHAPE"], sx, 1.0)
        self._blend = Curve(T["STACK_BLEND"], sx, 1.0)
        self.Zt = Curve(T["UPPER_TOP_CTRL"], sx, sz)
        self.Zc = Curve(T["COLLAR_CTRL"], sx, sz)
        self.zline = Curve(T["WRAP_CTRL"], sx, sz)
        self.zquarter = Curve(T["QUARTER_TOP_CTRL"], sx, sz)
        self.phw = Curve(T["PANEL_CTRL"], sx, sy)
        self.twall = Curve(T["TWALL_CTRL"], sx, 1.0)
        hr = T.get("HEEL_RECEDE")
        self.heel_recede = Curve(hr, sz, sx) if hr else None

        self.heel_h = float(p["heel_height"])
        self.fore_h = float(p["forefoot_height"])
        self.toe_spring = float(p["toe_spring"])
        self.outsole_t = float(p["outsole"]["base_thickness"]) + float(p["outsole"]["perimeter_lug_height"])
        self.upper_inset = float(p["upper"]["inset_from_sole"]) * sy

        # 2D planform maps
        pad = 25.0
        self.x_lo, self.x_hi = -pad, self.L + pad
        hw_max = max(self.W / 2, max(v for _, v in T["HW_CTRL"]) * sy)
        self.y_lo = -hw_max - pad
        self.y_hi = hw_max + pad
        h2 = float(p["resolution"]["planform_map"])
        self.sole2d = Map2D(self.outline(0.0), self.x_lo, self.x_hi, self.y_lo, self.y_hi, h2, with_phase=True)
        ic = T.get("UPPER_INSET_CTRL")
        self.inset_curve = Curve(ic, sx, sy) if ic else None
        self.upper2d = Map2D(self.outline(self.upper_inset if ic is None else self.inset_curve),
                             self.x_lo, self.x_hi, self.y_lo, self.y_hi, h2)

    # -- 1D profiles -----------------------------------------------------------
    def end_factor(self, x):
        rh, rt = self.heel_round * self.sx, self.toe_round * self.sx
        a = np.clip(x / rh, 0.0, 1.0)
        b = np.clip((x - (self.L - rt)) / rt, 0.0, 1.0)
        return np.sqrt(np.clip(1 - (1 - a) ** 2, 0, 1)) * np.sqrt(np.clip(1 - b ** 2, 0, 1))

    def hw(self, x):
        return self._hw(x) * self.end_factor(x)

    def Wu(self, x):
        ins = self.upper_inset if self.inset_curve is None else self.inset_curve(x)
        return np.maximum(self.hw(x) - ins, 0.0)

    def zg(self, x):
        """Ground line (bottom of the perimeter lugs): heel bevel + toe spring."""
        return self._bevel(x) + self.toe_spring * self._spring(x)

    def stack(self, x):
        return self.fore_h + (self.heel_h - self.fore_h) * self._blend(x)

    def ztop(self, x):
        """Top of midsole = footbed."""
        return self.zg(x) + self.stack(x)

    def zmid_bottom(self, x):
        return self.zg(x) + self.outsole_t

    def zb(self, x):
        return self.ztop(x) - 8.0 * self.sz

    # -- planform polygons -------------------------------------------------------
    def outline(self, inset, n=320):
        t = np.linspace(0.0, 1.0, n)
        x = self.L * (1 - np.cos(np.pi * t)) / 2
        w = self.hw(x) - (inset(x) if callable(inset) else inset)
        keep = w > 1e-3
        x, w = x[keep], w[keep]
        c = self.cy(x)
        top = np.c_[x, c + w]
        bot = np.c_[x[::-1], (c - w)[::-1]]
        return np.vstack([top, bot])
