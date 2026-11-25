"""Measure submitted circuits from Chromium's SVG DOM without RouteGuard."""
from collections import defaultdict
from itertools import combinations


def intersection(a, b):
    """Return the intersection bounds of two orthogonal segments, if any."""
    left, right = max(a[0], b[0]), min(a[2], b[2])
    top, bottom = max(a[1], b[1]), min(a[3], b[3])
    if left <= right and top <= bottom:
        return (left, top, right, bottom)
    return None


def interior(point, segment):
    return point not in (segment[:2], segment[2:])


def measure(snapshot, expected):
    paths = defaultdict(list)
    pins = defaultdict(dict)
    dots = defaultdict(set)
    for name, x, y, u, v in snapshot['segments']:
        if (x, y) != (u, v):
            assert x == u or y == v
            paths[name].append((min(x, u), min(y, v), max(x, u), max(y, v)))
    for name, ref, x, y in snapshot['pins']:
        assert ref not in pins[name]
        pins[name][ref] = (x, y)
    for name, x, y in snapshot['dots']:
        dots[name].add((x, y))

    issues = defaultdict(set)
    crossings = set()
    dot_locations = set().union(*dots.values())
    for name, wires in paths.items():
        for other, foreign in pins.items():
            if name != other and any(intersection(w, p+p) for w in wires for p in foreign.values()):
                issues[name].add('foreign terminal')
                issues[other].add('foreign terminal')
        for x, y, w, h in snapshot['bodies']:
            body = (x+1, y+1, x+w-1, y+h-1)
            if any(intersection(wire, body) for wire in wires):
                issues[name].add('wire through symbol body')
    for left, right in combinations(paths, 2):
        for a in paths[left]:
            for b in paths[right]:
                hit = intersection(a, b)
                if hit is None:
                    continue
                perpendicular = (a[0] == a[2]) != (b[0] == b[2])
                p = hit[:2]
                if perpendicular and interior(p, a) and interior(p, b) and p not in dot_locations:
                    crossings.add(p)
                else:
                    issues[left].add('ambiguous crossing or overlap')
                    issues[right].add('ambiguous crossing or overlap')

    for name, terminals in expected.items():
        actual = pins[name]
        if set(actual) != set(terminals):
            issues[name].add('incorrect terminal membership')
        wires = paths[name]
        if not wires:
            issues[name].add('label only')
            continue
        reached = {0}
        queue = [0]
        while queue:
            index = queue.pop()
            for candidate, wire in enumerate(wires):
                if candidate not in reached and intersection(wires[index], wire):
                    reached.add(candidate)
                    queue.append(candidate)
        if len(reached) != len(wires) or any(
            not any(intersection(wires[i], p+p) for i in reached) for p in actual.values()
        ):
            issues[name].add('interrupted wire')
        for p in {p for wire in wires for p in (wire[:2], wire[2:])} | dots[name]:
            directions = set()
            for wire in wires:
                if intersection(wire, p+p):
                    if wire[0] < p[0]: directions.add('left')
                    if wire[2] > p[0]: directions.add('right')
                    if wire[1] < p[1]: directions.add('up')
                    if wire[3] > p[1]: directions.add('down')
            if (len(directions) >= 3) != (p in dots[name]):
                issues[name].add('incorrect junction dot')

    assert set(pins) | set(paths) <= expected.keys(), 'Unexpected SVG net'
    return {
        'strict_passed': sum(not issues.get(name) for name in expected),
        'strict_failures': {name: sorted(errors) for name, errors in sorted(issues.items()) if errors},
        'undotted_crossings': len(crossings),
    }


DOM_SNAPSHOT = r"""svg => {
    const nodes = selector => Array.from(svg.querySelectorAll(selector));
    const xy = node => ['cx','cy'].map(key => Number(node.getAttribute(key)));
    const segments = [];
    for (const path of nodes('[data-route-net]')) {
        const tokens = path.getAttribute('d').trim().split(/\s+/);
        let x, y;
        for (let i = 0; i < tokens.length;) {
            const command = tokens[i++];
            const coordinate = Number(tokens[i++]);
            if (command === 'M') { x = coordinate; y = Number(tokens[i++]); continue; }
            if (command !== 'H' && command !== 'V') throw Error('Unexpected route command');
            const u = command === 'H' ? coordinate : x;
            const v = command === 'V' ? coordinate : y;
            segments.push([path.dataset.routeNet, x, y, u, v]);
            [x, y] = [u, v];
        }
    }
    return {
        segments,
        pins: nodes('[data-pin]').map(n => [n.dataset.net, n.dataset.pin, ...xy(n)]),
        dots: nodes('[data-junction-net]').map(n => [n.dataset.junctionNet, ...xy(n)]),
        bodies: nodes('.component[data-width]').map(n =>
            ['x','y','width','height'].map(key => Number(n.dataset[key]))),
    };
}"""
