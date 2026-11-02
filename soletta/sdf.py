"""Signed-distance-field toolkit used to build the organic shoe bodies.

Every primitive works on broadcastable numpy arrays, so the same code serves
structured-grid evaluation (X:(nx,1,1), Y:(1,ny,1), Z:(1,1,nz)) and point
queries (X, Y, Z all shaped (N,)). Negative values are inside the solid.
"""
import numpy as np


# ----------------------------------------------------------------------------
# Boolean operators
# ----------------------------------------------------------------------------

def smin(a, b, k):
    """Polynomial smooth minimum (smooth union with blend radius ~k)."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def round_intersect(a, b, r):
    """Intersection whose convex edge is rounded with radius r (hg_sdf)."""
    ua = np.maximum(r + a, 0.0)
    ub = np.maximum(r + b, 0.0)
    return np.minimum(-r, np.maximum(a, b)) + np.sqrt(ua * ua + ub * ub)


COMBINE = {
    "union": lambda a, b, k: np.minimum(a, b),
    "smooth_union": smin,
    "subtract": lambda a, b, k: np.maximum(a, -b),
    "smooth_subtract": lambda a, b, k: smax(a, -b, k),
    "intersect": lambda a, b, k: np.maximum(a, b),
    "smooth_intersect": smax,
    "round_intersect": round_intersect,
}
WINDOWABLE = {"union", "smooth_union", "subtract", "smooth_subtract"}


# ----------------------------------------------------------------------------
# Primitives (local coordinates)
# ----------------------------------------------------------------------------

def length3(x, y, z):
    return np.sqrt(x * x + y * y + z * z)


def box(px, py, pz, hx, hy, hz, r=0.0):
    qx = np.abs(px) - hx + r
    qy = np.abs(py) - hy + r
    qz = np.abs(pz) - hz + r
    outside = length3(np.maximum(qx, 0), np.maximum(qy, 0), np.maximum(qz, 0))
    inside = np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0.0)
    return outside + inside - r


def cylinder(px, py, pz, r, z0, z1, rr=0.0):
    """Capped cylinder along local z from z0 to z1, edges rounded by rr."""
    rad = np.sqrt(px * px + py * py)
    zc = 0.5 * (z0 + z1)
    hz = 0.5 * (z1 - z0)
    dx = rad - r + rr
    dz = np.abs(pz - zc) - hz + rr
    return (np.minimum(np.maximum(dx, dz), 0.0)
            + np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dz, 0) ** 2) - rr)


def torus(px, py, pz, R, r):
    q = np.sqrt(px * px + py * py) - R
    return np.sqrt(q * q + pz * pz) - r


def capsule(px, py, pz, a, b, r):
    bax, bay, baz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    pax, pay, paz = px - a[0], py - a[1], pz - a[2]
    bb = bax * bax + bay * bay + baz * baz
    h = np.clip((pax * bax + pay * bay + paz * baz) / max(bb, 1e-12), 0.0, 1.0)
    return length3(pax - bax * h, pay - bay * h, paz - baz * h) - r


def ellipsoid(px, py, pz, rx, ry, rz):
    k0 = length3(px / rx, py / ry, pz / rz)
    k1 = length3(px / (rx * rx), py / (ry * ry), pz / (rz * rz))
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def capsule2d(px, py, ax, ay, bx, by, r):
    bax, bay = bx - ax, by - ay
    pax, pay = px - ax, py - ay
    bb = bax * bax + bay * bay
    h = np.clip((pax * bax + pay * bay) / max(bb, 1e-12), 0.0, 1.0)
    return np.sqrt((pax - bax * h) ** 2 + (pay - bay * h) ** 2) - r


def rbox2d(px, py, hx, hy, r=0.0):
    qx = np.abs(px) - hx + r
    qy = np.abs(py) - hy + r
    return (np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2)
            + np.minimum(np.maximum(qx, qy), 0.0) - r)


def vesica_x(px, py, half_len, half_wid):
    """Pointed lens (vesica) with tips on the x axis at +-half_len."""
    a, w = half_len, half_wid
    r = 0.5 * (a * a / w + w)
    d = 0.5 * (a * a / w - w)
    qx = np.abs(py)          # iq's formula is written for a vertical lens
    qy = np.abs(px)
    tip = (qy - a) * d > qx * a
    d_tip = np.sqrt(qx * qx + (qy - a) ** 2)
    d_arc = np.sqrt((qx + d) ** 2 + qy * qy) - r
    return np.where(tip, d_tip, d_arc)


# ----------------------------------------------------------------------------
# Local frames
# ----------------------------------------------------------------------------

def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


class Frame:
    """Orthonormal frame: ez is the main axis, ex is ex_hint projected."""

    def __init__(self, origin, ez, ex_hint=(1.0, 0.0, 0.0)):
        self.o = np.asarray(origin, float)
        self.ez = unit(ez)
        hint = np.asarray(ex_hint, float)
        ex = hint - np.dot(hint, self.ez) * self.ez
        if np.linalg.norm(ex) < 1e-6:
            hint = np.array([0.0, 0.0, 1.0]) if abs(self.ez[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
            ex = hint - np.dot(hint, self.ez) * self.ez
        self.ex = unit(ex)
        self.ey = np.cross(self.ez, self.ex)

    def local(self, X, Y, Z):
        dx, dy, dz = X - self.o[0], Y - self.o[1], Z - self.o[2]
        ex, ey, ez = self.ex, self.ey, self.ez
        return (dx * ex[0] + dy * ex[1] + dz * ex[2],
                dx * ey[0] + dy * ey[1] + dz * ey[2],
                dx * ez[0] + dy * ez[1] + dz * ez[2])

    def world(self, lx, ly, lz):
        return self.o + lx * self.ex + ly * self.ey + lz * self.ez

    def bbox(self, radius):
        return (self.o - radius, self.o + radius)


# ----------------------------------------------------------------------------
# Features and scenes
# ----------------------------------------------------------------------------

class Feature:
    """A distance function plus an optional axis-aligned bounding box.

    The bbox must contain the solid; the scene pads it by the blend radius,
    so evaluation outside the padded box can be skipped for unions/cuts.
    """

    def __init__(self, fn, bbox=None, name=""):
        self.fn = fn
        self.bbox = None if bbox is None else (np.asarray(bbox[0], float), np.asarray(bbox[1], float))
        self.name = name

    def grid(self, xs, ys, zs, pad):
        return self.fn(xs[:, None, None], ys[None, :, None], zs[None, None, :])

    def points(self, P, pad):
        return self.fn(P[:, 0], P[:, 1], P[:, 2])


class CapsuleChain(Feature):
    """Tube of radius r through a polyline; each segment is windowed."""

    def __init__(self, pts, r, name=""):
        pts = np.asarray(pts, float)
        self.A, self.B, self.r = pts[:-1], pts[1:], float(r)
        self.pts = pts
        super().__init__(None, (pts.min(0) - r, pts.max(0) + r), name)

    def grid(self, xs, ys, zs, pad):
        out = np.full((len(xs), len(ys), len(zs)), pad, np.float32)
        for a, b in zip(self.A, self.B):
            lo = np.minimum(a, b) - self.r - pad
            hi = np.maximum(a, b) + self.r + pad
            i0, i1 = _slices(xs, lo[0], hi[0])
            j0, j1 = _slices(ys, lo[1], hi[1])
            k0, k1 = _slices(zs, lo[2], hi[2])
            if i1 <= i0 or j1 <= j0 or k1 <= k0:
                continue
            d = capsule(xs[i0:i1, None, None], ys[None, j0:j1, None], zs[None, None, k0:k1], a, b, self.r)
            sub = out[i0:i1, j0:j1, k0:k1]
            np.minimum(sub, d, out=sub)
        return out

    def points(self, P, pad):
        out = np.full(len(P), pad, float)
        for a, b in zip(self.A, self.B):
            lo = np.minimum(a, b) - self.r - pad
            hi = np.maximum(a, b) + self.r + pad
            m = np.all((P >= lo) & (P <= hi), axis=1)
            if not m.any():
                continue
            idx = np.nonzero(m)[0]
            d = capsule(P[idx, 0], P[idx, 1], P[idx, 2], a, b, self.r)
            out[idx] = np.minimum(out[idx], d)
        return out


def _slices(axis, lo, hi):
    return int(np.searchsorted(axis, lo, "left")), int(np.searchsorted(axis, hi, "right"))


class Scene:
    """Ordered CSG program of features evaluated lazily."""

    def __init__(self, name=""):
        self.name = name
        self.ops = []

    def add(self, kind, feature, k=0.0):
        if self.ops and feature.bbox is not None and kind not in WINDOWABLE:
            raise ValueError(f"{kind} cannot be windowed ({feature.name})")
        self.ops.append((kind, feature, float(k)))
        return len(self.ops)

    def mark(self):
        return len(self.ops)

    # -- point queries --------------------------------------------------------
    def points(self, P, upto=None):
        P = np.asarray(P, float).reshape(-1, 3)
        res = None
        for kind, f, k in self.ops[:upto]:
            pad = k + 1.0
            if res is None:
                res = np.asarray(f.points(P, pad), float) * np.ones(len(P))
                continue
            if f.bbox is None:
                res = COMBINE[kind](res, f.points(P, pad), k)
                continue
            lo, hi = f.bbox[0] - pad, f.bbox[1] + pad
            m = np.all((P >= lo) & (P <= hi), axis=1)
            if not m.any():
                continue
            idx = np.nonzero(m)[0]
            res[idx] = COMBINE[kind](res[idx], f.points(P[idx], pad), k)
        return res

    # -- structured grid -------------------------------------------------------
    def grid(self, xs, ys, zs, chunk=12, log=None):
        nx, ny, nz = len(xs), len(ys), len(zs)
        V = np.empty((nx, ny, nz), np.float32)
        for c0 in range(0, nx, chunk):
            cx = xs[c0:c0 + chunk]
            shape = (len(cx), ny, nz)
            res = None
            for kind, f, k in self.ops:
                pad = k + 1.0
                if res is None:
                    res = np.array(np.broadcast_to(f.grid(cx, ys, zs, pad), shape), np.float32)
                    continue
                if f.bbox is None:
                    res = COMBINE[kind](res, f.grid(cx, ys, zs, pad), k).astype(np.float32, copy=False)
                    continue
                lo, hi = f.bbox[0] - pad, f.bbox[1] + pad
                i0, i1 = _slices(cx, lo[0], hi[0])
                j0, j1 = _slices(ys, lo[1], hi[1])
                k0, k1 = _slices(zs, lo[2], hi[2])
                if i1 <= i0 or j1 <= j0 or k1 <= k0:
                    continue
                sub = res[i0:i1, j0:j1, k0:k1]
                d = f.grid(cx[i0:i1], ys[j0:j1], zs[k0:k1], pad)
                res[i0:i1, j0:j1, k0:k1] = COMBINE[kind](sub, d, k)
            V[c0:c0 + chunk] = res
            if log and (c0 // chunk) % 10 == 0:
                log(f"  {self.name}: slab {c0}/{nx}")
        return V


# ----------------------------------------------------------------------------
# Queries on scenes
# ----------------------------------------------------------------------------

def gradient(scene, P, upto=None, h=0.05):
    P = np.asarray(P, float).reshape(-1, 3)
    offs = np.array([[h, 0, 0], [-h, 0, 0], [0, h, 0], [0, -h, 0], [0, 0, h], [0, 0, -h]])
    Q = (P[:, None, :] + offs[None, :, :]).reshape(-1, 3)
    d = scene.points(Q, upto).reshape(-1, 6)
    g = np.stack([d[:, 0] - d[:, 1], d[:, 2] - d[:, 3], d[:, 4] - d[:, 5]], axis=1) / (2 * h)
    return g


def normals(scene, P, upto=None):
    g = gradient(scene, P, upto)
    return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)


def ray_hit(scene, origins, dirs, tmax, step=0.25, upto=None):
    """First surface crossing along each ray (fixed stepping + bisection).

    Returns (points, hit_mask, t)."""
    O = np.asarray(origins, float).reshape(-1, 3)
    D = np.asarray(dirs, float).reshape(-1, 3)
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    ts = np.arange(0.0, tmax + step, step)
    n, s = len(O), len(ts)
    hit = np.zeros(n, bool)
    t_lo = np.zeros(n)
    t_hi = np.zeros(n)
    batch = max(1, 400000 // s)
    for b0 in range(0, n, batch):
        sl = slice(b0, b0 + batch)
        Pq = O[sl, None, :] + D[sl, None, :] * ts[None, :, None]
        d = scene.points(Pq.reshape(-1, 3), upto).reshape(-1, s)
        inside = d < 0
        first = np.argmax(inside, axis=1)
        ok = inside.any(axis=1) & (first > 0)
        hit[sl] = ok
        t_hi[sl] = ts[first]
        t_lo[sl] = ts[np.maximum(first - 1, 0)]
    for _ in range(30):
        tm = 0.5 * (t_lo + t_hi)
        d = scene.points(O + D * tm[:, None], upto)
        inside = d < 0
        t_hi = np.where(inside, tm, t_hi)
        t_lo = np.where(inside, t_lo, tm)
    t = 0.5 * (t_lo + t_hi)
    return O + D * t[:, None], hit, t


def project(scene, P, offset=0.0, upto=None, iters=4):
    """Newton-project points onto the iso-surface d == offset."""
    P = np.asarray(P, float).reshape(-1, 3).copy()
    for _ in range(iters):
        d = scene.points(P, upto)
        g = gradient(scene, P, upto)
        gg = np.maximum((g * g).sum(1), 1e-9)
        P -= ((d - offset) / gg)[:, None] * g
    return P
