# Circuit AI project status

Phase 2 remains active on `phase2-independent-model`. Phase 4 and production changes require separate approval and evidence from the quality gates.

## CircuitLM 0.5 checkpoint

- 326 authored training descriptions, eleven reviewed intents plus the unsupported class, 40 component definitions and eleven reviewed topologies. Local mode also accepts complete pin-level prose using a deterministic parser.
- The image-derived AT89C51 / LM35 / ADC0804LCN subsystem adds a parallel digital bus, explicit control wiring, separate clock nets and an analog input. Physical packages and power pins are identified in the catalog. [Reference provenance](training/REFERENCE_SCHEMATICS.md)
- Studio can trace a net, list its terminals, distinguish continuous, label-only and interrupted routing, and display nominal calculations for a validated one-pole RC circuit. The calculation uses the ideal unloaded formula, not simulation. [Stanford filter reference](https://web.stanford.edu/class/archive/engr/engr40m.1178/slides_sp17/lecture14_annotated.pdf)
- On the 21 unchanged Chromium cases, endpoint label duplication dropped from 790 to 229 labels. The independent SVG measure found zero net-label overlaps in both sets and unchanged aggregate wire length and crossings. Continuous nets carry one label; fallback nets keep their terminal labels.
- The ADC benchmark passed 19 of 19 continuous nets with zero unintended contacts and 27 undotted crossings. The 1 kΩ / 100 nF RC case passed three nets and reported 1,592 Hz nominal cutoff. Total local checks passed 105 backend tests and 251 of 251 strict net checks across 23 Chromium submissions. Browser editing, import, export, and mobile checks passed.

## Open acceptance work

The authored suite includes reviewed prompts and a small set of unfamiliar pin-explicit designs. Effects such as component substitutions, ambitious functional requirements, real operation, and arbitrary pinout coverage need separate verification. The 98% target requires a frozen, diverse external holdout and independent scoring. Native schematic ERC and simulation have yet to run. The ADC still has crossings and packed text near the interfaces, and many devices remain functional blocks.

Continue by grading out-of-corpus prompts and source-backed netlists separately, improving label-to-wire clearance and wire lengths, and adding package-specific symbols. Record reference provenance and failed cases. For deployment, use only Preview on the existing AnEmpire `circuit-api` project, verify the exact commit and test actual Studio requests.

## Preview test prompts

- ADC long prompt is `ADC_PROMPT` in [image_reference.py](app/image_reference.py). Expected 11 components, 19 continuous nets.
- First-order filter: *Use a 5 V DC source named V1, a 1 kohm resistor named R1, and a 100 nF capacitor named C1. Connect V1 positive to R1 pin 1 on net INPUT. Connect R1 pin 2 to C1 pin 1 on net OUT. Connect C1 pin 2 to V1 negative on net RETURN.*
