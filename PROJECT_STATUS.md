# Circuit AI project status

Phase 3 component catalog work started on `phase3-component-intelligence`, based on Phase 2 preview commit `a35dae9`. The analog package update is on `phase3-analog-packages`. The independent connection accuracy threshold and free-form interpretation gaps remain open.

## Phase 3 · Electronic component intelligence

The launch tranche adds eight physical Texas Instruments PDIP packages, bringing the catalog to 48 entries including the existing generic and logical definitions. The catalog roadmap calls for 145 entries at the intermediate checkpoint and 1,100 at the final checkpoint.

| Function | Reviewed PDIP packages |
| --- | --- |
| NAND, NOR and inverter | [SN74HC00N](https://www.ti.com/lit/ds/symlink/sn74hc00.pdf), [SN74HC02N](https://www.ti.com/lit/ds/symlink/sn74hc02.pdf), [SN74HC04N](https://www.ti.com/lit/ds/symlink/sn74hc04.pdf) |
| AND, OR and XOR | [SN74HC08N](https://www.ti.com/lit/ds/symlink/sn74hc08.pdf), [SN74HC32N](https://www.ti.com/lit/ds/symlink/sn74hc32.pdf), [SN74HC86N](https://www.ti.com/lit/ds/symlink/sn74hc86.pdf) |
| Flip-flop and decoder | [SN74HC74N](https://www.ti.com/lit/ds/symlink/sn74hc74.pdf), [SN74HC138N](https://www.ti.com/lit/ds/symlink/sn74hc138.pdf) |

Each entry uses the datasheet's N-package pin function table and recommended operating conditions. Studio shows physical pin numbers, signal names, and polarity bubbles on package-level symbols. ERC checks required power pins, direct DC supply range, and push-pull outputs tied to rails. It flags visibly unconnected CMOS inputs. Input threshold, output drive, and current budgets require separate validation.

The 98% target requires an independently scored connection benchmark with zero unintended connections. The existing published pilot and per-package tests provide progress evidence for that gate.

### Analog packages and supply checks

The second tranche brings the catalog to 56 entries. It covers two op amps, three comparators, a CMOS timer, and two physical pinouts of the LM35 temperature sensor. The earlier logical sensor definition still supports existing designs.

| Devices | Manufacturer source |
| --- | --- |
| LM358P, LM2904P | [TI LM358 and LM2904 datasheet](https://www.ti.com/lit/ds/symlink/lm358.pdf), sections 4 and 5.3 |
| LM393P, LM2903P | [TI LM393 and LM2903 datasheet](https://www.ti.com/lit/ds/symlink/lm393.pdf), sections 4, 5.2 and 6 |
| LM311P | [TI LM311 datasheet](https://www.ti.com/lit/ds/symlink/lm311.pdf), sections 5 and 6.3 |
| TLC555CP | [TI TLC555 datasheet](https://www.ti.com/lit/ds/symlink/tlc555.pdf), sections 4 and 5.3 |
| LM35DZ/NOPB, LM35DT/NOPB | [TI LM35 datasheet](https://www.ti.com/lit/ds/symlink/lm35.pdf), sections 5 and 6.3 |

ERC evaluates the voltage directly across both supply pins when an explicit DC source spans them. It distinguishes open-collector outputs from driven outputs and rejects direct ties to a supply or driven output. Studio marks open-collector pins and includes a threshold comparator with a resistive pull-up. The package checks leave input common-mode range, output load, and pull-up sizing for separate review.

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

## Target-based passive sizing

Local mode can solve one missing resistor in an unloaded divider, or one missing resistor or capacitor in a first-order RC low-pass. It requires the source voltage, a target and exactly one passive value. Studio identifies the calculated part and displays the nominal result. Targets outside the topology's range and requests for additional constraints require clarification.

- Divider example — *Design a voltage divider. Use a 12 V source. The upper resistor is 33 kohm. Target an output of 3.3 V.*
- Filter example — *Create a first-order RC low-pass filter. Use 5 V at the input. The shunt capacitor is 100 nF. Target a cutoff of 1 kHz.*

Verification passed 130 backend tests and 266 of 266 strict net checks across 28 authored Chromium submissions, with zero unintended contacts and label-only nets. Browser editing, import, export and mobile checks passed. The two target schematics had no unrelated crossings, but both used a long wire detour on OUT. The unchanged published pilot returned zero exact free-form interpretations out of four and routed all 15 reference nets. The model and corpus remain at the CircuitLM 0.5 checkpoint.

## High-pass requests and passive layout

Studio accepts first-order RC high-pass requests by component role. It can calculate the nominal cutoff from both values or solve for the series capacitor or shunt resistor from a cutoff target and the other component value. The high-pass estimate describes the ideal frequency response, and steady DC is blocked in that topology.

For three-component passive loops with the standard pin order, the layout aligns the filter output or divider tap on a straight segment. Across five existing Chromium cases, routed wire length per diagram fell from 1,470 to 790 SVG units, with zero crossings and all nets continuous.

Verification passed 134 backend tests, 269 of 269 strict net checks across 29 authored Chromium submissions, and the Studio smoke test. The unmodified published pilot returned four clarifications and verified 15 of 15 routed reference nets. The classifier weights and corpus remain at CircuitLM 0.5.

## Open acceptance work

The authored suite includes reviewed prompts and a small set of unfamiliar pin-explicit designs. Effects such as component substitutions, ambitious functional requirements, real operation, and arbitrary pinout coverage need separate verification. The 98% target requires a frozen, diverse external holdout and independent scoring. Native schematic ERC and simulation have yet to run. The ADC still has crossings and packed text near the interfaces, and many devices remain functional blocks.

Continue by grading out-of-corpus prompts and source-backed netlists separately, improving label-to-wire clearance and wire lengths, and adding package-specific symbols. Record reference provenance and failed cases. For deployment, use only Preview on the existing AnEmpire `circuit-api` project, verify the exact commit and test actual Studio requests.

## Preview test prompts

- ADC long prompt is `ADC_PROMPT` in [image_reference.py](app/image_reference.py). Expected 11 components, 19 continuous nets.
- First-order filter: *Use a 5 V DC source named V1, a 1 kohm resistor named R1, and a 100 nF capacitor named C1. Connect V1 positive to R1 pin 1 on net INPUT. Connect R1 pin 2 to C1 pin 1 on net OUT. Connect C1 pin 2 to V1 negative on net RETURN.*
