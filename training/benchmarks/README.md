# Published topology benchmark

The published-v1 fixture freezes four externally sourced circuit topologies, their adaptations, locally authored prose prompts, and expected netlists. It is excluded from the classifier corpus and reviewed-prompt aliases. It is a small pilot with independent source provenance, rather than a blinded acceptance benchmark prepared by a separate evaluator.

Run `python scripts/published_benchmark.py` with Chromium and a Studio server on port 8765. Use `STUDIO_TEST_URL`, `BROWSER_EXECUTABLE`, and `PUBLISHED_RESULTS_DIR` to override defaults.

Each case is submitted twice through Studio. Local mode must reproduce the declared devices, values, and groups of terminals to count as an exact interpretation. A clarification is reported separately from an incorrect accepted draft. Net names are ignored in this score because the prose does not prescribe them. Built-in mode receives the reference circuit directly. The separate SVG checker verifies expected pins, continuity, contacts, symbol clearance, and junctions. Crossings and wire length are reported separately. Visual metrics use SVG units and do not establish circuit behavior.

The initial comparison on commit `f47f827` produced 0 exact interpretations, four clarifications, and 15 of 15 verified nets when given the reference circuits. The six-net LM358 example had 18 undotted crossings in the initial render. These counts do not establish a general routing accuracy percentage. Preserve published-v1 for regression comparison and add fresh topologies and prompts in a separately versioned fixture.
