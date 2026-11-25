# User-supplied reference schematics

Nine images reviewed in upload order. Image pixels are not model-training inputs. Only independently transcribed topology and textual descriptions are used; no reference image files are redistributed.

| Image | Extracted pattern | Status |
|---|---|---|
| 1 | 1N4007 bridge: AC1 D1.K/D2.A; AC2 D3.K/D4.A; positive D2.K/D4.K; negative D1.A/D3.A; C1 100 nF across output | Implemented as bridge_rectifier |
| 2 | Existing LED diagram: large empty spaces, lengthy bus detours, labels adjacent to wires | Compact placement rule added |
| 3 | Uno, LCD, ULN2003A, relays, lamps, virtual terminal | Functional block placement target; ratings and full pinout need verification |
| 4 | PIC, LCD, switch and resistor inputs, signal bus | Grouped signal routing target; image too low-resolution for complete netlist |
| 5 | MPX4115, thermistor divider, PIC16F876, LCD | Analog input stages and parallel data; verify part variant and pinout |
| 6 | Pull-up button inputs, named signals, LCD, ENC28J60 | Explicit labels can be useful in dense diagrams; not all wiring is visible |
| 7 | LM324 stages, BC548, potentiometers, feedback and supply rails | Feedback topology and local junction targets; not a verified design |
| 8 | AT89C51, LCD, oscillator and named nets | Parallel bus and grouped oscillator target; cropped image |
| 9 | AT89C51, ADC0804, LM35, L293D, LCD and two motors | Functional partitioning target; verify all connections before implementation |

Acceptance: exact terminal membership; distinct nets; correct symbol polarity; no cross-net contacts; no wire/body intersections; connected route geometry; junction dots only at branches; readable labels; compact placement; no fake simulation readings. Report label-only nets separately. Validate visual quality on screenshots, not only API success. No claim that any reference is hardware-verified.
