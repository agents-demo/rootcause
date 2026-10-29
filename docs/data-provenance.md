# Data provenance

The public demo is synthetic. The pilot connects to real factory systems, on site. This sheet stays
with every data pack.

## The public pack

| Asset | Source | Licence | Notes |
|---|---|---|---|
| `web/public/assets/bracket-*.svg` | Generated in-house for this repo | MIT | Cast bracket, optical and x-ray illustration |
| `web/public/assets/housing-surface.svg` | Generated in-house | MIT | Injection-moulded housing, short shot |
| `web/public/assets/weld-surface.svg` | Generated in-house | MIT | Cell tab weld, crack |
| `web/public/assets/solder-surface.svg` | Generated in-house | MIT | QFN solder void |
| `demo-pack.json` scenarios | `server/rootcause/demo/build_pack.py`, fixed seed 417 | MIT | Sensor series, batches, cases, reports, dashboard |
| Detector test images | `server/rootcause/engine/detection.py`, fixed seeds | MIT | Generated at test time; never shipped as customer data |

**No MVTec AD data** is used. MVTec AD is CC BY-NC-SA 4.0 (non-commercial) and may be used for
internal R&D only. It is not in this repository or the public deployment.

**No customer images, batches, serials or machine identifiers** are in the public pack. The four
scenarios are invented. The supplier names, batch ids and people are fictional.

## What the numbers mean

- The sensor series are generated from a baseline, a standard deviation and a shaped anomaly. The
  ranking is computed from those series with the same code the pilot uses.
- The detections displayed in the demo are precomputed for the seeded case. The detector in
  `engine/detection.py` is real and tested; the fine-tuned model is a pilot deliverable.
- The dashboard figures are scenario data, not a performance claim about a real factory.
- The NPU latency shown in the admin screen is illustrative. The broker in `npu/` reports the real
  backend and latency when it runs.

## The pilot pack

For a customer deployment:

1. Keep a provenance sheet with the pack: source system, extraction date, owner, permission.
2. Written demo-use permission, not just a pilot NDA, before any image is shown publicly.
3. Strip serial numbers and operator names unless they are required for the case.
4. Keep the raw data on the factory network; export only the approved report.
5. If a customer wants a cross-factory pattern share, it is opt-in and limited to cause labels and
  factor ranges. No images, batches or machine identifiers.

## Model provenance

Every case records the model version (`rootcause-0.9.0` in the demo). A pilot case should also
record:

- detector artifact hash and training dataset version;
- NPU backend and device (CPU vs Ascend);
- ranking engine version;
- data sources read for the case.

This is what makes “the model said so” auditable.

## Commercial-safe public assets

For a public or commercial demo, use assets generated in-house (as here) or a licensed defect pack.
Do not use MVTec AD, customer images or images pulled from the web. The provenance sheet is part of
the demo, not an afterthought.
