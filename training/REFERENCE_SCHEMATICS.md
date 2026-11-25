# User-supplied reference schematics

Nine images reviewed. The table uses their original reference numbering. Image pixels are not model-training inputs. Only independently transcribed topology and textual descriptions are used; no reference image files are redistributed.

| Image | Extracted pattern | Status |
|---|---|---|
| 1 | 1N4007 bridge: AC1 D1.K/D2.A; AC2 D3.K/D4.A; positive D2.K/D4.K; negative D1.A/D3.A; C1 100 nF across output | Implemented as bridge_rectifier |
| 2 | Existing LED diagram: large empty spaces, lengthy bus detours, labels adjacent to wires | Compact placement rule added |
| 3 | Uno, LCD, ULN2003A, relays, lamps, virtual terminal | Functional block placement target; ratings and full pinout need verification |
| 4 | PIC, LCD, switch and resistor inputs, signal bus | Grouped signal routing target; image too low-resolution for complete netlist |
| 5 | MPX4115, thermistor divider, PIC16F876, LCD | Analog input stages and parallel data; verify part variant and pinout |
| 6 | Pull-up button inputs, named signals, LCD, ENC28J60 | Explicit labels can be useful in dense diagrams; not all wiring is visible |
| 7 | LM324 stages, BC548, potentiometers, feedback and supply rails | Feedback topology and local junction targets; not a verified design |
| 8 | AT89C51, LCD, oscillator and named nets | Implemented as at89c51_lcd with package pins independently checked |
| 9 | AT89C51, ADC0804, LM35, L293D, LCD and two motors | Reset RC informed the AT89C51 subsystem. ADC, sensor and motor stages remain layout references. |

Acceptance: exact terminal membership; distinct nets; correct symbol polarity; no cross-net contacts; no wire/body intersections; connected route geometry; junction dots only at branches; readable labels; compact placement; no fake simulation readings. Report label-only nets separately. Validate visual quality on screenshots, not only API success. No claim that any reference is hardware-verified.

## AT89C51 / LM016L transcription

The close-up identifies P1.0–P1.7 as LCD D0–D7, P2.1 as RS, P2.2 as EN, EA high, and two separate oscillator nets with 33 pF capacitors to ground. The complete temperature controller shows the 10 µF high-side reset capacitor and 10 kΩ pull-down. Its application-specific LCD control mapping is different and is excluded from this netlist.

The 12 MHz frequency and a contrast potentiometer are explicit design choices because the close-up does not establish a crystal frequency or a suitable adjustable contrast circuit. The two supply pins and the LCD pin map were checked against the [AT89C51 datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0265.pdf) and [Hitachi display databook](https://www.bitsavers.org/components/hitachi/_dataBooks/1987_Hitachi_Liquid_Crystal_Display_Modules.pdf). The reference tests compare the actual render against a fixture separate from RouteGuard.

The reviewed long prompt is recorded in [image_reference.py](../app/image_reference.py). The other schematics inform block placement, polarity, labels and junction conventions. Their incomplete netlists have not been included as training targets.

## Temperature acquisition subsystem

CircuitLM 0.5 adds the 8051, LM35, and ADC0804 acquisition slice from the temperature-controller reference. The ADC pin numbers, recommended supply range, and separate analog/digital grounds were checked against [TI's ADC0804-N datasheet](https://www.ti.com/lit/ds/symlink/adc0804-n.pdf). The eight data signals retain the pictured Port 2 grouping. RD, WR and INTR assignments are explicit design choices. The LM35 output faces its destination and the rendered digital signals lie in parallel tracks. The original display and actuator sections remain separate references. No simulated readings are rendered.
