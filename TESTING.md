# v0.3 validation record

- Python suite: 65 passing tests, including the original v1 regression tests.
- 1,000 deterministic generated netlist variations are structurally checked and parsed as SVG; every rendered pin-to-net mapping is compared with the source netlist.
- 200-component layout/import boundary and 129-component LED-bank case passes structure/render checks.
- Arduino Uno/LCD reference checks cover RS, enable, data, contrast, ground, and backlight connections.
- Negative cases cover supply shorts, direct voltage mismatches, missing pins/values, unknown parts/pins, duplicate references/nets, conflicting pin assignments and custom-part override attempts.
- Custom part output conflicts, SVG escaping, JSON round trips, PNG dimensions, authentication and size limits are tested.
- AI boundaries are tested with mocked valid, clarification, malformed and unavailable responses. A live model provider was not configured; free-form model quality has not been validated.
- JavaScript syntax checked with Node. Browser smoke testing is performed separately against the deployed studio; the local environment could not launch Chromium because its process socket operation was denied.

## Run your own checks

Open `/studio`, load an example, edit the component/net tables, apply edits and download a diagram. The **Run example tests** button checks all three shipped example netlists on your current server. Import editable JSON to resume a saved design.

For the full suite: `python -m pytest -q` after installing `requirements-dev.txt`. Optional Playwright browser smoke test: `python scripts/browser_test.py` against a running server on port 8765.

These tests validate software behavior, not physical circuit correctness. No SPICE run, Proteus simulation, tolerance analysis, board build, GPIO drive-strength validation or live AI benchmark has been performed. Generated case count is not a claim of thousands of supported circuit families.
