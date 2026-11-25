# Circuit AI project status

Phase 2 is active on `phase2-independent-model`. Production stays on `main` and requires separate approval.

## Current development checkpoint

- CircuitLM 0.4 independently trained on 314 authored descriptions for ten reviewed intent categories and one unsupported category. The trainer, corpus and model artifact are versioned together.
- The catalog contains 39 definitions. Ten named reference topologies are available in `/v2/examples`. The single-LED and sized LED-bank shortcuts are additional entry points.
- Studio can also generate a circuit from a complete pin-level prose request. `app/constraint_parser.py` checks every clause against the catalog and passes the netlist to the existing structural and electrical checks. Component choices or connections that are missing or expressed as desired behavior require clarification.
- New package definitions use TI's [NE555P](https://www.ti.com/lit/ds/symlink/ne555.pdf) and [LM324N](https://www.ti.com/lit/ds/symlink/lm324.pdf) datasheets. The timer topology follows TI Figure 6-5 and uses chosen component values. The timing network sits to the left of the device and the output connector to the right. The standalone SVG still has eight undotted crossings and generic IC blocks.
- RouteRepair compares the alternate grid order when the first complete route contains crossings. The AT89C51 display stayed at 16 continuous nets and dropped from 29 crossings to 27.

## Verification

- Local backend suite passed 102 tests. Chromium passed 229 of 229 net checks on 21 authored submissions. Browser editing, dragging, exports, import and mobile smoke checks passed.
- In the new browser cases, an unfamiliar two-output RC topology passed four exact net checks and the NE555P passed six. The pin-level parser rejects unknown parts, unsupported constraints, invalid units, conflicting net assignments, and unknown terminals.
- The benchmark fixtures and geometry checker are separate from RouteGuard. The suite is developer-authored, and evaluation across diverse externally prepared circuits remains open. The 98% acceptance target, native KiCad/Proteus ERC, and circuit simulation have yet to be established.

## Resume here

Use the latest commit and completed CI for the development branch as the source of truth. Check the exact SHA in the Vercel Preview environment before marking a release deployed. Use the pre-existing `an-empire/circuit-api` project. Production and `main` require explicit approval.

Next, expand pin-level fixtures across held-out circuit families, measure crowded labels and wire length, and turn ambiguous prompt requirements into structured clarification requests. Persist the exact metrics and review the rendered images at each checkpoint.

```text
Title: Twin RC outputs.
Use a 5 V DC source named V1, a 4.7 kΩ resistor named R4, and a 10 kohm resistor named R5.
Use a 100 nF capacitor named C4 and a 220 nF capacitor named C5.
Connect V1 positive, R4.1 and R5 pin 1 on net POWER.
Connect R4 pin 2 to C4 pin 1 on net FAST.
Connect R5 pin 2 to C5 pin 1 on net SLOW.
Connect V1 negative, C4.2, and C5.2 on net RETURN.
```

Select **CircuitLM · reviewed requests and pin-level prose** in Studio for this example.
