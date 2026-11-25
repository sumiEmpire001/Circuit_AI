import xml.etree.ElementTree as ET
from fastapi.testclient import TestClient
from app.main import app
from app.design_examples import controller_lcd, mega_ldr_servo
from app.design import check_design
from app.multi_render import render_design

def test_lcd_reference_connections():
    expected={'RS':{'U1.D12','LCD1.4'},'ENABLE':{'U1.D11','LCD1.6'},'DATA4':{'U1.D5','LCD1.11'},'DATA5':{'U1.D4','LCD1.12'},'DATA6':{'U1.D3','LCD1.13'},'DATA7':{'U1.D2','LCD1.14'},'CONTRAST':{'RV1.W','LCD1.3'},'BACKLIGHT':{'R1.2','LCD1.15'},'VCC':{'V1.+','U1.5V','LCD1.2','RV1.1','R1.1'},'GND':{'V1.-','U1.GND','LCD1.1','LCD1.5','LCD1.16','RV1.2'}}
    d=controller_lcd()
    assert {n.name:set(n.pins) for n in d.nets}==expected
    svg,_,_=render_design(d,check_design(d))
    assert 'HD44780 parallel' in svg
    root=ET.fromstring(svg)
    assert {p.attrib['data-pin']:p.attrib['data-net'] for p in root.iter() if 'data-pin' in p.attrib}=={p:n for n,ps in expected.items() for p in ps}

def test_servo_separate_supply_and_signal():
    r=TestClient(app).post('/v2/draft',json={'prompt':'mega_ldr_servo'})
    assert r.status_code==200
    d=r.json()
    assert not d['validation']['errors']
    expected={'VCC':{'V1.+','U1.5V','LDR1.1'},'SENSE':{'LDR1.2','R1.1','U1.A0'},'GND':{'V1.-','U1.GND','R1.2','V2.-','M1.GND'},'SERVO_PWR':{'V2.+','M1.VCC'},'SERVO_SIG':{'U1.D9','M1.SIG'}}
    assert {n['name']:set(n['pins']) for n in d['design']['nets']}==expected
    root=ET.fromstring(d['image']['svg'])
    assert {p.attrib['data-pin']:p.attrib['data-net'] for p in root.iter() if 'data-pin' in p.attrib}=={p:n for n,ps in expected.items() for p in ps}
