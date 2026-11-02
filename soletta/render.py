"""Colouring (camo upper, material zones) and orthographic preview renders."""
import numpy as np


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.uint8)


CAMO = ["#6e1a2a", "#c8162b", "#e46a7c", "#ef6a1f", "#1e4a5a", "#8f1d24", "#4a1b2b", "#d13a2f"]
LABEL_COLORS = {
    1: "#3b3e42",   # midsole / wraps
    2: "#e6dfcb",   # lace panel
    3: "#2b5868",   # collar / lining
    4: "#2b5868",   # tongue
    5: "#34373b",   # pods / brackets
    6: "#a3a7ab",   # cable
    7: "#18191b",   # guides / anchors / pull tab
    8: "#2a2b2d",   # eyelets
}


def camo_colors(P, seed=11, n_cells=170):
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    lo, hi = P.min(0), P.max(0)
    seeds = rng.uniform(lo, hi, (n_cells, 3))
    warp = np.c_[np.sin(P[:, 1] * 0.09 + 1.3) + np.sin(P[:, 2] * 0.05),
                 np.sin(P[:, 2] * 0.08 + 0.4) + np.sin(P[:, 0] * 0.04),
                 np.sin(P[:, 0] * 0.07 + 2.1) + np.sin(P[:, 1] * 0.06)] * 7.0
    _, idx = cKDTree(seeds).query(P + warp)
    pal = np.array([hex2rgb(c) for c in CAMO])
    choice = rng.integers(0, len(pal), n_cells)
    return pal[choice[idx]]


def body_colors(P, labels):
    C = camo_colors(P)
    for lab, col in LABEL_COLORS.items():
        C[labels == lab] = hex2rgb(col)
    return C


def solid_colors(n, hexcol):
    return np.tile(hex2rgb(hexcol), (n, 1))


def dial_colors(V, frame, origin, dp):
    q = V - np.asarray(origin)
    lx, ly, lz = q @ frame.ex, q @ frame.ey, q @ frame.ez
    C = solid_colors(len(V), "#232425")
    cap = (np.hypot(lx, ly) < dp["cap_diameter"] / 2 + 0.05) & (lz > dp["thickness"] - 1.05)
    C[cap] = hex2rgb("#9a9da1")
    return C


# ----------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------

VIEWS = {
    # name: (camera direction from target, up vector, label)
    "left": ((0, 1, 0), (0, 0, 1), "Left Side (Dial Side A)"),
    "right": ((0, -1, 0), (0, 0, 1), "Right Side (Dial Side B)"),
    "top": ((0, 0, 1), (0, -1, 0), "Top View"),
    "bottom": ((0, 0, -1), (0, 1, 0), "Bottom View"),
    "front": ((1, 0, 0), (0, 0, 1), "Front View"),
    "rear": ((-1, 0, 0), (0, 0, 1), "Rear View"),
    "iso": ((0.75, 0.9, 0.55), (0, 0, 1), "Isometric"),
}


def render_all(parts, outdir, dial_info, log=print):
    """parts: list of (V, F, C uint8). Writes PNGs and returns paths."""
    import os
    try:
        import pyvista as pv
    except Exception as e:  # noqa: BLE001
        log(f"pyvista unavailable ({e}); falling back to matplotlib renders")
        return render_matplotlib(parts, outdir, log)
    pv.OFF_SCREEN = True
    os.makedirs(outdir, exist_ok=True)
    allV = np.vstack([p[0] for p in parts])
    lo, hi = allV.min(0), allV.max(0)
    center = (lo + hi) / 2
    ext = hi - lo
    pl = pv.Plotter(off_screen=True, window_size=(1800, 1100))
    pl.set_background("#f3f3f3")
    for V, F, C in parts:
        faces = np.hstack([np.full((len(F), 1), 3), F]).astype(np.int64).ravel()
        pd = pv.PolyData(np.asarray(V, float), faces)
        pd.point_data["rgb"] = np.asarray(C, np.uint8)
        pl.add_mesh(pd, scalars="rgb", rgb=True, smooth_shading=True,
                    specular=0.25, specular_power=18, ambient=0.18, diffuse=0.85)
    pl.enable_parallel_projection()
    out = {}
    aspect = 1800 / 1100
    for name, (d, up, label) in VIEWS.items():
        d = np.asarray(d, float)
        d /= np.linalg.norm(d)
        cam = pl.camera
        cam.focal_point = center
        cam.position = center + d * 1500
        cam.up = up
        # fit: project extents onto the screen axes
        upv = np.asarray(up, float)
        right = np.cross(-d, upv)
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) - center
        sx = np.abs(corners @ right).max()
        sy = np.abs(corners @ upv).max()
        cam.parallel_scale = max(sy, sx / aspect) * 1.08
        pl.reset_camera_clipping_range()
        path = os.path.join(outdir, f"view_{name}.png")
        pl.screenshot(path)
        out[name] = (path, label)
    # dial close-ups (one per side, front dial)
    for key, label in (("L1", "Dial Tension Mechanism (Side A)"), ("R1", "Dial Tension Mechanism (Side B)")):
        info = dial_info.get(key)
        if info is None:
            continue
        o, n = info
        cam = pl.camera
        cam.focal_point = o
        cam.position = o + n * 600 + np.array([0, 0, 120.0])
        cam.up = (0, 0, 1)
        cam.parallel_scale = 32
        pl.reset_camera_clipping_range()
        path = os.path.join(outdir, f"view_dial_{key}.png")
        pl.screenshot(path)
        out["dial_" + key] = (path, label)
    pl.close()
    log(f"rendered {len(out)} views with pyvista")
    return out


def render_matplotlib(parts, outdir, log=print):
    import os
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    os.makedirs(outdir, exist_ok=True)
    out = {}
    light = np.array([0.3, 0.5, 0.8])
    light /= np.linalg.norm(light)
    for name, (d, up, label) in VIEWS.items():
        fig = plt.figure(figsize=(12, 7), dpi=110)
        ax = fig.add_subplot(111, projection="3d")
        for V, F, C in parts:
            step = max(1, len(F) // 120000)
            Fs = F[::step]
            tri = V[Fs]
            nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
            shade = 0.35 + 0.65 * np.clip(nrm @ light, 0, 1)
            col = C[Fs[:, 0]] / 255.0 * shade[:, None]
            pc = Poly3DCollection(tri, facecolors=np.clip(col, 0, 1), linewidths=0)
            ax.add_collection3d(pc)
        allV = np.vstack([p[0] for p in parts])
        lo, hi = allV.min(0), allV.max(0)
        c = (lo + hi) / 2
        r = (hi - lo).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r)
        ax.set_ylim(c[1] - r, c[1] + r)
        ax.set_zlim(c[2] - r, c[2] + r)
        d = np.asarray(d, float)
        elev = np.degrees(np.arcsin(d[2] / np.linalg.norm(d)))
        azim = np.degrees(np.arctan2(d[1], d[0]))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        path = os.path.join(outdir, f"view_{name}.png")
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        out[name] = (path, label)
    log(f"rendered {len(out)} views with matplotlib")
    return out


def contact_sheet(views, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    layout = [["left", "right"], ["top", "bottom"], ["front", "rear", "dial_L1", "dial_R1"]]
    fig = plt.figure(figsize=(16, 13), dpi=110)
    fig.patch.set_facecolor("#f3f3f3")
    gs = fig.add_gridspec(3, 4, height_ratios=[1.0, 1.0, 0.9], hspace=0.12, wspace=0.04)
    for r, row in enumerate(layout):
        span = 4 // len(row)
        for c, key in enumerate(row):
            ax = fig.add_subplot(gs[r, c * span:(c + 1) * span])
            ax.set_axis_off()
            if key in views:
                img = mpimg.imread(views[key][0])
                ax.imshow(img)
                ax.set_title(views[key][1], fontsize=11, color="#333")
    fig.suptitle(title, fontsize=15, color="#222")
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
