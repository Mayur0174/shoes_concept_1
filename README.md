# Soletta dual-dial trail shoe: parametric CAD

A parametric CAD reconstruction of the Soletta technical trail shoe concept. It has an organic midsole with three through-chambers, a chevron-lug outsole and three **working, printable ratchet dials** on the outer side and three **webbing straps with moulded ladder-lock buckles** on the inner side, as in the reference sheet. Each dial winds a loop of real 1 mm line through a channel inside a moulded webbing strap that runs up to the lace panel or collar, as in the reference sheet. It also has a toe cap, heel counter with pull tab, padded collar, a hollow foot cavity, an open lacing throat over a separate tongue, and 6+6 eyelets for real laces.

All the code runs on GitHub Actions, so nothing needs to be installed locally. Every push builds the model, and each run:

* publishes a **GitHub Release** `build-N` with zipped STEP, STL, printable and assembly files
* commits preview renders to `renders/` and a validation report to `reports/`

## Editing the model

Every dimension is in [`params.json`](params.json): master length, width and height, heel and forefoot stack, toe spring, chamber positions, dial size and placement, cable targets, eyelets, lace diameter and so on. Change a value, commit and push, and CI rebuilds everything. Set `"quality": "full"` for production resolution (0.35 mm body grid). `"draft"` gives a fast preview (0.8 mm).

You can also start a build by hand from the **Actions → build-cad → Run workflow** button and choose the quality there.

## How it is modelled

| Part | Technique | Files |
|---|---|---|
| Main body (midsole, upper, foot cavity, throat slot, inner tongue, collar, heel counter, dial pods, webbing straps with 1.6 mm cable channels, U-turn guides, toe-cage straps, eyelets) | Signed-distance CSG with smooth (G2-like) blends, meshed by marching cubes | `components/body*.stl`, `step/body.step` (faceted) |
| Outsole | Same SDF method: perimeter block lugs, pods with chevrons, cross-hatch floor, shank diamond, midfoot web | `components/outsole*.stl`, `step/outsole.step` |
| Laces (display only) | Tubes draped over the finished surface, over/under crossings, bow with aglets. Used for renders; lace the real shoe with real laces | `components/lace_assembly*.stl` |
| Dial mechanism (x6) | Exact B-rep in CadQuery: housing (ratchet teeth, snap axle, cable ports), spool (compliant pawls, cable groove, knot pockets, hex key), knob | `components/dial_{housing,spool,knob}.stl`, `step/dial_*_exact_brep.step` |

All the shapes are real geometry, not textures. The SDF approach guarantees the organic parts are watertight and manifold, with filleted transitions.

`step/soletta_assembly.step` is a named, coloured assembly that imports into Fusion 360. The dial parts are exact B-rep solids there. The organic bodies are faceted B-rep solids, which you can edit as solids in Fusion or convert with *Mesh → Convert*. To change their shape parametrically, edit `params.json` instead.

## 3D printing

`printable/` contains:

* `shoe_body_with_outsole.stl` / `.3mf`: one watertight piece; print it upright on the outsole
* `dial_kit_x3_plate.stl`: 3 housings, 3 spools and 3 knobs, already in print orientation
* `medial_straps_tpu_x3.stl`: the three inner-side straps as flat strips (print flat in TPU), or use 15 mm nylon webbing cut to the lengths in the build report
* `dial_housing_single.stl`, `dial_spool_single.stl`, `dial_knob_single.stl`: one of each, for a test print

### Shoe body

Print it in **TPU 95A** so it flexes on the foot and the cable tension can pull the upper in. Use 0.2 mm layers, 3 walls, 15–20 % gyroid infill, and tree supports for the midsole chamber roofs and the inside of the toe box (remove them through the throat). At full size (290 mm long) you need a bed of at least 300 mm. Otherwise scale `length`, `max_width` and `height` in `params.json`.

### Dial mechanism (per dial: housing + spool + knob)

Print in **PETG** (PLA+ works) at 0.12–0.16 mm layers, 100 % infill, **no supports**:

* housing: flange down
* spool: pawls down (the three thin arms must print flat on the bed so they flex)
* knob: knurled face down

Print one set first and check the fit. The spool should turn freely on the axle, and the axle ridge should click into both detent grooves. If it is too tight, raise `dials.mechanism.clearance` in `params.json` (default 0.2 mm); if the pawls slip, raise `pawl_tip_r`.

### What else you need

* 3 lengths of **1.0 mm braided line** (Dyneema/PE fishing line, 30–50 kg), about 200 mm each
* 6 **M2 × 6 mm self-tapping screws** (2 per housing)
* 15 mm **nylon webbing** for the inner straps (or the printed TPU strips)
* a drop of **CA glue** per knob
* a pair of normal **flat laces** (about 120 cm) for the eyelets

### Assembly (per dial)

1. Screw the housing onto its pod with the two cable ports facing the channel mouths.
2. Thread the line into one channel mouth, through the channel and around the U-turn guide at the far end, and back out of the other mouth.
3. Pass both ends through the housing's cable ports. Push each end into a radial hole in the spool groove, pull it out through the knot pocket on the underside, tie a stopper knot and pull it back.
4. Push the spool down onto the axle until it clicks twice, then glue the knob onto the hex key.

### Inner-side straps

Each strap runs from the loop at the lace-panel edge (the collar loop for the rear strap) down to the buckle on the midsole.

1. Pass one end under the bar of the top loop, fold it back about 20 mm and glue or stitch it.
2. At the bottom, thread the free end down through the outer slot of the buckle and back up through the inner slot.
3. Pull the free end to tighten. Friction on the centre bar holds it, and lifting the buckle's outer edge releases it.

### Use

* **Tighten:** push the knob down and turn it **clockwise**. It clicks 24 times per turn and holds.
* **Release:** pull the knob up about 3 mm until it clicks. The spool then spins free and you can slip the shoe off.
* The laces close the throat over the tongue. The dials cinch the outer side (forefoot, midfoot and heel collar), and the straps cinch the inner side.

The build report lists for every part: watertightness, winding, body count, volume, overhang share and sampled wall thickness, plus the dial mechanism's interference checks (engaged, turning and released).
