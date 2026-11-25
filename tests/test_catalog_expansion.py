from app.catalog import CATALOG
from app.design import check_design
from app.design_examples import mega_ldr
from app.multi_render import render_design
import xml.etree.ElementTree as ET

def test_mega_headers():
    pins=CATALOG['arduino_mega']['pins']
    assert all(f'D{i}' in pins for i in range(54))
    assert all(f'A{i}' in pins for i in range(16))

def test_mega_ldr():
    design=mega_ldr()
    checks=check_design(design)
    assert not checks['errors']
    svg,_,_=render_design(design,checks)
    root=ET.fromstring(svg)
    assert {p.attrib['data-pin']:p.attrib['data-net'] for p in root.iter() if 'data-pin' in p.attrib} == {p:n.name for n in design.nets for p in n.pins}

def test_verified_package_pin_labels():
    hc = CATALOG['sn74hc14n']
    assert hc['pin_labels'] == dict(zip(map(str,range(1,15)),
        ('1A','1Y','2A','2Y','3A','3Y','GND','4Y','4A','5Y','5A','6Y','6A','VCC')))
    assert [pin for pin,role in hc['pins'].items() if role=='output']==['2','4','6','8','10','12']
    op = CATALOG['lm358n']
    assert op['pin_labels'] == dict(zip(map(str,range(1,9)),
        ('OUT1','IN1-','IN1+','V-','IN2+','IN2-','OUT2','V+')))
    assert op['pins']['4']=='passive'  # V- may be a negative rail.
    assert op['required']==['4','8']
