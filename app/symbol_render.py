"""Draw KiCad primitives and reference terminals in the Studio SVG."""
from html import escape

FILL = {'outline':'#874d3d', 'background':'#e4e5c7'}


def svg_symbol(data, x, y):
    yield f'<g class="imported-symbol" transform="translate({x} {y})">'
    for kind, color, *points in data['shapes']:
        fill = FILL.get(color, 'none')
        attrs = f'class="symbol" style="fill:{fill}"'
        if kind == 'text':
            (a,b), = points
            yield f'<text x="{a}" y="{b}" text-anchor="middle" dominant-baseline="central">{escape(color)}</text>'
        elif kind == 'rectangle':
            (a,b),(c,d) = points
            yield f'<rect {attrs} x="{min(a,c)}" y="{min(b,d)}" width="{abs(c-a)}" height="{abs(d-b)}"/>'
        elif kind == 'circle':
            (a,b),(c,d) = points
            yield f'<circle {attrs} cx="{(a+c)/2}" cy="{(b+d)/2}" r="{abs(c-a)/2}"/>'
        elif kind == 'arc':
            (a,b),(r,flags),(c,d) = points
            yield f'<path {attrs} d="M {a} {b} A {r} {r} 0 {flags//2} {flags%2} {c} {d}"/>'
        else:
            start, *rest = points
            command = 'C' if kind=='bezier' else 'L'
            tail = ' '.join(f'{a} {b}' for a,b in rest)
            yield f'<path {attrs} d="M {start[0]} {start[1]} {command} {tail}"/>'
    yield '</g>'


def pin_glyph(shape, end, y, direction, line, parts, qualified):
    """Draw pin decorations from its connection end toward the symbol body."""
    inset = 0
    if shape in {'inverted','inverted_clock'}:
        parts.append(f'<circle class="symbol" cx="{end-4*direction}" cy="{y}" r="4" data-active-low="{qualified}"/>')
        inset = 8
    if shape in {'clock','inverted_clock','clock_low','edge_clock_high'}:
        line(f'M {end} {y-5} l {6*direction} 5 l {-6*direction} 5')
    if shape in {'input_low','clock_low','output_low'}:
        line(f'M {end} {y} l {-6*direction} -6 h {6*direction}')
    if shape=='non_logic':
        line(f'M {end-4} {y-4} l 8 8 M {end-4} {y+4} l 8 -8')
    return end-inset*direction


def svg_pin_marker(shape, body_x, body_y, angle, line, parts, qualified):
    if shape=='line':
        return 0
    if angle:
        parts.append(f'<g transform="rotate({-angle} {body_x} {body_y})">')
    end = pin_glyph(shape,body_x,body_y,1,line,parts,qualified)
    if angle:
        parts.append('</g>')
    return body_x-end
