from app.route_guard import audit_routes

def svg(a,b):
    return f'<svg><path data-route-net="A" d="{a}"/><path data-route-net="B" d="{b}"/></svg>'

def test_detect_crossing():
    assert not audit_routes(svg('M 0 10 H 20','M 10 0 V 20'))['passed']
def test_detect_endpoint_touch():
    assert not audit_routes(svg('M 0 10 H 20','M 20 10 V 20'))['passed']
def test_detect_overlap():
    assert not audit_routes(svg('M 0 10 H 20','M 5 10 H 30'))['passed']
def test_gap_is_clear():
    assert audit_routes(svg('M 0 10 H 20','M 10 0 V 6 M 10 14 V 20'))['passed']

def test_geometric_pin_continuity():
    pins='<circle data-pin="R1.1" data-net="A" cx="0" cy="10"/><circle data-pin="R2.1" data-net="A" cx="20" cy="10"/>'
    def case(path):
        return audit_routes(f'<svg>{pins}<path data-route-net="A" d="{path}"/></svg>')
    assert case('M 0 10 H 20')['continuous_nets']==['A']
    assert case('M 0 10 H 8 M 12 10 H 20')['interrupted_nets'][0]['net']=='A'
