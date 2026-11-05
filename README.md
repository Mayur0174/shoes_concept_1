# Soletta 3-dial trail shoe: parametric CAD

A parametric CAD reconstruction of the Soletta technical trail shoe concept. It has a chunky organic midsole, a chevron-lug outsole with a closed midfoot, and a **laceless 3-dial cable closure**: three working, printable ratchet dials on the outer side. Each dial pulls a loop of line through moulded guides on both edges of the lacing opening, across a tongue with a centre webbing strip. The line itself is fitted after printing and is not part of the model.

All the code runs on GitHub Actions, so nothing needs to be installed locally. Every push builds the model, and each run:

* publishes a **GitHub Release** `build-N` with zipped STEP, STL, printable and assembly files
* commits preview renders to `renders/` and a validation report to `reports/`

## Display model (looks, not printing)

`build_display.py` builds a second, high-detail model that follows the reference photographs as closely as possible. It is for renders and the viewer, not for printing. The printable, working shoe is still `build.py` + `params.json`.

* `params_display.json` holds every curve traced from the photos: side silhouette and heel lean, instep line, collar line, midsole wave line, planform, sole openings, dial centres, strap paths, keeper bar, panel and collar shape. The values are millimetres measured from the side view (0.314 mm/px) and top view (0.325 mm/px).
* Display-only features live in `soletta/display.py` (the cable guides are shared with the printable model in `soletta/lacing.py`):
  * the grey sole as a bulging tub with a rounded lip
  * dial cradles
  * a padded collar that is thicker at the heel
  * the heel badge
  * a sculpted sidewall groove (no openings)
* Run `python build_display.py --res 0.4` to write `out_display/`: an STL per part, a GLB, and `step/soletta_display_assembly.step` plus one STEP per part. The STEP has faceted organic parts and exact dials.
* Clay renders registered to the photos (same frame and scale) are made with Blender's `bpy` module. The side silhouette matches the photo at IoU ≈ 0.91.

## Editing the model

Every dimension is in [`params.json`](params.json): master length, width and height, heel and forefoot stack, toe spring, dial size and placement, lacing zones and guide sizes (`lacing`), tongue and so on. Change a value, commit and push, and CI rebuilds everything. Set `"quality": "full"` for production resolution (0.35 mm body grid). `"draft"` gives a fast preview (0.8 mm).

You can also start a build by hand from the **Actions → build-cad → Run workflow** button and choose the quality there.

## How it is modelled

| Part | Technique | Files |
|---|---|---|
| Main body (midsole, upper, foot cavity, 20 mm lacing opening, collar, heel counter, dial pods, cable guides: bent guides on the outer edge, U-guides on the inner edge, each with a 2.2 mm bore) | Signed-distance CSG with smooth (G2-like) blends, meshed by marching cubes | `components/body*.stl`, `step/body.step` (faceted) |
| Outsole | Same SDF method: perimeter block lugs, pods with chevrons, cross-hatch floor, shank diamond and ribs over a closed midfoot | `components/outsole*.stl`, `step/outsole.step` |
| Tongue (separate part) | Follows the inside of the upper with a 1 mm gap; centre webbing strip; printed flat | `printable/tongue_tpu_flat.stl`, `components/tongue_as_fitted.stl` |
| Dial mechanism (x3) | Exact B-rep in CadQuery: housing (ratchet teeth, snap axle, cable ports), spool (compliant pawls, cable groove, knot pockets, hex key) and knob; 15 mm tall assembled | `components/dial_{housing,spool,knob}.stl`, `step/dial_*_exact_brep.step` |

All the shapes are real geometry, not textures. The SDF approach guarantees the organic parts are watertight and manifold, with filleted transitions.

`step/soletta_assembly.step` is a named, coloured assembly that imports into Fusion 360. The dial parts are exact B-rep solids there. The organic bodies are faceted B-rep solids, which you can edit as solids in Fusion or convert with *Mesh → Convert*. To change their shape parametrically, edit `params.json` instead.

## 3D printing

`printable/` contains:

* `shoe_body_with_outsole.stl` / `.3mf`: one watertight piece; print it upright on the outsole
* `dial_kit_x3_plate.stl`: 3 housings, 3 spools and 3 knobs, already in print orientation
* `tongue_tpu_flat.stl`: the tongue, printed flat in TPU and bent into place
* `dial_housing_single.stl`, `dial_spool_single.stl`, `dial_knob_single.stl`: one of each, for a test print

### Fit

At the default master size (290 mm long) the inside is 270 mm long, 99–101 mm wide at the ball, 66 mm at the heel, 60 mm high over the instep and 31 mm over the toes. That fits a foot up to about **260 mm long (US M8.5–9, EU 42)** with toe room. For a bigger foot, raise `length` (and `max_width`) in `params.json`: every curve scales with them.

### Shoe body

Print it in **TPU 95A** so it flexes on the foot and the cable tension can pull the upper in. Use 0.2 mm layers, 3 walls and 10–15 % gyroid infill (about 420 g and 45–70 h at 15 %). You need a bed of at least 300 mm.

**Supports.** The roof of the toe box (about 130 cm² inside the shoe) need tree supports. Remove the inner ones through the collar and the lacing throat, before you fit the tongue. TPU supports are tough to remove: set a 0.3 mm support Z gap, or use a PLA support interface on a dual-extrusion printer, which peels cleanly off TPU.

### Dial mechanism (per dial: housing + spool + knob)

Print in **PETG** (PLA+ works) at 0.12–0.16 mm layers, 100 % infill, **no supports**:

* housing: flange down
* spool: pawls down (the three thin arms must print flat on the bed so they flex)
* knob: knurled face down

Print one set first and check the fit. The spool should turn freely on the axle, and the axle ridge should click into both detent grooves. If it is too tight, raise `dials.mechanism.clearance` in `params.json` (default 0.2 mm); if the pawls slip, raise `pawl_tip_r`.

### What else you need

* 3 lengths of **1.0 mm braided line** (Dyneema/PE fishing line, 30–50 kg). The build report gives the length each dial needs (about 22–28 cm, plus 5 cm for knots).
* 6 **M2 × 6 mm self-tapping screws** (2 per housing), plus flexible glue (e.g. E6000) under each housing flange, because screws alone hold poorly in TPU
* optional: short pieces of **PTFE tube, 2 mm OD / 1 mm ID**, to line the guide bores (2.2 mm) and lower friction
* a drop of **CA glue** per knob, and TPU-compatible glue for the tongue

### Assembly (per dial)

1. Screw the housing onto its pod with the two cable ports facing up toward the lacing opening.
2. Feed the line from one port up to the first outer-edge guide, across the tongue, around the U-guide on the inner edge, back across to the second outer-edge guide, and down to the other port.
3. Pass both ends through the housing's cable ports. Push each end into a radial hole in the spool groove, pull it out through the knot pocket on the underside, tie a stopper knot and pull it back.
4. Push the spool down onto the axle until it clicks twice, then glue the knob onto the hex key.

### Tongue

Bend the flat tongue into the throat, padded end up at the collar. Glue its front 15 mm to the inside of the vamp just in front of the end of the lacing slot. The rest must stay free so the two eyelet sides can slide over it.

### Use

* **Tighten:** push the knob down and turn it **clockwise**. It clicks 24 times per turn and holds.
* **Release:** pull the knob up about 3 mm until it clicks. The spool then spins free and you can slip the shoe off.
* Each dial closes one zone of the lacing opening over the tongue: front dial at the toe end, middle dial at the midfoot, rear dial at the collar.

The build report lists for every part: watertightness, winding, body count, volume, overhang share and sampled wall thickness, plus the dial mechanism's interference checks (engaged, turning and released).
