"""Audit the emitted SVG for seeded variations of Studio example placements."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
from random import Random
from xml.etree import ElementTree

from app.design import Position, check_design
from app.design_examples import EXAMPLES
from app.multi_render import layout
from app.route_repair import render_repaired
from scripts.routing_measurement import measure

EXAMPLE_IDS = ('nand_gate', 'comparator', 'rc_ladder', 'bridge_rectifier',
               'schmitt_inverter', 'controller_lcd', 'mega_ldr', 'mega_ldr_servo')
CONTACT_ISSUES = {'foreign terminal', 'ambiguous crossing or overlap'}


def snapshot(svg):
    data = {name: [] for name in ('segments', 'pins', 'dots', 'bodies')}
    for node in ElementTree.fromstring(svg).iter():
        attrs = node.attrib
        if 'data-route-net' in attrs:
            net = attrs['data-route-net']
            commands = iter(attrs['d'].split())
            point = None
            for command in commands:
                coordinate = float(next(commands))
                if command == 'M':
                    point = (coordinate, float(next(commands)))
                    continue
                if command not in {'H', 'V'} or point is None:
                    raise ValueError(f'Unexpected route path command {command}')
                x, y = point
                point = (coordinate, y) if command == 'H' else (x, coordinate)
                data['segments'].append((net, x, y, *point))
        elif 'data-pin' in attrs:
            data['pins'].append((attrs['data-net'], attrs['data-pin'],
                                 float(attrs['cx']), float(attrs['cy'])))
        elif 'data-junction-net' in attrs:
            data['dots'].append((attrs['data-junction-net'], float(attrs['cx']), float(attrs['cy'])))
        elif 'data-width' in attrs:
            data['bodies'].append(tuple(float(attrs[f'data-{field}']) for field in ('x', 'y', 'width', 'height')))
    return data


def evaluate(case):
    seed, index = case
    name = EXAMPLE_IDS[index % len(EXAMPLE_IDS)]
    random = Random(f'{seed}:{index}')
    design = EXAMPLES[name]()
    boxes, _ = layout(design)
    for component in design.components:
        x, y, _, _ = boxes[component.ref]
        component.position = Position(x=max(170, x+random.randint(-18, 18)),
                                      y=max(110, y+random.randint(-18, 18)))
    validation = check_design(design)
    svg, _, _, _ = render_repaired(design, validation)
    expected = {net.name: set(net.pins) for net in design.nets}
    result = measure(snapshot(svg), expected)
    failures = Counter(reason for reasons in result['strict_failures'].values() for reason in reasons)
    contacts = any(reason in CONTACT_ISSUES for reason in failures)
    return name, len(expected), result['strict_passed'], contacts, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=int, default=5000)
    parser.add_argument('--seed', type=int, default=20261126)
    parser.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.cases < 1 or args.jobs < 1:
        parser.error('--cases and --jobs must be positive')

    totals = {name: Counter() for name in EXAMPLE_IDS}
    failures = Counter()
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        cases = ((args.seed, index) for index in range(args.cases))
        for name, expected, passed, contacts, reasons in pool.map(evaluate, cases, chunksize=8):
            totals[name].update(cases=1, expected_nets=expected, passed_nets=passed,
                                cases_with_unintended_contacts=int(contacts))
            failures.update(reasons)

    aggregate = sum(totals.values(), Counter())
    report = {
        'seed': args.seed,
        'scope': 'Seeded placement variations of authored Studio examples',
        'total': dict(aggregate),
        'net_accuracy': aggregate['passed_nets'] / aggregate['expected_nets'],
        'failure_reasons': dict(failures),
        'examples': {name: dict(counts) for name, counts in totals.items() if counts},
    }
    formatted = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(formatted+'\n')
    print(formatted)


if __name__ == '__main__':
    main()
