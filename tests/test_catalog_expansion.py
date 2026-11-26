from app.catalog import CATALOG
from app.design import check_design
from app.design_examples import mega_ldr, nand_gate
from app.multi_render import render_design
import xml.etree.ElementTree as ET
import pytest

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


@pytest.mark.parametrize('part_id,pins,outputs,active_low', [
    ('sn74hc00n', '1A 1B 1Y 2A 2B 2Y GND 3Y 3A 3B 4Y 4A 4B VCC', '3 6 8 11', '3 6 8 11'),
    ('sn74hc02n', '1Y 1A 1B 2Y 2A 2B GND 3A 3B 3Y 4A 4B 4Y VCC', '1 4 10 13', '1 4 10 13'),
    ('sn74hc04n', '1A 1Y 2A 2Y 3A 3Y GND 4Y 4A 5Y 5A 6Y 6A VCC', '2 4 6 8 10 12', '2 4 6 8 10 12'),
    ('sn74hc08n', '1A 1B 1Y 2A 2B 2Y GND 3Y 3A 3B 4Y 4A 4B VCC', '3 6 8 11', ''),
    ('sn74hc32n', '1A 1B 1Y 2A 2B 2Y GND 3Y 3A 3B 4Y 4A 4B VCC', '3 6 8 11', ''),
    ('sn74hc86n', '1A 1B 1Y 2A 2B 2Y GND 3Y 3A 3B 4Y 4A 4B VCC', '3 6 8 11', ''),
    ('sn74hc74n', '1CLR 1D 1CLK 1PRE 1Q 1Q_N GND 2Q_N 2Q 2PRE 2CLK 2D 2CLR VCC', '5 6 8 9', '1 4 6 8 10 13'),
    ('sn74hc138n', 'A B C G2A G2B G1 Y7 GND Y6 Y5 Y4 Y3 Y2 Y1 Y0 VCC',
     '7 9 10 11 12 13 14 15', '4 5 7 9 10 11 12 13 14 15'),
])
def test_ti_hc_package_pinouts(part_id, pins, outputs, active_low):
    part = CATALOG[part_id]
    labels = pins.split()
    assert part['pin_labels'] == dict(zip(map(str, range(1, len(labels)+1)), labels))
    assert part['required'] == [str(labels.index('GND')+1), str(len(labels))]
    assert [pin for pin, role in part['pins'].items() if role == 'output'] == outputs.split()
    assert part['active_low'] == active_low.split()
    assert part['supply_range'] == (2.0, 6.0)
    assert part['source'].endswith(part_id[:-1]+'.pdf')


def test_nand_example_erc_and_inversion_marks():
    design = nand_gate()
    checks = check_design(design)
    assert not checks['errors']
    assert not checks['warnings']
    svg, _, _ = render_design(design, checks)
    root = ET.fromstring(svg)
    assert {node.get('data-active-low') for node in root.iter() if node.get('data-active-low')} == {
        'U1.3', 'U1.6', 'U1.8', 'U1.11',
    }


def test_nand_erc_reports_floating_inputs_output_on_rail_and_overvoltage():
    design = nand_gate()
    next(c for c in design.components if c.ref=='V1').value = '9 V'
    by_net = {net.name: net for net in design.nets}
    by_net['GND'].pins.remove('U1.4')
    by_net['GND'].pins.append('U1.3')
    design.nets.remove(by_net['OUTPUT'])
    checks = check_design(design)
    assert {error['code'] for error in checks['errors']} == {'logic_output_on_rail', 'voltage_mismatch'}
    floating = next(w for w in checks['warnings'] if w['code']=='floating_cmos_input')
    assert floating['target'] == 'U1'
    assert '4 (2A)' in floating['message']
    assert '6 (2Y)' not in floating['message']
