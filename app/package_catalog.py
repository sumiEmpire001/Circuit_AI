"""Reviewed physical packages. The numeric order in each pin map is significant."""

QUAD_GATE = '1A 1B 1Y 2A 2B 2Y GND 3Y 3A 3B 4Y 4A 4B VCC'
QUAD_NOR = '1Y 1A 1B 2Y 2A 2B GND 3A 3B 3Y 4A 4B 4Y VCC'
HEX_INVERTER = '1A 1Y 2A 2Y 3A 3Y GND 4Y 4A 5Y 5A 6Y 6A VCC'


def hc_package(model, function, pin_map, outputs, active_low=()):
    labels = dict(enumerate(pin_map.split(), 1))
    pins = {
        str(number): 'power_in' if label == 'VCC' else 'ground' if label == 'GND'
        else 'output' if number in outputs else 'input'
        for number, label in labels.items()
    }
    return {
        'name': f'{model} {function} (PDIP-{len(labels)})',
        'manufacturer': 'Texas Instruments',
        'mpn': model,
        'package': f'PDIP-{len(labels)} (N)',
        'symbol': 'logic_package',
        'logic_function': function,
        'input_family': 'CMOS',
        'pins': pins,
        'pin_labels': {str(number): label for number, label in labels.items()},
        'required': [pin for pin, role in pins.items() if role in {'ground', 'power_in'}],
        'active_low': [str(number) for number in active_low],
        'voltage': None,
        'supply_range': (2.0, 6.0),
        'source': f'https://www.ti.com/lit/ds/symlink/{model[:-1].lower()}.pdf',
    }


QUAD_OUTPUTS = (3, 6, 8, 11)
PACKAGE_CATALOG = {
    'sn74hc00n': hc_package('SN74HC00N', 'Quad NAND', QUAD_GATE, QUAD_OUTPUTS, QUAD_OUTPUTS),
    'sn74hc02n': hc_package('SN74HC02N', 'Quad NOR', QUAD_NOR, (1, 4, 10, 13), (1, 4, 10, 13)),
    'sn74hc04n': hc_package('SN74HC04N', 'Hex inverter', HEX_INVERTER, (2, 4, 6, 8, 10, 12), (2, 4, 6, 8, 10, 12)),
    'sn74hc08n': hc_package('SN74HC08N', 'Quad AND', QUAD_GATE, QUAD_OUTPUTS),
    'sn74hc32n': hc_package('SN74HC32N', 'Quad OR', QUAD_GATE, QUAD_OUTPUTS),
    'sn74hc86n': hc_package('SN74HC86N', 'Quad XOR', QUAD_GATE, QUAD_OUTPUTS),
    'sn74hc74n': hc_package(
        'SN74HC74N', 'Dual D flip-flop',
        '1CLR 1D 1CLK 1PRE 1Q 1Q_N GND 2Q_N 2Q 2PRE 2CLK 2D 2CLR VCC',
        (5, 6, 8, 9), (1, 4, 6, 8, 10, 13),
    ),
    'sn74hc138n': hc_package(
        'SN74HC138N', '3-to-8 decoder',
        'A B C G2A G2B G1 Y7 GND Y6 Y5 Y4 Y3 Y2 Y1 Y0 VCC',
        (7, 9, 10, 11, 12, 13, 14, 15), (4, 5, 7, 9, 10, 11, 12, 13, 14, 15),
    ),
}


def analog_package(model, function, package, datasheet, pin_map, required,
                   supply_return, supply_range, *, open_collector=(), active_low=()):
    return {
        'name': f'{model} {function}',
        'manufacturer': 'Texas Instruments',
        'mpn': model,
        'package': package,
        'symbol': 'analog_package',
        'function': function,
        'pins': {str(i): role for i, (_, role) in enumerate(pin_map, 1)},
        'pin_labels': {str(i): label for i, (label, _) in enumerate(pin_map, 1)},
        'required': list(required),
        'voltage': None,
        'supply_range': supply_range,
        'supply_return': supply_return,
        'open_collector': list(open_collector),
        'active_low': list(active_low),
        'source': f'https://www.ti.com/lit/ds/symlink/{datasheet}.pdf',
    }


PDIP8 = 'PDIP-8 (P)'
DUAL_AMPLIFIER = (
    ('OUT1', 'output'), ('IN1-', 'input'), ('IN1+', 'input'), ('V-', 'passive'),
    ('IN2+', 'input'), ('IN2-', 'input'), ('OUT2', 'output'), ('V+', 'power_in'),
)
DUAL_COMPARATOR = (
    ('1OUT', 'output'), ('1IN-', 'input'), ('1IN+', 'input'), ('GND', 'passive'),
    ('2IN+', 'input'), ('2IN-', 'input'), ('2OUT', 'output'), ('VCC', 'power_in'),
)

PACKAGE_CATALOG.update({
    'lm358p': analog_package('LM358P', 'Dual op amp', PDIP8, 'lm358',
                             DUAL_AMPLIFIER, ('4', '8'), '4', (3, 30)),
    'lm2904p': analog_package('LM2904P', 'Dual op amp', PDIP8, 'lm358',
                              DUAL_AMPLIFIER, ('4', '8'), '4', (3, 26)),
    'lm393p': analog_package('LM393P', 'Dual comparator', PDIP8, 'lm393',
                             DUAL_COMPARATOR, ('4', '8'), '4', (2, 30),
                             open_collector=('1', '7')),
    'lm2903p': analog_package('LM2903P', 'Dual comparator', PDIP8, 'lm393',
                              DUAL_COMPARATOR, ('4', '8'), '4', (2, 30),
                              open_collector=('1', '7')),
    'lm311p': analog_package(
        'LM311P', 'Comparator', PDIP8, 'lm311',
        (('EMIT', 'passive'), ('IN+', 'input'), ('IN-', 'input'), ('VCC-', 'passive'),
         ('BAL', 'input'), ('BAL_STRB', 'input'), ('COL', 'output'), ('VCC+', 'power_in')),
        ('2', '3', '4', '8'), '4', (3.5, 30), open_collector=('7',),
    ),
    'tlc555cp': analog_package(
        'TLC555CP', 'CMOS timer', PDIP8, 'tlc555',
        (('GND', 'ground'), ('TRIG', 'input'), ('OUT', 'output'), ('RESET', 'input'),
         ('CONT', 'input'), ('THRES', 'input'), ('DISCH', 'output'), ('VDD', 'power_in')),
        ('1', '2', '4', '6', '8'), '1', (2, 15), open_collector=('7',), active_low=('4',),
    ),
    'lm35dz': analog_package(
        'LM35DZ/NOPB', 'Temperature sensor', 'TO-92 (LP)', 'lm35',
        (('VS', 'power_in'), ('VOUT', 'output'), ('GND', 'ground')),
        ('1', '3'), '3', (4, 30),
    ),
    'lm35dt': analog_package(
        'LM35DT/NOPB', 'Temperature sensor', 'TO-220 (NEB)', 'lm35',
        (('VS', 'power_in'), ('GND', 'ground'), ('VOUT', 'output')),
        ('1', '2'), '2', (4, 30),
    ),
})
