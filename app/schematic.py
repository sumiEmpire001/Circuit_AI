"""Deterministic, Proteus-inspired SVG for the supported checked circuit graphs.

Drawing coordinates are intentionally fixed to keep labels and wires separate.
This exports SVG/PNG, not a native Proteus design or simulation.
"""
from html import escape


def engineering(value, unit):
    for scale, prefix in [(1e6, 'M'), (1e3, 'k'), (1, ''), (1e-3, 'm'),
                          (1e-6, 'µ'), (1e-9, 'n'), (1e-12, 'p')]:
        if abs(value) >= scale:
            return f'{value / scale:g} {prefix}{unit}'
    return f'{value:g} {unit}'


def render_proteus(components):
    source, resistor, load = components
    # This layout supports exactly the API's three checked templates.
    expected = [{'+': 'IN', '-': '0'}, {'1': 'IN', '2': 'OUT'},
                {'A': 'OUT', 'K': '0'} if load['type'] == 'LED' else {'1': 'OUT', '2': '0'}]
    if ([c['pins'] for c in components] != expected
            or source['type'] != 'V' or resistor['type'] != 'R'
            or load['type'] not in ('R', 'C', 'LED')):
        raise ValueError('Unsupported graph for schematic layout')
    parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500" role="img" aria-labelledby="title desc">
<title id="title">Circuit AI electrical schematic</title>
<desc id="desc">DC source V1 feeds R1 and the output node. The load connects OUT to ground.</desc>
<defs>
<pattern id="minor" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 H 0 V 10" fill="none" stroke="#c9c9b3" stroke-width="0.45"/></pattern>
<pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse"><rect width="50" height="50" fill="url(#minor)"/><path d="M 50 0 H 0 V 50" fill="none" stroke="#b1b39b" stroke-width="0.8"/></pattern>
</defs>
<rect width="800" height="500" fill="#eeeedb"/><rect width="800" height="500" fill="url(#grid)"/>
<style>text{font-family:DejaVu Sans,sans-serif;fill:#343a2c;font-size:15px}.pin{font-size:11px;fill:#7b493d}.wire{stroke:#285b36;stroke-width:2;fill:none;stroke-linejoin:round}.symbol{stroke:#874d3d;stroke-width:2;fill:none}.junction{fill:#285b36}</style>''']

    def text(x, y, value, cls=''):
        parts.append(f'<text x="{x}" y="{y}" class="{cls}">{escape(str(value))}</text>')

    def path(d, cls='symbol', extra=''):
        parts.append(f'<path class="{cls}" d="{d}" {extra}/>')

    text(30, 35, 'CIRCUIT AI / ELECTRICAL SCHEMATIC')
    # Named nets: horizontal/vertical conductors never pass through symbol bodies.
    path('M 170 220 V 150 H 310', 'wire', 'data-net="IN"')
    path('M 410 150 H 520 V 240 M 520 150 H 650', 'wire', 'data-net="OUT"')
    path('M 170 280 V 360 H 520 V 300 M 520 360 V 390', 'wire', 'data-net="0"')
    parts.append('<circle class="symbol" cx="170" cy="250" r="30"/>')
    path('M 163 237 H 177 M 170 230 V 244 M 163 263 H 177')
    path('M 310 150 H 330 M 390 150 H 410')
    parts.append('<rect class="symbol" x="330" y="139" width="60" height="22"/>')
    text(330, 112, resistor['ref'])
    text(330, 132, engineering(resistor['value'], 'Ω'))
    text(312, 175, '1', 'pin'); text(401, 175, '2', 'pin')
    text(65, 242, source['ref']); text(65, 264, engineering(source['value'], 'V'))
    text(182, 214, '+', 'pin'); text(182, 298, '−', 'pin')
    text(185, 140, 'IN'); text(660, 155, 'OUT')
    if load['type'] == 'R':
        path('M 520 240 V 248 M 520 292 V 300')
        parts.append('<rect class="symbol" x="509" y="248" width="22" height="44"/>')
        value = engineering(load['value'], 'Ω')
    elif load['type'] == 'C':
        path('M 520 240 V 263 M 502 263 H 538 M 502 277 H 538 M 520 277 V 300')
        value = engineering(load['value'], 'F')
    else:
        path('M 520 240 V 253 M 506 253 H 534 L 520 278 Z M 506 280 H 534 M 520 280 V 300')
        # Outward arrows distinguish the LED from an ordinary diode.
        path('M 540 260 L 555 245 M 549 245 H 555 V 251 M 548 274 L 563 259 M 557 259 H 563 V 265')
        value = engineering(load['value'], 'V') + ' Vf'
    text(580, 262, load['ref']); text(580, 285, value)
    pins = list(load['pins'])
    text(497, 235, pins[0], 'pin'); text(497, 318, pins[1], 'pin')
    for x, y in [(520, 150), (520, 360)]:
        parts.append(f'<circle class="junction" cx="{x}" cy="{y}" r="4"/>')
    parts.append('<circle cx="650" cy="150" r="4" stroke="#285b36" fill="#eeeedb" stroke-width="2"/>')
    path('M 506 390 H 534 M 511 396 H 529 M 516 402 H 524', 'wire')
    text(545, 397, 'GND (0)')
    text(30, 455, 'Nominal component values • Template connectivity checked')
    text(30, 479, 'Proteus-inspired drawing • Not simulated • Not a native Proteus file')
    parts.append('</svg>')
    return '\n'.join(parts)
