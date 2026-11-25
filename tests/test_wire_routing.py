import xml.etree.ElementTree as ET
from app.design import Design, check_design
from app.multi_render import render_design
from app.route_repair import render_repaired
from app.design_examples import led_bank, mega_ldr_servo, controller_lcd

def test_three_component_series_routes():
    for i in range(30):
        d=Design(title='LED circuit',components=[dict(ref='V1',part='dc_source',value='5 V'),dict(ref='R1',part='resistor',value=f'{330+i} ohm'),dict(ref='D1',part='led',value='Red LED')],nets=[dict(name='VCC',pins=['V1.+','R1.1']),dict(name='LED',pins=['R1.2','D1.A']),dict(name='GND',pins=['D1.K','V1.-'])])
        v=check_design(d)
        assert not v['errors']
        svg,_,_,audit=render_repaired(d,v)
        assert audit['passed']
        root=ET.fromstring(svg)
        assert {p.attrib['data-route-net'] for p in root.iter() if 'data-route-net' in p.attrib}=={'VCC','LED','GND'}
        assert {p.attrib['data-pin']:p.attrib['data-net'] for p in root.iter() if 'data-pin' in p.attrib}=={p:n.name for n in d.nets for p in n.pins}
        assert svg==render_repaired(d,v)[0]

def test_complex_routes_preserve_net_ownership():
    for d in [led_bank(4),mega_ldr_servo(),controller_lcd()]:
        v=check_design(d)
        assert not v['errors']
        svg,_,_=render_design(d,v)
        root=ET.fromstring(svg)
        expected={p:n.name for n in d.nets for p in n.pins}
        assert {p.attrib['data-pin']:p.attrib['data-net'] for p in root.iter() if 'data-pin' in p.attrib}==expected
        routed={p.attrib['data-route-net'] for p in root.iter() if 'data-route-net' in p.attrib}
        assert routed
        assert {p.attrib['data-junction-net'] for p in root.iter() if 'data-junction-net' in p.attrib}<=routed


def test_live_contract_three_component_prompt():
    from fastapi.testclient import TestClient
    from app.main import app
    response=TestClient(app).post('/v2/draft',json={'prompt':'5v led with 330 ohm resistor','parser':'builtin'})
    assert response.status_code==200
    result=response.json()
    assert len(result['design']['components'])==3
    assert not result['validation']['errors']
    assert len(result['routed_nets'])==3
    assert result['unrouted_nets']==[]
