# CircuitLM schematic symbols

CircuitLM uses the local symbol index to resolve a part number or a qualified
KiCad name such as `Sensor:BME280`. An ambiguous part name requires a qualified
name. In a circuit prompt, use a physical pin number when a device repeats a
pin label. A symbol lookup can also be requested without a netlist.

## Source and license

The registry adapts 159 schematic libraries from the KiCad 9.0 series by the
KiCad community. The source filenames and exact SHA-256 fingerprints are in
`app/symbol_data/registry.json.gz`. The derived data is distributed under
CC BY-SA 4.0 with the KiCad library exception. See
[the included license and attribution](../app/symbol_data/LICENSE.txt) and
[the KiCad licensing terms](https://www.kicad.org/libraries/license/).

To rebuild the registry and its vector data with a matching KiCad library
snapshot, run `python training/import_symbols.py /usr/share/kicad/symbols`.

The generated snapshot contains 10,150 named entries, 3,728 distinct symbol
definitions including terminal metadata, and 1,963 distinct vector artworks.
Orderable variants may share the same artwork. The importer selects
single-unit default-style parts with supported primitives and distinct visible
orthogonal pin locations. Symbols with unsupported geometry, stacked or hidden
pins, and multi-unit parts are excluded. Each part keeps the source reference
prefix, pin number and label. The imported definitions are intended for
schematic drafting. Use the manufacturer data for verified package pinouts,
values, electrical ratings and application circuits.

The existing intent classifier handles supported circuit descriptions.
Exact symbol retrieval gives the editor a larger drawing vocabulary.
For a new topology, pin-explicit prompts use this vocabulary without inventing
wires. See the long-prompt regressions in `tests/test_symbol_library.py`.
