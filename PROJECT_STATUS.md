# Circuit AI project status

Phase 2 remains active on `phase2-independent-model`. Phase 4 and production changes require separate approval and evidence from the quality gates.

## CircuitLM 0.5 checkpoint

- 326 authored training descriptions, eleven reviewed intents plus the unsupported class, 40 component definitions and eleven reviewed topologies. Local mode also accepts complete pin-level prose using a deterministic parser.
- The image-derived AT89C51 / LM35 / ADC0804LCN subsystem adds a parallel digital bus, explicit control wiring, separate clock nets and an analog input. Physical packages and power pins are identified in the catalog. [Reference provenance](training/REFERENCE_SCHEMATICS.md)
- Studio can trace a net, list its terminals, distinguish continuous, label-only and interrupted routing, and display nominal calculations for a validated one-pole RC circuit. The calculation uses the ideal unloaded formula, not simulation. [Stanford filter reference](https://web.stanford.edu/class/archive/engr/engr40m.1178/slides_sp17/lecture14_annotated.pdf)
- On the 21 unchanged Chromium cases, endpoint label duplication dropped from 790 to 229 labels. The independent SVG measure found zero net-label overlaps in both sets and unchanged aggregate wire length and crossings. Continuous nets carry one label; fallback nets keep their terminal labels.
- The ADC benchmark passed 19 of 19 continuous nets with zero unintended contacts and 27 undotted crossings. The 1 kΩ / 100 nF RC case passed three nets and reported 1,592 Hz nominal cutoff. Total local checks passed 105 backend tests and 251 of 251 strict net checks across 23 Chromium submissions. Browser editing, import, export, and mobile checks passed.

## Published topology pilot

Four published references (MIT, Microchip, Arduino and Texas Instruments) are frozen in [published-v1](training/benchmarks/README.md). Prompt wording and adapted netlists were authored locally and excluded from training. CircuitLM requested clarification on all four free-form descriptions. Supplying the expected terminal groups directly yielded 15 of 15 continuous nets with zero unintended contacts. The six-net LM358 diagram had 18 undotted crossings and long feedback loops. These are pilot counts, not the independent 98% gate.

The pin-level parser now understands reference-first sentences such as `R1 is a 330 ohm resistor` and infers connected groups from explicit terminal joins. Connecting differently named nets produces a clarification rather than silently merging them. The classifier weights and training corpus remain at version 0.5. Local results are 108 backend tests and 254 of 254 strict net checks across 24 authored browser submissions, plus the published pilot above.

## Parameterized passive requests

Local mode now builds a two-resistor voltage divider or a first-order RC low-pass filter from a circuit heading and component roles. The grammar accepts variable values and units, clause order, and optional reference designators. It requires every applicable role and rejects duplicate or unsupported constraints. CircuitLM weights remain at 0.5.

Studio reports an unloaded nominal output voltage and gain for a verified divider topology, or cutoff and time constant for a recognized RC filter. The engineering formulas follow [Microchip's voltage divider reference](https://developerhelp.microchip.com/xwiki/bin/view/products/amplifiers-linear/analog-sensor-conditioning-circuits/voltage-divider/) and [Stanford's RC filter lecture](https://web.stanford.edu/class/archive/engr/engr40m.1178/slides_sp17/lecture14_annotated.pdf). These are ideal calculations, not simulation.

Verification passed 118 backend tests and 260 of 260 net checks across 26 authored browser submissions. The published-v1 pilot stayed at zero exact free-form prompts out of four and 15 of 15 routed reference nets. No published-v1 prompt was used to train or register an alias.

Example: *Design a voltage divider. Use a 12 V source. The upper resistor is 33 kohm. The lower resistor is 10 kohm. Calculate the nominal output voltage.*

## Open acceptance work

The authored suite includes reviewed prompts and a small set of unfamiliar pin-explicit designs. Effects such as component substitutions, ambitious functional requirements, real operation, and arbitrary pinout coverage need separate verification. The 98% target requires a frozen, diverse external holdout and independent scoring. Native schematic ERC and simulation have yet to run. The ADC still has crossings and packed text near the interfaces, and many devices remain functional blocks.

Continue by grading out-of-corpus prompts and source-backed netlists separately, improving label-to-wire clearance and wire lengths, and adding package-specific symbols. Record reference provenance and failed cases. For deployment, use only Preview on the existing AnEmpire `circuit-api` project, verify the exact commit and test actual Studio requests.

## Preview test prompts

- ADC long prompt is `ADC_PROMPT` in [image_reference.py](app/image_reference.py). Expected 11 components, 19 continuous nets.
- First-order filter: *Use a 5 V DC source named V1, a 1 kohm resistor named R1, and a 100 nF capacitor named C1. Connect V1 positive to R1 pin 1 on net INPUT. Connect R1 pin 2 to C1 pin 1 on net OUT. Connect C1 pin 2 to V1 negative on net RETURN.*
