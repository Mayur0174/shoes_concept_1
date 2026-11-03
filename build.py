"""Build the Soletta dual-dial trail shoe: meshes, STEP, renders, report.

Usage:  python build.py [--quality draft|full] [--params params.json]
Outputs go to ./out (large files) plus ./renders and ./reports (small,
committed back by CI).
"""
import argparse
import json
import os
import shutil
import sys
import time
import traceback
import zipfile

import numpy as np
import trimesh

from soletta.profiles import Profiles
from soletta.body import build_body, body_labels
from soletta.outsole import build_outsole
from soletta.laces import build_laces
from soletta import meshing as M
from soletta import render as RD

T0 = time.time()
WARN = []


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def optional(label):
    def deco(fn):
        def run(*a, **k):
            try:
                return fn(*a, **k)
            except Exception:  # noqa: BLE001
                tb = traceback.format_exc()
                log(f"WARNING: {label} failed\n{tb}")
                WARN.append(f"{label} failed: {tb.strip().splitlines()[-1]}")
                return None
        return run
    return deco


def grid_mesh(scene, lo, hi, h, name):
    axes = M.domain_axes(lo, hi, h)
    log(f"{name}: evaluating SDF on {len(axes[0])}x{len(axes[1])}x{len(axes[2])} grid @ {h} mm")
    V = scene.grid(*axes, log=log)
    log(f"{name}: marching cubes")
    mesh = M.mesh_from_volume(V, axes, 1)
    del V
    mesh, dropped = M.keep_largest(mesh)
    if dropped:
        WARN.append(f"{name}: removed {dropped} floating fragment(s)")
    log(f"{name}: {len(mesh.faces)} triangles, watertight={mesh.is_watertight}")
    return mesh


def printable_version(mesh, target, name):
    d = M.decimate(mesh, target)
    if d is None:
        WARN.append(f"{name}: decimation failed, printable copy uses full resolution")
        return mesh
    return d


@optional("insole logo deboss")
def deboss_logo(body, prof, depth=0.7):
    import cadquery as cq
    from soletta.dials import tessellate
    x = 92.0 * prof.sx
    z = float(prof.ztop(x))
    slope = float(prof.ztop(x + 5) - prof.ztop(x - 5)) / 10.0
    txt = (cq.Workplane("XY").text("SOLETTA", 9.0, 3.0, halign="center", valign="center",
                                   kind="bold").val())
    V, F = tessellate(txt, 0.02, 0.2)
    tm = trimesh.Trimesh(V, F, process=True)
    tm.apply_transform(trimesh.transformations.rotation_matrix(np.arctan(slope), [0, -1, 0]))
    tm.apply_translation([x, float(prof.cy(x)), z - depth])
    out = M.boolean(body, tm, "difference")
    if out is None:
        raise RuntimeError("manifold difference returned nothing")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default="params.json")
    ap.add_argument("--quality", default=None)
    args = ap.parse_args()
    with open(args.params) as f:
        params = json.load(f)
    quality = args.quality or os.environ.get("SOLETTA_QUALITY") or params.get("quality", "full")
    res = params["resolution"][quality]
    log(f"quality={quality} resolution={res}")

    out = "out"
    if os.path.isdir(out):
        shutil.rmtree(out)
    for d in ("components", "assembly", "printable", "step", "release"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    os.makedirs("renders", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    prof = Profiles(params)
    log("profiles + planform maps ready")
    model = build_body(prof, log)
    lace_sc = build_laces(model, log)
    outsole_sc = build_outsole(prof)

    from soletta.dials import build_dials, tessellate
    kit, dials = build_dials(model, log)

    # -------------------------------------------------------------- meshing
    L, W, H = prof.L, prof.W, prof.H
    dial_pts = np.array([d["origin"] for d in model.dials])
    y_lo = min(float((prof.cy(np.linspace(0, L, 200)) - prof.hw(np.linspace(0, L, 200))).min()),
               float(dial_pts[:, 1].min()) - 30) - 4
    y_hi = max(float((prof.cy(np.linspace(0, L, 200)) + prof.hw(np.linspace(0, L, 200))).max()),
               float(dial_pts[:, 1].max()) + 30) + 4
    z_lo = float(prof.zmid_bottom(np.linspace(0, L, 300)).min()) - 3
    body = grid_mesh(model.scene, (-8, y_lo, z_lo), (L + 8, y_hi, H + 3), res["body"], "body")

    z_hi_out = float(prof.zmid_bottom(np.linspace(0, L, 300)).max()) + 2
    outsole = grid_mesh(outsole_sc, (-6, y_lo + 10, -2.0), (L + 6, y_hi - 10, z_hi_out),
                        res["outsole"], "outsole")
    laces = grid_mesh(lace_sc, lace_sc.domain[0], lace_sc.domain[1], res["laces"], "laces")

    deb = deboss_logo(body, prof)
    if deb is not None and deb.is_watertight:
        body = deb
        log("insole logo debossed")

    def occ_mesh(shape):
        V, F = tessellate(shape, 0.02, 0.15)
        tm = trimesh.Trimesh(V, F, process=True)
        if tm.volume < 0:
            tm.invert()
        return tm

    dial_meshes = []          # (dial, kind, mesh) placed on the shoe
    for d in dials:
        for kind in ("housing", "spool", "knob"):
            dial_meshes.append((d, kind, occ_mesh(d[kind])))
    local = {k: occ_mesh(kit[k]) for k in ("housing", "spool", "knob")}

    # ----------------------------------------------------------- validation
    log("validating meshes")
    report = dict(quality=quality, resolution_mm=res, params=params, components=[], warnings=WARN)
    ws = M.wall_thickness(model.scene, body, None, n=params["validation"]["wall_samples"])
    report["components"].append(M.validate("body", body, wall_stats=ws))
    report["components"].append(M.validate("outsole", outsole))
    report["components"].append(M.validate("laces", laces))
    for k in ("housing", "spool", "knob"):
        report["components"].append(M.validate(f"dial {k} (each)", local[k]))
    report["mechanism"] = kit["checks"]

    # ------------------------------------------------------------- printable
    pv = params["printable"]
    body_p = printable_version(body, pv["body_faces"], "body")
    outsole_p = printable_version(outsole, pv["outsole_faces"], "outsole")
    laces_p = printable_version(laces, pv["lace_faces"], "laces")
    merged = M.boolean(body_p, outsole_p, "union")
    if merged is None or not merged.is_watertight:
        WARN.append("body+outsole union failed; printable shoe exported as two shells")
        merged = trimesh.util.concatenate([body_p, outsole_p])
    report["components"].append(M.validate("printable shoe (body+outsole)", merged))

    # ---------------------------------------------------------------- exports
    log("exporting STL")
    comp = os.path.join(out, "components")
    body.export(os.path.join(comp, "body_hires.stl"))
    outsole.export(os.path.join(comp, "outsole_hires.stl"))
    laces.export(os.path.join(comp, "lace_assembly_hires.stl"))
    body_p.export(os.path.join(comp, "body.stl"))
    outsole_p.export(os.path.join(comp, "outsole.stl"))
    laces_p.export(os.path.join(comp, "lace_assembly.stl"))
    for k in ("housing", "spool", "knob"):
        local[k].export(os.path.join(comp, f"dial_{k}.stl"))
    for d, kind, tm in dial_meshes:
        side = "left" if d["side"] > 0 else "right"
        tm.export(os.path.join(comp, f"dial_{kind}_{side}_{d['name']}_in_place.stl"))

    prn = os.path.join(out, "printable")
    merged.export(os.path.join(prn, "shoe_body_with_outsole.stl"))
    # mechanism print plates in their print orientation (no supports):
    # housing flange-down, spool pawls-down, knob face-down
    oriented = {}
    for k in ("housing", "spool", "knob"):
        t = local[k].copy()
        if k == "knob":
            t.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
        t.apply_translation([0, 0, -t.bounds[0][2]])
        oriented[k] = t
        t.export(os.path.join(prn, f"dial_{k}_single.stl"))
    pitch = 50.0
    plate = []
    for i in range(6):
        for j, k in enumerate(("housing", "spool", "knob")):
            t = oriented[k].copy()
            t.apply_translation([j * pitch, i * pitch, 0])
            plate.append(t)
    trimesh.util.concatenate(plate[:9]).export(os.path.join(prn, "dial_kit_x3_plate_A.stl"))
    trimesh.util.concatenate(plate[9:]).export(os.path.join(prn, "dial_kit_x3_plate_B.stl"))
    export_3mf(merged, os.path.join(prn, "shoe_body_with_outsole.3mf"))

    hi_parts = [body, outsole, laces] + [tm for _, _, tm in dial_meshes]
    trimesh.util.concatenate(hi_parts).export(os.path.join(out, "assembly", "soletta_assembly_hires.stl"))
    pr_parts = [body_p, outsole_p, laces_p] + [tm for _, _, tm in dial_meshes]
    trimesh.util.concatenate(pr_parts).export(os.path.join(out, "assembly", "soletta_assembly.stl"))

    # colours
    log("colouring")
    lab = body_labels(model, np.asarray(body_p.vertices))
    body_C = RD.body_colors(np.asarray(body_p.vertices), lab)
    outsole_C = RD.solid_colors(len(outsole_p.vertices), "#1d1e20")
    laces_C = RD.solid_colors(len(laces_p.vertices), "#ebe5d4")
    dial_parts = []
    for d, kind, tm in dial_meshes:
        C = RD.dial_colors(np.asarray(tm.vertices), d["frame"], d["origin"], kind)
        dial_parts.append((np.asarray(tm.vertices), np.asarray(tm.faces), C))
    color_parts = [(np.asarray(body_p.vertices), np.asarray(body_p.faces), body_C),
                   (np.asarray(outsole_p.vertices), np.asarray(outsole_p.faces), outsole_C),
                   (np.asarray(laces_p.vertices), np.asarray(laces_p.faces), laces_C)] + dial_parts
    export_glb(color_parts, os.path.join(out, "assembly", "soletta_assembly_color.glb"))

    # ---------------------------------------------------------------- renders
    dial_info = {d["name"]: (d["origin"], d["frame"].ez) for d in model.dials}
    views = render(color_parts, dial_info)
    if views:
        RD.contact_sheet(views, "renders/contact_sheet.png",
                         "Soletta dual-dial trail shoe  |  CAD reconstruction  |  %s quality" % quality)
        render_parts(outsole_p, outsole_C)
    mech_sheet(local["housing"], local["spool"], local["knob"])

    # ---------------------------------------------------------------- report
    def write_report():
        report["elapsed_s"] = round(time.time() - T0, 1)
        report["dial_frames"] = [dict(name=d["name"], origin=[round(float(v), 2) for v in d["origin"]],
                                      axis=[round(float(v), 3) for v in d["frame"].ez],
                                      seat_height=round(float(d["seat"]), 2)) for d in model.dials]
        with open("reports/report.json", "w") as f:
            json.dump(report, f, indent=2, default=float)
        write_markdown(report, "reports/report.md")

    write_report()  # early copy so renders + report survive a STEP crash
    export_step(model, body_p, outsole_p, laces_p, kit, dials, params, out)
    write_report()
    package(out)
    log("done")


@optional("3MF export")
def export_3mf(mesh, path):
    mesh.export(path)


@optional("GLB export")
def export_glb(parts, path):
    scene = trimesh.Scene()
    for i, (V, F, C) in enumerate(parts):
        tm = trimesh.Trimesh(V, F, process=False)
        tm.visual = trimesh.visual.ColorVisuals(tm, vertex_colors=np.c_[C, np.full(len(C), 255)])
        scene.add_geometry(tm, node_name=f"part_{i}")
    scene.export(path)


@optional("STEP export")
def export_step(model, body_p, outsole_p, laces_p, kit, dials, params, out):
    import cadquery as cq
    sp = params["step"]
    log("STEP: building faceted solids for organic bodies")
    solids = {}
    for name, mesh, target in (("body", body_p, sp["body_faces"]),
                               ("outsole", outsole_p, sp["outsole_faces"]),
                               ("lace_assembly", laces_p, sp["lace_faces"])):
        dm = M.decimate(mesh, target)
        if dm is None or len(dm.faces) > 3 * target:
            WARN.append(f"STEP: {name} could not be reduced to ~{target} facets; skipped")
            log(f"STEP: {name} skipped (decimation failed)")
            continue
        t = time.time()
        solids[name] = cq.Shape.cast(M.mesh_to_occ_solid(dm))
        log(f"STEP: {name} faceted solid from {len(dm.faces)} facets in {time.time() - t:.1f}s")
        solids[name].exportStep(os.path.join(out, "step", f"{name}.step"))
    kit["housing"].exportStep(os.path.join(out, "step", "dial_housing_exact_brep.step"))
    kit["spool"].exportStep(os.path.join(out, "step", "dial_spool_exact_brep.step"))
    kit["knob"].exportStep(os.path.join(out, "step", "dial_knob_exact_brep.step"))
    assy = cq.Assembly(name="soletta_shoe")
    for key, nm, col in (("body", "main_shoe_body", (0.45, 0.12, 0.16)),
                         ("outsole", "outsole", (0.11, 0.11, 0.12)),
                         ("lace_assembly", "lace_assembly", (0.92, 0.9, 0.83))):
        if key in solids:
            assy.add(solids[key], name=nm, color=cq.Color(*col))
    for d in dials:
        assy.add(d["housing"], name=f"dial_housing_{d['name']}", color=cq.Color(0.29, 0.30, 0.32))
        assy.add(d["spool"], name=f"dial_spool_{d['name']}", color=cq.Color(0.20, 0.20, 0.21))
        assy.add(d["knob"], name=f"dial_knob_{d['name']}", color=cq.Color(0.14, 0.14, 0.15))
    path = os.path.join(out, "step", "soletta_assembly.step")
    if hasattr(assy, "export"):
        assy.export(path)
    else:
        assy.save(path)
    log("STEP: assembly written")


@optional("mechanism sheet")
def mech_sheet(housing, spool, knob):
    return RD.mechanism_sheet(housing, spool, knob, "renders/dial_mechanism_sections.png")


@optional("rendering")
def render(parts, dial_info):
    return RD.render_all(parts, "renders", dial_info, log)


@optional("outsole render")
def render_parts(outsole_p, C):
    RD.render_all([(np.asarray(outsole_p.vertices), np.asarray(outsole_p.faces), C)],
                  "renders/outsole_only", {}, log)


def write_markdown(r, path):
    lines = [f"# Soletta CAD build report ({r['quality']} quality)", "",
             f"Elapsed: {r['elapsed_s']} s. Grid resolution (mm): {r['resolution_mm']}", "",
             "| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |",
             "|---|---|---|---|---|---|---|---|"]
    for c in r["components"]:
        lines.append("| {name} | {triangles:,} | {watertight} | {winding_consistent} | {bodies} | {v:.1f} | {e} | {o:.1%} |".format(
            v=c["volume_mm3"] / 1000, e=" x ".join(f"{x:.1f}" for x in c["extents_mm"]),
            o=c["overhang_area_fraction_gt45"], **c))
    wt = r["components"][0].get("wall_thickness")
    if wt:
        lines += ["", "## Body wall thickness (SDF ray sampling)", "",
                  "| samples | p01 | p05 | median | share < 2.5 mm |", "|---|---|---|---|---|",
                  f"| {wt['samples']} | {wt['p01']} | {wt['p05']} | {wt['median']} | {wt['frac_below_2_5mm']:.2%} |",
                  "", "Thin samples are expected on the cable channel sheaths (4 mm tube, 1.6 mm bore), the inner tongue, guide clips and eyelet rims, "
                  "which are features rather than walls."]
    mc = r.get("mechanism")
    if mc:
        lines += ["", "## Dial mechanism checks (exact B-rep)", "", "| check | value |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in mc.items()]
    lines += ["", "## Dial frames", "", "| Dial | Origin (mm) | Axis | Seat height |", "|---|---|---|---|"]
    for d in r["dial_frames"]:
        lines.append(f"| {d['name']} | {d['origin']} | {d['axis']} | {d['seat_height']} |")
    lines += ["", "## Warnings", ""] + ([f"- {w}" for w in r["warnings"]] or ["- none"])
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def package(out):
    rel = os.path.join(out, "release")

    def zipdir(name, folders, files=()):
        with zipfile.ZipFile(os.path.join(rel, name), "w", zipfile.ZIP_DEFLATED) as z:
            for folder in folders:
                for root, _, fs in os.walk(folder):
                    for fn in fs:
                        p = os.path.join(root, fn)
                        z.write(p, os.path.relpath(p, out))
            for p in files:
                if os.path.exists(p):
                    z.write(p, os.path.relpath(p, "."))

    zipdir("soletta_STEP.zip", [os.path.join(out, "step")])
    zipdir("soletta_STL_components.zip", [os.path.join(out, "components")])
    zipdir("soletta_printable.zip", [os.path.join(out, "printable")],
           ["README.md", "renders/dial_mechanism_sections.png"])
    zipdir("soletta_assembly.zip", [os.path.join(out, "assembly")])
    for p in ("renders/contact_sheet.png", "renders/dial_mechanism_sections.png", "reports/report.md"):
        if os.path.exists(p):
            shutil.copy(p, rel)
    log("release packages: " + ", ".join(sorted(os.listdir(rel))))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
