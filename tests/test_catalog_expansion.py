from app.catalog import CATALOG
from app.design import check_design
from app.design_examples import comparator, mega_ldr, nand_gate
from app.multi_render import render_design
from app.package_catalog import EXISTING_HC_VARIANTS, HCT_VARIANTS, LOGIC_FAMILIES, TI_PACKAGE_CODES
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


@pytest.mark.parametrize('part_id,pins,span,sinks', [
    ('lm358p', 'OUT1 IN1- IN1+ V- IN2+ IN2- OUT2 V+', (3, 30), ()),
    ('lm2904p', 'OUT1 IN1- IN1+ V- IN2+ IN2- OUT2 V+', (3, 26), ()),
    ('lm393p', '1OUT 1IN- 1IN+ GND 2IN+ 2IN- 2OUT VCC', (2, 30), ('1', '7')),
    ('lm2903p', '1OUT 1IN- 1IN+ GND 2IN+ 2IN- 2OUT VCC', (2, 30), ('1', '7')),
    ('lm311p', 'EMIT IN+ IN- VCC- BAL BAL_STRB COL VCC+', (3.5, 30), ('7',)),
    ('tlc555cp', 'GND TRIG OUT RESET CONT THRES DISCH VDD', (2, 15), ('7',)),
    ('lm35dz', 'VS VOUT GND', (4, 30), ()),
    ('lm35dt', 'VS GND VOUT', (4, 30), ()),
])
def test_ti_analog_package_pinouts(part_id, pins, span, sinks):
    part = CATALOG[part_id]
    assert list(part['pin_labels'].values()) == pins.split()
    assert part['supply_range'] == span
    assert part['open_collector'] == list(sinks)
    assert part['supply_return'] in part['required']


def test_comparator_example_has_valid_supply_and_pullup():
    design = comparator()
    checks = check_design(design)
    assert not checks['errors']
    assert not checks['warnings']


def test_open_collector_net_accepts_multiple_sinks_and_rejects_driven_output():
    design = comparator()
    output = next(n for n in design.nets if n.name == 'OUTPUT')
    output.pins.append('U1.7')
    assert not check_design(design)['errors']
    supply = next(n for n in design.nets if n.name == 'VCC')
    supply.pins.extend(output.pins)
    design.nets.remove(output)
    assert 'open_collector_conflict' in {error['code'] for error in check_design(design)['errors']}


@pytest.mark.parametrize('volts,reversed_supply,code', [
    ('1.5 V', False, 'voltage_mismatch'),
    ('5 V', True, 'supply_polarity'),
])
def test_comparator_supply_checks_use_both_pins(volts, reversed_supply, code):
    design = comparator()
    next(c for c in design.components if c.ref == 'V1').value = volts
    if reversed_supply:
        positive = next(n for n in design.nets if n.name == 'VCC')
        negative = next(n for n in design.nets if n.name == 'RETURN')
        positive.pins.remove('U1.8')
        negative.pins.remove('U1.4')
        positive.pins.append('U1.4')
        negative.pins.append('U1.8')
    assert code in {error['code'] for error in check_design(design)['errors']}


LOGIC_ORDERABLES = {
    **{family: details[-1] for family, details in LOGIC_FAMILIES.items()},
    **EXISTING_HC_VARIANTS,
    **HCT_VARIANTS,
}


@pytest.mark.parametrize('family,suffix', [
    (family, suffix) for family, codes in LOGIC_ORDERABLES.items() for suffix in codes.split()
])
def test_ti_logic_orderables_map_to_one_physical_outline(family, suffix):
    model = family + suffix.lower()
    spec = CATALOG[model]
    code, outline = TI_PACKAGE_CODES[suffix]
    assert spec['mpn'] == model.upper()
    assert spec['package'] == f'{outline}-{len(spec["pins"])} ({code})'
    assert spec['source'].endswith(f'/{family}.pdf')
    assert set(spec['pin_labels']) == set(spec['pins'])
    assert set(spec['active_low']) <= set(spec['pins'])
    assert set(spec['no_connect']).isdisjoint(spec['required'])
    assert spec['supply_range'] == ((4.5, 5.5) if family.startswith('sn74hct') else (2.0, 6.0))


def test_ti_hct_supply_limits_and_nc_pin_checks():
    design = nand_gate()
    u1 = next(component for component in design.components if component.ref == 'U1')
    source = next(component for component in design.components if component.ref == 'V1')
    u1.part = 'sn74hct00dr'
    source.value = '3.3 V'
    assert {error['code'] for error in check_design(design)['errors']} == {'voltage_mismatch'}
    source.value = '5 V'
    u1.part = 'sn74hc20pwr'
    checks = check_design(design)
    nc_errors = [issue['message'] for issue in checks['errors'] if issue['code']=='no_connect_pin']
    assert nc_errors == ['U1.3 is marked NC for this package and must remain open']


def test_ti_shift_register_control_and_output_polarity():
    spec = CATALOG['sn74hc165dbr']
    assert spec['pin_labels']['1'] == 'SH_LD'
    assert spec['pin_labels']['7'] == 'QH_N'
    assert spec['pin_labels']['9'] == 'QH'
    assert spec['pins']['1'] == 'input'
    assert spec['pins']['7'] == spec['pins']['9'] == 'output'
    assert spec['active_low'] == ['1', '7']


@pytest.mark.parametrize('key,package,min_input', [
    ('lm1117dt_18', 'TO-252 (NDP)', 3.2),
    ('lm1117dt_25', 'TO-252 (NDP)', 3.9),
    ('lm1117dt_33', 'TO-252 (NDP)', 4.75),
    ('lm1117dt_50', 'TO-252 (NDP)', 6.5),
    ('lm1117t_25', 'TO-220 (NDE)', 3.9),
    ('lm1117t_33', 'TO-220 (NDE)', 4.75),
    ('lm1117t_50', 'TO-220 (NDE)', 6.5),
])
def test_lm1117_fixed_package_pinout(key, package, min_input):
    part = CATALOG[key]
    assert part['package'] == package
    assert part['pin_labels'] == {'1': 'GND', '2': 'VOUT', '3': 'VIN'}
    assert part['supply_range'] == (min_input, 15)
    assert part['pins']['2'] == 'power_out'


def test_lm1117_checks_output_capacitor_path_and_polarity():
    from app.multi_api import builtin_design

    design = builtin_design(
        'component V1 dc_source 5 V\ncomponent U1 lm1117t_33\n'
        'component C1 capacitor_polarized 10 uF\ncomponent J1 connector2\n'
        'net VIN V1.+ U1.3\nnet VOUT U1.2 J1.1 C1.+\nnet RETURN V1.- U1.1 J1.2 C1.-'
    )
    assert not check_design(design)['errors']
    design.nets[1].pins[-1], design.nets[2].pins[-1] = 'C1.-', 'C1.+'
    assert {item['code'] for item in check_design(design)['errors']} == {'regulator_output_capacitor'}


def test_pin_level_prompt_accepts_regulator_orderable_number():
    from app.circuitlm import draft_local

    design = draft_local(
        'Use a 5 V DC source named V1, an LM1117T-3.3/NOPB named U1, '
        'a 10 uF polarized capacitor named C1. '
        'Connect V1 positive to U1 VIN. Connect U1 VOUT to C1 +. '
        'Connect V1 negative to U1 GND and C1 -.'
    )
    assert next(component.part for component in design.components if component.ref=='U1') == 'lm1117t_33'
    assert not check_design(design)['errors']
