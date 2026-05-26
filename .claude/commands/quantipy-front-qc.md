---
description: Regenerate static migration-front QC overlays
---

Run `quantipy front --auto --qc --resume --config ./config.yaml`. This
regenerates per-FOV QC overlays into results/04_migration/qc/ and keeps the
previous overlays in qc_prev/ for visual diffing after editing
migration.* config values. Note: `quantipy front` is stubbed in Phase 1;
will land in Phase 4.
