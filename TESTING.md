# Phase 2 validation record

Baseline commit `966c791` passed both GitHub workflows and all 88 locally reproduced backend tests. The Chromium suite's nine original prompts yielded 16 of 49 uninterrupted nets. In particular, the Uno/LCD produced 0 of 10 and the temperature-controlled motor produced 1 of 9. Matching labels supplied connectivity where routes were incomplete.

The updated branch passed 92 Python tests. Chromium submitted prompts through Studio and measured SVG geometry with `scripts/routing_measurement.py`, which does not import RouteGuard or the router. The expected netlists are in `scripts/frontend_netlists.json`. The checker verifies exact pin membership, wire continuity, symbol-body clearance, junction dots, and ambiguous cross-net contacts. A plain orthogonal crossing is valid when both wires continue through it and no junction dot is present.

| Chromium cases | Passing nets | Coverage |
| --- | ---: | --- |
| Nine original prompts | 49 / 49 | Seven distinct circuits, including Uno/LCD and motor driver |
| Three additional local prompts | 16 / 16 | Alternate motor wording, Mega/LDR, SN74HC14N |
| Three explicit netlists outside the classifier corpus | 20 / 20 | LM358N buffer, dual filter, dual transistor LED loads |
| LED-bank stress tests | 118 / 118 | 16, 32, and 64 branches, all with zero wire crossings |
| Total | 203 / 203 | 18 browser submissions, including repeated topologies |

The 32-channel bank initially had a label-only VCC rail and 1,286 crossings. Routing repeated branches along shared rails resolved both. The general router completed the temperature motor's 9 nets with 16 undotted crossings; the dual filter still had 20 undotted crossings on five nets. The browser smoke test also exercised edits, drag, downloads in three formats, JSON import, the examples panel, and mobile overflow. Chromium verified that an unsupported add-on to a reviewed local prompt was rejected.

The visual review compared the IEC series resistor and LED symbols with the [KiCad tutorial](https://docs.kicad.org/9.0/en/getting_started_in_kicad/getting_started_in_kicad.html), and the motor stage's enable, direction inputs, split supplies and paired loads with [TI's L293/L293D reference](https://www.ti.com/lit/ds/symlink/l293d.pdf). The wire audit follows [KiCad's junction convention](https://docs.kicad.org/9.0/en/eeschema/eeschema.html) and [Proteus's documented branch junctions](https://www.labcenter.com/documentation/mergedProjects/Schematic%20Capture%20Manual/GENERAL_CONCEPTS/Wiring_Up.htm). Several dense worksheets still have crowded labels and blocks standing in for full device symbols. Native KiCad/Proteus ERC and simulation have yet to be run.

The score applies to this authored suite. The independent 98% acceptance threshold still needs a blinded set of externally sourced, diverse netlists and a separate visual review. Electrical suitability, simulation and hardware operation are outside this measurement.

Run `python -m pytest -q` for backend tests. Install Playwright's Chromium and start Uvicorn on port 8765, then run `python scripts/frontend_benchmark.py` and `python scripts/browser_test.py`. Set `BROWSER_EXECUTABLE` to use an installed Chromium and `STUDIO_TEST_URL` to point at a running preview.

# v0.3 validation record

- Python suite: 65 passing tests, including the original v1 regression tests.
- 1,000 deterministic generated netlist variations are structurally checked and parsed as SVG; every rendered pin-to-net mapping is compared with the source netlist.
- 200-component layout/import boundary and 129-component LED-bank case passes structure/render checks.
- Arduino Uno/LCD reference checks cover RS, enable, data, contrast, ground, and backlight connections.
- Negative cases cover supply shorts, direct voltage mismatches, missing pins/values, unknown parts/pins, duplicate references/nets, conflicting pin assignments and custom-part override attempts.
- Custom part output conflicts, SVG escaping, JSON round trips, PNG dimensions, authentication and size limits are tested.
- AI boundaries are tested with mocked valid, clarification, malformed and unavailable responses. A live model provider was not configured; free-form model quality has not been validated.
- JavaScript syntax checked with Node. Live browser smoke checks passed for prompt generation, value edits reflected in SVG, draggable symbol coordinates, SVG/PNG/editable JSON downloads, and all three example checks. The local environment could not launch Chromium because its process socket operation was denied; live UI checks used the available cloud browser. Mobile viewport and browser file-import automation were not exercised; backend JSON round trips passed.

## Run your own checks

Open `/studio`, load an example, edit the component/net tables, apply edits and download a diagram. The **Run example tests** button checks all three shipped example netlists on your current server. Import editable JSON to resume a saved design.

For the full suite: `python -m pytest -q` after installing `requirements-dev.txt`. Optional Playwright browser smoke test: `python scripts/browser_test.py` against a running server on port 8765.

These tests validate software behavior, not physical circuit correctness. No SPICE run, Proteus simulation, tolerance analysis, board build, GPIO drive-strength validation or live AI benchmark has been performed. Generated case count is not a claim of thousands of supported circuit families.

GitHub Actions passed on commit `a87ccd1d007e8e68fd2bac176f48a664f46cd69d`. The public test studio is https://circuit-api-two.vercel.app/studio . Free-form AI is not configured on this deployment.
