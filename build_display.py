"""Build the high-detail DISPLAY model (traced from the reference photos).

Not for printing: see build.py / params.json for the printable, working shoe.
Outputs to out_display/: one STL per part, a combined GLB, and (when the
Blender `bpy` module is available) clay renders registered to the photos.

usage: python build_display.py [--res 0.4] [--params params_display.json]
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import trimesh

import build as B
from soletta.profiles import Profiles
from soletta.body import build_body
from soletta.outsole import build_outsole
from soletta.laces import build_laces
from soletta.tongue import tongue_display_scene
from soletta.dials import tessellate, place
from soletta.display import make_display_dial

GREYS = {  # clay tones per part, only to tell parts apart
    "body": "#a6aaae", "outsole": "#3b3e41", "tongue": "#979da2", "laces": "#202124",
    "dials": "#47494c", "webbing": "#6c7074", "buckles": "#2e3032",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="params_display.json")
    ap.add_argument("--res", type=float, default=None)
    ap.add_argument("--out", default="out_display")
    ap.add_argument("--no-step", action="store_true", help="skip the STEP export")
    a = ap.parse_args()
    p = json.load(open(a.params))
    res = p["resolution"]["display"]
    h = a.res or res["body"]
    os.makedirs(a.out, exist_ok=True)
    T0 = time.time()
    prof = Profiles(p)
    model = build_body(prof, B.log)
    tongue_sc = tongue_display_scene(model, prof)

    class _Drape:
        def points(self, P, upto=None):
            P = np.asarray(P, float).reshape(-1, 3)
            return np.minimum(model.scene.points(P, upto), tongue_sc.points(P))
    model.drape_scene = _Drape()
    lace_sc = None if p.get("lacing", {}).get("system") == "cable_guides" else build_laces(model, B.log)

    L = prof.L
    parts = {}
    parts["body"] = B.grid_mesh(model.scene, (-14, -88, 2), (L + 12, 88, 160), h, "body")
    parts["outsole"] = B.grid_mesh(build_outsole(prof), (-10, -78, -2), (L + 10, 78, 32),
                                   max(h * 0.75, 0.3), "outsole")
    parts["tongue"] = B.grid_mesh(tongue_sc, tongue_sc.domain[0], tongue_sc.domain[1], max(h * 0.75, 0.3), "tongue")
    cable = p.get("lacing", {}).get("system") == "cable_guides"
    if not cable:              # with cable lacing the line is fitted afterwards
        parts["laces"] = B.grid_mesh(lace_sc, lace_sc.domain[0], lace_sc.domain[1], max(h * 0.7, 0.3), "laces")
    if model.straps:
        from soletta.straps import build_strap_display, make_buckle
        ws = build_strap_display(model, prof)
        parts["webbing"] = B.grid_mesh(ws, ws.domain[0], ws.domain[1], max(h * 0.7, 0.3), "webbing", keep_all=True)
        bq = make_buckle(p["medial"])
        bms = []
        for st in model.straps:
            fr = st["buckle_frame"]
            V, F = tessellate(place(bq, fr.o, fr.ez, fr.ex), 0.02, 0.15)
            bms.append(trimesh.Trimesh(V, F, process=True))
        parts["buckles"] = trimesh.util.concatenate(bms)
    dd = make_display_dial(p["display_features"]["dial"])
    dms, exact = [], {}
    for d in model.dials:
        fr = d["frame"]
        o = fr.world(0, 0, d["seat"])
        shp = place(dd, o, fr.ez, fr.ex)
        exact[f"dial_{d['name']}"] = shp
        V, F = tessellate(shp, 0.02, 0.12)
        dms.append(trimesh.Trimesh(V, F, process=True))
    parts["dials"] = trimesh.util.concatenate(dms)
    if model.straps:
        for i, st in enumerate(model.straps):
            fr = st["buckle_frame"]
            exact[f"buckle_{i + 1}"] = place(bq, fr.o, fr.ez, fr.ex)

    scene = trimesh.Scene()
    for k, m in parts.items():
        m.export(os.path.join(a.out, f"{k}.stl"))
        c = GREYS[k].lstrip("#")
        rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
        mm = m.copy()
        mm.visual = trimesh.visual.ColorVisuals(mm, vertex_colors=np.tile(rgb + [255], (len(mm.vertices), 1)))
        scene.add_geometry(mm, node_name=k, geom_name=k)
        B.log(f"{k}: {len(m.faces)} triangles, watertight={m.is_watertight}")
    scene.export(os.path.join(a.out, "soletta_display.glb"))
    if not a.no_step:
        export_display_step(parts, exact, p, a.out)
    B.log(f"display model done in {time.time() - T0:.0f}s")


def export_display_step(parts, exact, p, out):
    """STEP: organic parts as faceted B-rep solids, dials and buckles exact."""
    import cadquery as cq
    from soletta import meshing as M
    sd = os.path.join(out, "step")
    os.makedirs(sd, exist_ok=True)
    targets = p.get("step_display", {"body": 90000, "outsole": 60000, "tongue": 12000,
                                     "laces": 24000, "webbing": 12000})
    tones = {"body": (0.66, 0.67, 0.69), "outsole": (0.20, 0.21, 0.22), "tongue": (0.58, 0.61, 0.63),
             "laces": (0.12, 0.12, 0.13), "webbing": (0.40, 0.42, 0.44)}
    assy = cq.Assembly(name="soletta_display")
    for name, tgt in targets.items():
        if name not in parts:
            continue
        mesh = parts[name]
        pieces = mesh.split(only_watertight=False) if name == "webbing" else [mesh]
        solids = []
        for k, piece in enumerate(pieces):
            dm = M.decimate(piece, max(2000, int(tgt / len(pieces))))
            if dm is None:
                B.WARN.append(f"display STEP: {name} could not be decimated; skipped")
                continue
            t = time.time()
            solids.append(cq.Shape.cast(M.mesh_to_occ_solid(dm)))
            B.log(f"display STEP: {name}[{k}] {len(dm.faces)} facets in {time.time() - t:.1f}s")
        if not solids:
            continue
        shape = solids[0] if len(solids) == 1 else cq.Compound.makeCompound(solids)
        shape.exportStep(os.path.join(sd, f"{name}.step"))
        assy.add(shape, name=name, color=cq.Color(*tones[name]))
    for name, shp in exact.items():
        col = (0.25, 0.26, 0.27) if name.startswith("dial") else (0.09, 0.09, 0.10)
        assy.add(shp, name=name, color=cq.Color(*col))
    path = os.path.join(sd, "soletta_display_assembly.step")
    if hasattr(assy, "export"):
        assy.export(path)
    else:
        assy.save(path)
    B.log("display STEP assembly written: " + path)


if __name__ == "__main__":
    main()
