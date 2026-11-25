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
