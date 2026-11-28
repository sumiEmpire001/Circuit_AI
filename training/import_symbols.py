"""Build the CircuitLM symbol registry from the KiCad 9 schematic libraries."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')
PIN_ID = re.compile(r'[A-Z0-9_+\-]{1,24}')
REFERENCE = re.compile(r'[A-Z_][A-Z0-9_+\-]{0,12}')
SCALE = 9
ROLES = dict(input='input', output='output', bidirectional='bidirectional',
             tri_state='output', passive='passive', power_in='power_in', power_out='power_out',
             open_collector='passive', open_emitter='passive', free='passive',
             unspecified='passive', no_connect='passive')


def tree(source):
    frames = [[]]
    for match in TOKEN.finditer(source):
        token = match[0]
        if token == '(':
            node = []
            frames[-1].append(node)
            frames.append(node)
        elif token == ')':
            frames.pop()
        else:
            frames[-1].append(json.loads(token) if token.startswith('"') else token)
    return frames[0][0]


def children(node, tag):
    return (item for item in node if isinstance(item, list) and item[0] == tag)


def get(node, tag, default=None):
    return next(children(node, tag), default)


def geometry(units):
    """Normalize the original symbol body and pin geometry into SVG coordinates."""
    def xy(position):
        x, y = map(float, position[1:3])
        return round(x*SCALE), round(-y*SCALE)

    shapes, bounds = [], []
    terminals = {}
    for unit in units:
        for row in unit[2:]:
            if not isinstance(row, list):
                continue
            kind = row[0]
            if kind == 'pin':
                if row[1] not in ROLES or any(i == 'hide' or i == ['hide', 'yes'] for i in row[3:]):
                    return
                number = get(row, 'number')[1]
                if number in terminals or not PIN_ID.fullmatch(number):
                    return
                at = get(row, 'at')
                angle = int(at[3])
                if angle not in (0, 90, 180, 270):
                    return
                end = xy(at)
                length = round(float(get(row, 'length')[1])*SCALE)
                terminals[number] = [*end, length, angle, row[2], get(row, 'name')[1], row[1]]
            elif kind in {'polyline', 'bezier', 'arc', 'rectangle', 'circle', 'text'}:
                fill = get(row, 'fill')
                filled = '' if fill is None else fill[1][1]
                if kind in {'polyline', 'bezier'}:
                    points = [xy(p) for p in get(row, 'pts')[1:]]
                elif kind == 'circle':
                    x, y = xy(get(row, 'center'))
                    r = round(float(get(row, 'radius')[1])*SCALE)
                    points = [(x-r,y-r), (x+r,y+r)]
                elif kind == 'text':
                    at = get(row, 'at')
                    if not at or int(at[3]) % 180:
                        return
                    points = [xy(at)]
                    filled = row[1]
                else:
                    points = [xy(get(row, k)) for k in (('start','mid','end') if kind=='arc' else ('start','end'))]
                if kind == 'arc':
                    (x1,y1),(x2,y2),(x3,y3) = points
                    d = 2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
                    if not d:
                        kind = 'polyline'
                    else:
                        z1,z2,z3 = (x*x+y*y for x,y in points)
                        cx = (z1*(y2-y3)+z2*(y3-y1)+z3*(y1-y2))/d
                        cy = (z1*(x3-x2)+z2*(x1-x3)+z3*(x2-x1))/d
                        radius = math.hypot(x1-cx,y1-cy)
                        sweep = int(d>0)
                        angle = lambda x,y: math.atan2(y-cy,x-cx)
                        extent = ((angle(x3,y3)-angle(x1,y1))*(1 if sweep else -1)) % math.tau
                        for step in range(4):
                            a = step*math.pi/2
                            if ((a-angle(x1,y1))*(1 if sweep else -1)) % math.tau <= extent:
                                bounds.append((round(cx+radius*math.cos(a)),round(cy+radius*math.sin(a))))
                        points = [points[0], (round(radius), 2*int(extent>math.pi)+sweep), points[-1]]
                bounds.extend(points if kind!='arc' else (points[0],points[-1]))
                shapes.append([kind, filled, *points])
            else:
                return
    if not shapes or not 1 <= len(terminals) <= 64:
        return
    active = list(terminals.values())
    locations = {(x,y) for x,y,*_ in active}
    if len(locations)!=len(active) or any(p[4] not in {'line','inverted','clock','inverted_clock','input_low','clock_low','output_low','edge_clock_high','non_logic'} for p in active):
        return
    for angle, axis, low in ((0,0,True),(180,0,False),(270,1,True),(90,1,False)):
        edges = {p[axis] for p in active if p[3]==angle}
        if len(edges)>1:
            return
        if edges:
            edge = next(iter(edges))
            body_edge = (min if low else max)(p[axis] for p in bounds)
            if (body_edge-edge)*(1 if low else -1) < -2:
                return
    bounds.extend(locations)
    x0,y0 = (min(p[i] for p in bounds)-16 for i in (0,1))
    w,h = (max(p[i] for p in bounds)-origin+16 for i,origin in enumerate((x0,y0)))
    if w>480 or h>830:
        return
    for p in active:
        p[0] -= x0
        p[1] -= y0
    for s in shapes:
        for i,p in enumerate(s[2:],2):
            if s[0]=='arc' and i==3:
                continue
            s[i] = [p[0]-x0,p[1]-y0]
    return {'size':[w,h], 'shapes':shapes, 'terminals':terminals}


def build(source):
    registry, drawings, checksum = {}, {}, {}
    for file in sorted(source.glob('*.kicad_sym')):
        raw = file.read_bytes()
        if file.stem.endswith('_IEEE') or file.stem in {'power','Graphic','Mechanical','Simulation_SPICE'}:
            continue
        symbols = {node[1]:node for node in children(tree(raw.decode()),'symbol')}
        prepared = {}
        for name, node in symbols.items():
            parent = get(node,'extends')
            parent_name = parent[1] if parent else name
            if parent_name not in prepared:
                base = symbols.get(parent_name, [])
                units = list(children(base,'symbol'))
                default = [unit for unit in units if re.search(r'_[01]_[01]$',unit[1])]
                multi = any(re.search(r'_\d+_[012]$', unit[1]) and not re.search(r'_[01]_[012]$',unit[1]) for unit in units)
                prepared[parent_name] = None if multi else geometry(default)
            data = prepared[parent_name]
            if not data:
                continue
            properties = {p[1]:p[2] for p in children(node,'property')}
            ref = properties.get('Reference','').upper()
            if not REFERENCE.fullmatch(ref) or len(name)>100:
                continue
            origin = f'{file.stem}:{name}'
            part = 'ks_'+hashlib.sha256(origin.encode()).hexdigest()[:16]
            key = hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()[:20]
            drawings[key] = data
            registry[part] = [origin,ref,properties.get('Datasheet',''),key]
            checksum[file.name] = hashlib.sha256(raw).hexdigest()
    return {'source':checksum,'entries':registry,'drawings':drawings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    args = parser.parse_args()
    result = build(args.source)
    target = ROOT/'app'/'symbol_data'
    target.mkdir(exist_ok=True)
    def write(name, payload):
        content = json.dumps(payload,separators=(',',':')).encode()
        (target/f'{name}.json.gz').write_bytes(gzip.compress(content,mtime=0))

    write('registry', {'source':result['source'],'entries':result['entries']})
    for i in range(4):
        chunk = {k:v for k,v in result['drawings'].items() if int(k[0],16)%4==i}
        write(f'drawings_{i}',chunk)
    print(f"{len(result['entries'])} symbols, {len(result['drawings'])} symbol definitions, {len(result['source'])} libraries")
