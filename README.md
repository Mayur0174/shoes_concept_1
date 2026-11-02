# Soletta dual-dial trail shoe: parametric CAD

A parametric CAD reconstruction of the Soletta technical trail shoe concept. It has an organic midsole with three through-chambers, a chevron-lug outsole and three rotary dials on each side (six in total) with routed 1.5 mm tension cables. It also has a toe cap, heel counter with pull tab, padded collar, tongue, lace panel, 6+6 eyelets and real 4.5 mm round laces tied in a bow.

All the code runs on GitHub Actions, so nothing needs to be installed locally. Every push builds the model, and each run:

* publishes a **GitHub Release** `build-N` with zipped STEP, STL, printable and assembly files
* commits preview renders to `renders/` and a validation report to `reports/`

## Editing the model

Every dimension is in [`params.json`](params.json): master length, width and height, heel and forefoot stack, toe spring, chamber positions, dial size and placement, cable targets, eyelets, lace diameter and so on. Change a value, commit and push, and CI rebuilds everything. Set `"quality": "full"` for production resolution (0.35 mm body grid). `"draft"` gives a fast preview (0.8 mm).

You can also start a build by hand from the **Actions → build-cad → Run workflow** button and choose the quality there.

## How it is modelled

| Part | Technique | Files |
|---|---|---|
| Main body (midsole, upper, wraps, tongue, collar, heel counter, pods, brackets, cables, guides, anchors, eyelets) | Signed-distance CSG with smooth (G2-like) blends, meshed by marching cubes | `components/body*.stl`, `step/body.step` (faceted) |
| Outsole | Same SDF method: perimeter block lugs, pods with chevrons, cross-hatch floor, shank diamond, midfoot web | `components/outsole*.stl`, `step/outsole.step` |
| Laces | Tubes draped over the finished surface, over/under crossings, bow with aglets | `components/lace_assembly*.stl`, `step/lace_assembly.step` |
| Dials (x6) | Exact B-rep in CadQuery: knurled ring, centre cap, hex drive, notch, grooves, snap socket | `components/dial_*.stl`, `step/dial_single_exact_brep.step` |

All the shapes are real geometry, not textures. The SDF approach guarantees the organic parts are watertight and manifold, with filleted transitions.

`step/soletta_assembly.step` is a named, coloured assembly that imports into Fusion 360. The dials are exact B-rep solids there. The organic bodies are faceted B-rep solids, which you can edit as solids in Fusion or convert with *Mesh → Convert*. To change their shape parametrically, edit `params.json` instead.

## 3D printing

`printable/` contains:

* `shoe_body_with_outsole.stl` / `.3mf`: one watertight piece; print it upright on the outsole
* `dials_x6_plate.stl`: print bottom face down; they press onto the 6 mm bracket pegs (0.15 mm clearance)
* `laces_print_flexible.stl`: print in TPU

Recommended settings: 0.2 mm layers, 3 walls, tree supports for the midsole chamber roofs and toe-box overhangs, and TPU 95A for the outsole if you want it flexible. At full size (290 mm long) you need a bed of at least 300 mm. Otherwise scale `length`, `max_width` and `height` in `params.json` (or scale in the slicer).

The build report lists for every part: watertightness, winding, body count, volume, overhang share and sampled wall thickness.
