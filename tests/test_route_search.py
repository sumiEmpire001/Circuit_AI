from app.route_search import find_path,route_grid
from app.design_examples import rc_ladder,led_bank
from app.design import check_design
from app.route_guard import audit_routes
from app.route_repair import route_names

def test_astar_detours_around_blocked_nodes():
    def neighbors(p):
        x,y=p
        return [(a,b) for a,b in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)] if 0<=a<=4 and 0<=b<=4]
    blocked={(2,1),(2,2),(2,3)}
    path=find_path((0,2),{(4,2)},neighbors,blocked)
    assert path[0]==(0,2) and path[-1]==(4,2)
    assert len(path)==9 and not set(path)&blocked
    assert find_path((0,2),{(4,2)},neighbors,{(2,y) for y in range(5)}) is None

def test_compact_led_route():
    d=led_bank(1)
    svg,_,_=route_grid(d,check_design(d))
    assert route_names(svg)=={n.name for n in d.nets}
    assert audit_routes(svg)['passed']

def test_rc_grid_no_cross_net_contacts():
    d=rc_ladder()
    svg,_,_=route_grid(d,check_design(d))
    assert route_names(svg)
    assert audit_routes(svg)['passed']
