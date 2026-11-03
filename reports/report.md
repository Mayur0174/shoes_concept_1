# Soletta CAD build report (full quality)

Elapsed: 340.4 s. Grid resolution (mm): {'body': 0.35, 'outsole': 0.25, 'laces': 0.22}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 3,772,654 | True | True | 1 | 989.9 | 298.2 x 130.6 x 106.9 | 17.5% |
| outsole | 2,437,890 | True | True | 1 | 106.6 | 291.9 x 112.8 x 22.8 | 24.5% |
| laces | 1,131,922 | True | True | 1 | 25.2 | 94.8 x 79.5 x 72.8 | 13.1% |
| dial housing (each) | 8,852 | True | True | 1 | 4.0 | 36.0 x 40.4 x 13.4 | 0.2% |
| dial spool (each) | 5,596 | True | True | 1 | 2.9 | 26.0 x 25.9 x 12.6 | 4.1% |
| dial knob (each) | 14,328 | True | True | 1 | 6.6 | 34.0 x 34.0 x 8.0 | 4.8% |
| printable shoe (body+outsole) | 943,164 | True | True | 1 | 1096.5 | 298.2 x 130.6 x 114.9 | 23.8% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 3460 | 1.25 | 2.25 | 8.05 | 7.89% |

Thin samples are expected on the cable channel sheaths (4 mm tube, 1.6 mm bore), the inner tongue, guide clips and eyelet rims, which are features rather than walls.

## Dial mechanism checks (exact B-rep)

| check | value |
|---|---|
| spool_vs_knob_mm3 | 0.0 |
| engaged_rest_spool_vs_housing_mm3 | 0.0 |
| engaged_knob_vs_housing_mm3 | 0.0 |
| released_spin_max_interference_mm3 | 0.0 |
| engaged_turning_pawl_flex_overlap_mm3 | 1.086 |
| tooth_engagement_mm | 0.8 |
| clicks_per_turn | 24 |
| cable_per_turn_mm_each_end | 53.4 |
| release_lift_mm | 3.2 |
| stack_height_mm | 19.6 |

## Dial frames

| Dial | Origin (mm) | Axis | Seat height |
|---|---|---|---|
| L1 | [185.63, 68.23, 53.6] | [-0.015, 0.864, 0.504] | 9.0 |
| L2 | [132.09, 60.67, 49.7] | [0.003, 0.991, -0.132] | 9.0 |
| L3 | [69.09, 60.72, 63.35] | [0.004, 1.0, -0.029] | 6.46 |
| R1 | [185.11, -65.9, 53.59] | [-0.036, -0.863, 0.504] | 9.0 |
| R2 | [132.04, -54.68, 49.7] | [0.002, -0.991, -0.132] | 9.0 |
| R3 | [69.51, -59.52, 63.35] | [0.023, -0.999, -0.029] | 6.67 |

## Warnings

- outsole: removed 11 floating fragment(s)
- laces: removed 5 floating fragment(s)
