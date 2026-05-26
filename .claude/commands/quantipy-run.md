---
description: Run the QuantiPy Polarity single-shot pipeline on a folder of images
---

Run `quantipy run --config ./config.yaml` if a config.yaml is present in the
current working directory. If not found, run `quantipy init-config --mode masks`
(or the user-specified mode) first, then ask the user to confirm before
running `quantipy run`. Note: `quantipy run` is stubbed in Phase 1 — it will
exit non-zero with a "not yet implemented" message until Phase 5 lands.
