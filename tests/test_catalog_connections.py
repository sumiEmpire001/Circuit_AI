"""Exercise every catalog terminal through the netlist and SVG pipeline."""
from xml.etree import ElementTree

import pytest

from app.catalog import CATALOG
from app.design import Design, check_design
from app.multi_render import render_design
from app.route_repair import render_repaired
from scripts.routing_measurement import measure
from scripts.routing_stress import snapshot


@pytest.mark.parametrize('part_id', sorted(CATALOG))
def test_catalog_terminals_round_trip_and_route(part_id):
    spec = CATALOG[part_id]
    pins = set(spec['pins'])
    if 'pin_labels' in spec:
        assert set(spec['pin_labels']) == pins
    for field in ('required', 'active_low', 'no_connect', 'open_collector', 'open_drain'):
        assert set(spec.get(field, ())) <= pins
    if 'supply_return' in spec:
        assert spec['supply_return'] in spec['required']
        assert 0 < spec['supply_range'][0] <= spec['supply_range'][1]
    if 'mpn' in spec:
        assert spec['manufacturer'] and spec['package'] and spec['source'].startswith('https://')
    reserved = set(spec.get('no_connect', ()))
    assert reserved.isdisjoint(spec['required'])

    # Isolate each terminal on a distinct probe net. This exercises pin identity
    # and SVG membership without treating a probe as a functional circuit.
    terminals = [pin for pin in spec['pins'] if pin not in reserved]
    probes = {}
    components = [{'ref': 'DUT', 'part': part_id}]
    nets = []
    for first in range(0, len(terminals), 48):
        group = terminals[first:first+48]
        model, ref = f'probe_{first}', f'P{first}'
        probes[model] = {'name': 'Probe terminals', 'pins': {str(i): 'passive' for i in range(len(group))}}
        components.append({'ref': ref, 'part': model})
        for offset, pin in enumerate(group):
            nets.append({'name': f'N{first+offset}', 'pins': [f'DUT.{pin}', f'{ref}.{offset}']})
    design = Design(components=components, nets=nets, custom_parts=probes)
    svg, _, _ = render_design(design, check_design(design), route_order=[])
    actual = {node.get('data-pin'): node.get('data-net') for node in ElementTree.fromstring(svg).iter()
              if node.get('data-pin') is not None}
    assert actual == {pin: net.name for net in design.nets for pin in net.pins}

    # Check visible wire continuity independently on one terminal per entry.
    sample = Design(
        components=[components[0], {'ref': 'J1', 'part': 'connector2'}],
        nets=[{'name': 'PROBE', 'pins': [f'DUT.{terminals[0]}', 'J1.1']}],
    )
    svg, _, _, _ = render_repaired(sample, check_design(sample))
    assert measure(snapshot(svg), {'PROBE': set(sample.nets[0].pins)})['strict_passed'] == 1


def test_hc266_distinguishes_open_drain_outputs_from_driven_outputs():
    model = CATALOG['sn74hc266n']
    assert model['pin_labels']['4'] == '2Y'
    assert model['open_drain'] == ('3', '4', '10', '11')
    design = Design(
        components=[{'ref': 'U1', 'part': 'sn74hc266n'},
                    {'ref': 'V1', 'part': 'dc_source', 'value': '5 V'},
                    {'ref': 'J1', 'part': 'connector2'}],
        nets=[{'name': 'VCC', 'pins': ['V1.+', 'U1.14']},
              {'name': 'GND', 'pins': ['V1.-', 'U1.7']},
              {'name': 'WIRED', 'pins': ['U1.3', 'U1.4', 'J1.1']}],
    )
    assert not check_design(design)['errors']
    design.nets[0].pins.extend(design.nets.pop().pins)
    assert {item['code'] for item in check_design(design)['errors']} == {'open_collector_conflict'}
