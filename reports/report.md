# Soletta CAD build report (full quality)

Elapsed: 377.9 s. Grid resolution (mm): {'body': 0.35, 'outsole': 0.25, 'laces': 0.22}

| Component | Triangles | Watertight | Winding OK | Bodies | Volume (cm3) | Extents (mm) | Overhang >45 deg |
|---|---|---|---|---|---|---|---|
| body | 3,956,818 | True | True | 1 | 889.7 | 298.2 x 127.0 x 106.9 | 18.7% |
| outsole | 2,443,970 | True | True | 1 | 115.2 | 291.8 x 112.6 x 22.8 | 23.6% |
| laces | 660,744 | True | True | 1 | 15.1 | 98.0 x 47.7 x 42.5 | 16.1% |
| dial housing (each) | 8,790 | True | True | 1 | 3.0 | 30.6 x 33.4 x 13.4 | 0.3% |
| dial spool (each) | 6,560 | True | True | 1 | 1.9 | 21.6 x 21.6 x 12.6 | 4.3% |
| dial knob (each) | 14,088 | True | True | 1 | 3.7 | 26.0 x 26.0 x 8.0 | 5.3% |
| printable shoe (body+outsole), reloaded STL | 955,240 | True | True | 1 | 1000.5 | 298.2 x 127.0 x 114.7 | 21.5% |

## Body wall thickness (SDF ray sampling)

| samples | p01 | p05 | median | share < 2.5 mm |
|---|---|---|---|---|
| 3656 | 1.45 | 2.25 | 6.65 | 6.37% |

Thin samples are expected on the cable channel sheaths (4 mm tube, 1.6 mm bore), the inner tongue, guide clips and eyelet rims, which are features rather than walls.

## Function checks on the printable STL

| check | value |
|---|---|
| channel L1 open, min clearance from centre line mm | 0.8 |
| channel L1 length mm | 86.7 |
| channel L2 open, min clearance from centre line mm | 0.8 |
| channel L2 length mm | 102.9 |
| channel L3 open, min clearance from centre line mm | 0.8 |
| channel L3 length mm | 90.1 |
| channel R1 open, min clearance from centre line mm | 0.8 |
| channel R1 length mm | 84.4 |
| channel R2 open, min clearance from centre line mm | 0.8 |
| channel R2 length mm | 103.5 |
| channel R3 open, min clearance from centre line mm | 0.8 |
| channel R3 length mm | 89.7 |
| tongue gap under the quarters, min mm | 1.0 |

## Dial mechanism checks (exact B-rep)

| check | value |
|---|---|
| spool_vs_knob_mm3 | 0.0 |
| engaged_rest_spool_vs_housing_mm3 | 0.0 |
| engaged_knob_vs_housing_mm3 | 0.0 |
| released_spin_max_interference_mm3 | 0.0 |
| engaged_turning_pawl_flex_overlap_mm3 | 1.255 |
| tooth_engagement_mm | 0.8 |
| clicks_per_turn | 24 |
| cable_per_turn_mm_each_end | 45.9 |
| release_lift_mm | 3.2 |
| stack_height_mm | 19.6 |

## Dial frames

| Dial | Origin (mm) | Axis | Seat height |
|---|---|---|---|
| L1 | [175.29, 67.43, 37.81] | [-0.074, 0.997, 0.035] | 7.0 |
| L2 | [128.17, 58.79, 44.16] | [0.008, 0.989, 0.15] | 5.0 |
| L3 | [57.77, 58.41, 52.07] | [-0.01, 0.996, -0.084] | 7.0 |
| R1 | [174.63, -64.19, 37.75] | [-0.103, -0.994, 0.032] | 7.0 |
| R2 | [128.25, -53.64, 44.29] | [0.011, -0.989, 0.15] | 5.85 |
| R3 | [57.95, -57.47, 52.07] | [-0.002, -0.996, -0.084] | 7.0 |

## Warnings

- body: removed 1 floating fragment(s)
- outsole: removed 5 floating fragment(s)
- laces: removed 3 floating fragment(s)
