from itertools import permutations
import xml.etree.ElementTree as ET
from app.design import check_design
from app.design_examples import EXAMPLES,rc_ladder
from app.route_repair import render_repaired,route_names,remove_routes
from app.route_guard import audit_routes

def test_remove_only_conflicting_route():
    s='<svg><path data-route-net="A" d="M 0 0 H 10"/><circle data-junction-net="A"/><circle data-pin="R1.1" data-net="A"/><path data-route-net="B" d="M 10 0 V 10"/></svg>'
    out=remove_routes(s,{'A'})
    assert route_names(out)=={'B'}
    assert 'data-pin="R1.1"' in out
    assert 'data-junction-net' not in out

def check(d):
    svg,_,_,audit=render_repaired(d,check_design(d))
    assert audit['passed'],audit
    assert audit_routes(svg)['passed']
    assert 1<=audit['attempts']<=4
    root=ET.fromstring(svg)
    assert {p.get('data-pin'):p.get('data-net') for p in root.iter() if p.get('data-pin')}=={p:n.name for n in d.nets for p in n.pins}
    assert route_names(svg)<={n.name for n in d.nets}

def test_reference_examples():
    for example in EXAMPLES.values(): check(example())

def test_rc_layout_permutations():
    d=rc_ladder()
    for order in permutations(d.components):
        check(d.model_copy(update={'components':list(order)}))

def test_repeated_led_branches_have_continuous_rails_after_position_round_trip():
    from app.design import Design
    from app.design_examples import led_bank

    d = led_bank(32)
    svg, boxes, _, audit = render_repaired(d, check_design(d))
    assert len(audit['continuous_nets'])==34
    assert audit['undotted_crossings']==0
    exported = d.model_dump()
    for component in exported['components']:
        x, y, _, _ = boxes[component['ref']]
        component['position'] = {'x': x, 'y': y}
    restored = Design.model_validate(exported)
    assert render_repaired(restored, check_design(restored))[3]==audit
