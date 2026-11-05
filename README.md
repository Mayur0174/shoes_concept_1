# Soletta 3-dial trail shoe: parametric CAD

A parametric CAD model of the Soletta technical trail shoe, traced from the reference photographs. It has:

* a chunky grey sole tub with a rounded lip
* a chevron-lug outsole with a closed midfoot
* a padded collar and heel badge
* a **laceless 3-dial cable closure**: three working, printable ratchet dials on the outer side. Each dial pulls one loop of line through moulded guides on both edges of the lacing opening, across a tongue with a centre webbing strip and keeper loops.

The line itself is fitted after printing and is not part of the model.

There are two builds from the same traced shape:

| Build | What it is for | Script | Parameters | Release |
|---|---|---|---|---|
| **Printable** | the real, working shoe: hollow foot cavity, separate tongue, real dial mechanism, guide bores | `build.py` | `params.json` | `build-N` |
| **Display** | renders and viewing: the same shape, solid, no bores | `build_display.py` | `params_display.json` | `display-N` (includes a STEP assembly) |

All the code runs on GitHub Actions, so nothing needs to be installed locally. Every push builds the models. Each printable run publishes a release with zipped STEP, STL, printable and assembly files, and commits preview renders to `renders/` and a validation report to `reports/`.

## Editing the model

Every dimension is in [`params.json`](params.json):

* master length, width, stack heights and toe spring
* the profile tables traced from the photos (`tables`)
* dial size, placement and the mechanism (`dials`)
* lacing zones and guide sizes (`lacing`)
* the tongue and its keeper loops (`upper.tongue`)

Change a value, commit and push, and CI rebuilds everything. `"quality": "full"` is production resolution (0.35 mm body grid); `"draft"` gives a fast preview (0.8 mm). You can also start a build from **Actions → build-cad → Run workflow**.

`params_display.json` uses the same tables. The values are millimetres measured from the side view (0.314 mm/px) and top view (0.325 mm/px). The side silhouette matches the photo at IoU ≈ 0.92.

## How it is modelled

| Part | Technique | Files |
|---|---|---|
| Main body: sole tub, upper, foot cavity, 30 mm lacing opening, padded collar, heel badge, 3 dial pods (flat seat, 2 × M2 pilot holes, 2 cable ports), lacing guides | Signed-distance CSG with smooth blends, meshed by marching cubes | `components/body*.stl`, `step/body.step` (faceted) |
| Lacing guides (per dial) | Two bent guides on the outer edge and a U-guide on the inner edge. Each is a 5.2 mm moulded tube with a 2.2 mm bore on a flat 9 mm overlay pad. | part of the body |
| Outsole | Perimeter block lugs, chevron pods, cross-hatch floor, shank diamond and ribs over a closed midfoot | `components/outsole*.stl`, `step/outsole.step` |
| Tongue (separate part) | Follows the inside of the upper with a 1 mm gap, padded top, centre webbing strip with 6 keeper loops (one where each line crosses). It is printed flat. | `printable/tongue_tpu_flat.stl`, `components/tongue_as_fitted.stl` |
| Dial mechanism (× 3) | Exact B-rep in CadQuery: housing (24 ratchet teeth, snap axle, 2 cable ports), spool (3 compliant pawls, cable groove, knot pockets, hex key) and knob. It is 15 mm tall assembled. | `components/dial_{housing,spool,knob}.stl`, `step/dial_*_exact_brep.step` |

`step/soletta_assembly.step` is a named, coloured assembly that opens in Fusion 360. The dial parts are exact solids. The organic parts are faceted solids: edit them through `params.json`, or convert them in Fusion with *Mesh → Convert*.

## 3D printing

`printable/` contains:

* `shoe_body_with_outsole.stl` / `.3mf`: one watertight piece; print it upright on the outsole
* `dial_kit_x3_plate.stl`: 3 housings, 3 spools and 3 knobs, already in print orientation
* `tongue_tpu_flat.stl`: the tongue, padded end at one end and glue flap at the other, keeper loops up
* `dial_housing_single.stl`, `dial_spool_single.stl`, `dial_knob_single.stl`: one of each, for a test print

### Fit

At the default size (290 mm long) the inside is:

* about 266 mm long
* 104 mm wide at the ball and 72 mm at the heel
* 47 mm high over the ball and 30 mm over the toes

That fits a foot up to about 255 mm long (US M8–8.5). For a bigger foot, raise `length` (and `max_width`) in `params.json`: every curve scales with them.

### Shoe body

Print it in **TPU 95A**, so it flexes on the foot and the dials can pull the opening closed.

* Settings: 0.2 mm layers, 3 walls, 10–15 % gyroid infill.
* About 520 g and 55–85 hours at 15 % infill.
* The printed shoe is about 296 × 141 × 138 mm, so you need a bed of at least 300 mm.
* The walls are at least 2.6 mm (the build report checks this).

**Supports.** The roof of the toe box and the outside of the collar roll need tree supports. Remove the inner ones through the collar and the lacing opening, before you fit the tongue. TPU supports are tough to remove: set a 0.3 mm support Z gap, or use a PLA support interface on a dual-extrusion printer, which peels cleanly off TPU.

### Dial mechanism (per dial: housing + spool + knob)

Print in **PETG** (PLA+ works) at 0.12–0.16 mm layers, 100 % infill, **no supports**:

* housing: flange down
* spool: pawls down (the three thin arms must print flat on the bed so they flex)
* knob: knurled face down

Print one set first and check the fit. The spool should turn freely on the axle, and the axle ridge should click into both detent grooves. If it is too tight, raise `dials.mechanism.clearance` (default 0.2 mm). If the pawls slip, raise `pawl_tip_r`.

### Tongue

Print it flat in TPU with the keeper loops facing up; the loops are short bridges and need no supports.

## Assembly

### What else you need

* 1.0 mm braided **Dyneema/PE line** (30–50 kg), cut into 3 pieces: **35 cm** (front dial), **36 cm** (middle dial), **38 cm** (rear dial). The build report gives each route's exact length (about 23, 24.5 and 25.5 cm). The rest is for knots and is trimmed off.
* 6 **M2 × 6 mm self-tapping screws** (2 per housing), plus flexible glue (e.g. E6000) under each housing flange, because screws alone hold poorly in TPU
* **CA glue** (superglue), and a TPU-compatible glue for the tongue
* optional: short pieces of **PTFE tube, 2 mm OD / 1 mm ID**, to line the guide bores and lower friction

### Order

1. **Tongue.** Slide the flat tongue into the lacing opening, padded end up at the collar and keeper loops facing out. Glue only its front 15 mm (the glue flap) to the inside of the toe box, just in front of the end of the opening.
2. **Housings.** Glue and screw each housing onto its pod, with its two cable ports facing up toward its guides.
3. **Line.** Thread each dial as described below, with the shoe fully open.
4. **Spools and knobs.** Fit them last.

### Threading the line (repeat for each dial)

Each dial owns one zone of the opening: the front dial the guides at the toe end, the middle dial the middle set, the rear dial the set at the collar.

1. Cut the ends at an angle and soak the last 1 cm in CA glue. Once dry, it acts as a stiff needle through the 2.2 mm bores. A loop of thin wire helps through the curved U-guides.
2. From one cable port of the housing, run the line up to the **first outer-edge guide** and push it through, so it comes out pointing across the opening.
3. Take it across the tongue **through the keeper loop** on the centre strip, to the **U-guide on the inner edge**. Feed it in one end of the U and out the other.
4. Take it back across the tongue **through the next keeper loop**, to the **second outer-edge guide**, and push it through.
5. Run it down to the housing's **other cable port**. Pull the loop until the line lies flat with no twists.
6. Push each end through its cable port into the housing. Feed it into one of the two radial holes in the spool's groove, and pull it out through the knot pocket on the spool's underside.
7. Tie a stopper knot in each end (double overhand or figure-eight), add a drop of CA glue, trim to about 3 mm, and pull the knots back into their pockets.
8. Push the spool onto the axle until it clicks twice, then glue the knob onto the hex key.

## Use

* **Tighten:** push the knob down and turn it **clockwise**. It clicks 24 times per turn and holds. The spool winds both ends in, pulling the inner U-guide toward the outer guides and closing that zone over the tongue.
* **Release:** pull the knob up about 3 mm until it clicks. The spool spins free and the line pays out, so you can open the shoe and step out.
* If a zone closes completely before it feels snug, re-tie that dial with a slightly shorter line; if it cannot reach snug, use a longer one.

## Checks in every build

The build report (`reports/report.md`) lists, for every part:

* watertightness, body count, volume, overhang share and sampled wall thickness
* the dial mechanism's interference checks (engaged, turning and released)
* every lacing guide bore open end to end
* the line length per dial
* the lacing opening clear from footbed to top
* the tongue's sliding clearance under the opening edges
