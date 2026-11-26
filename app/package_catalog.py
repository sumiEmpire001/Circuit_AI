"""Reviewed physical packages. The numeric order in each pin map is significant."""

QUAD_GATE = '1A 1B 1Y 2A 2B 2Y GND 3Y 3A 3B 4Y 4A 4B VCC'
QUAD_NOR = '1Y 1A 1B 2Y 2A 2B GND 3A 3B 3Y 4A 4B 4Y VCC'
HEX_INVERTER = '1A 1Y 2A 2Y 3A 3Y GND 4Y 4A 5Y 5A 6Y 6A VCC'
TRIPLE_GATE = '1A 1B 2A 2B 2C 2Y GND 3Y 3A 3B 3C 1Y 1C VCC'
DUAL_GATE = '1A 1B NC 1C 1D 1Y GND 2Y 2A 2B NC 2C 2D VCC'
BINARY_COUNTER = 'CLR CLK A B C D ENP GND LOAD ENT QD QC QB QA RCO VCC'


def hc_package(model, function, pin_map, outputs, active_low=()):
    labels = dict(enumerate(pin_map.split(), 1))
    pins = {
        str(number): 'power_in' if label == 'VCC' else 'ground' if label == 'GND'
        else 'output' if number in outputs else 'passive' if label == 'NC' else 'input'
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
        'no_connect': [str(number) for number, label in labels.items() if label == 'NC'],
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

# Package codes are included only where the TI pin diagram and the package
# option addendum cover the same physical package. One orderable per package.
TI_PACKAGE_CODES = {
    'N': ('N', 'PDIP'), 'DR': ('D', 'SOIC'), 'DBR': ('DB', 'SSOP'),
    'NSR': ('NS', 'SOP'), 'PWR': ('PW', 'TSSOP'),
}
SOIC_SOP_TSSOP = 'DR NSR PWR'
COMMON_HC = 'N DR NSR PWR'
WIDE_HC = 'N DR DBR NSR PWR'

LOGIC_FAMILIES = {
    'sn74hc14': ('Hex Schmitt inverter', HEX_INVERTER, (2, 4, 6, 8, 10, 12), (2, 4, 6, 8, 10, 12), 'DR DBR NSR PWR'),
    'sn74hc10': ('Triple 3-input NAND', TRIPLE_GATE, (6, 8, 12), (6, 8, 12), COMMON_HC),
    'sn74hc11': ('Triple 3-input AND', TRIPLE_GATE, (6, 8, 12), (), COMMON_HC),
    'sn74hc20': ('Dual 4-input NAND', DUAL_GATE, (6, 8), (6, 8), COMMON_HC),
    'sn74hc21': ('Dual 4-input AND', DUAL_GATE, (6, 8), (), COMMON_HC),
    'sn74hc27': ('Triple 3-input NOR', TRIPLE_GATE, (6, 8, 12), (6, 8, 12), 'N DR NSR'),
    'sn74hc139': ('Dual 2-to-4 decoder', '1G 1A 1B 1Y0 1Y1 1Y2 1Y3 GND 2Y3 2Y2 2Y1 2Y0 2B 2A 2G VCC',
                  (4, 5, 6, 7, 9, 10, 11, 12), (1, 4, 5, 6, 7, 9, 10, 11, 12, 15), WIDE_HC),
    'sn74hc151': ('8-to-1 multiplexer', 'D3 D2 D1 D0 Y W G GND C B A D7 D6 D5 D4 VCC',
                  (5, 6), (6, 7), COMMON_HC),
    'sn74hc153': ('Dual 4-to-1 multiplexer', '1G B 1C3 1C2 1C1 1C0 1Y GND 2Y 2C0 2C1 2C2 2C3 A 2G VCC',
                  (7, 9), (1, 15), COMMON_HC),
    'sn74hc157': ('Quad 2-to-1 multiplexer', 'SEL 1A 1B 1Y 2A 2B 2Y GND 3Y 3B 3A 4Y 4B 4A G VCC',
                  (4, 7, 9, 12), (15,), WIDE_HC),
    'sn74hc174': ('Hex D flip-flop', 'CLR 1Q 1D 2D 2Q 3D 3Q GND CLK 4Q 4D 5Q 5D 6D 6Q VCC',
                  (2, 5, 7, 10, 12, 15), (1,), WIDE_HC),
    'sn74hc175': ('Quad D flip-flop', 'CLR 1Q 1Q_N 1D 2D 2Q_N 2Q GND CLK 3Q 3Q_N 3D 4D 4Q_N 4Q VCC',
                  (2, 3, 6, 7, 10, 11, 14, 15), (1, 3, 6, 11, 14), COMMON_HC),
    'sn74hc161': ('4-bit binary counter', BINARY_COUNTER, (11, 12, 13, 14, 15), (1, 9), COMMON_HC),
    'sn74hc163': ('4-bit binary counter', BINARY_COUNTER, (11, 12, 13, 14, 15), (1, 9), COMMON_HC),
    'sn74hc164': ('8-bit serial-in shift register', 'A B QA QB QC QD GND CLK CLR QE QF QG QH VCC',
                  (3, 4, 5, 6, 10, 11, 12, 13), (9,), COMMON_HC),
    'sn74hc165': ('8-bit parallel-in shift register', 'SH_LD CLK E F G H QH_N GND QH SER A B C D CLK_INH VCC',
                  (7, 9), (1, 7), WIDE_HC),
    'sn74hc166': ('8-bit parallel-in shift register', 'SER A B C D CLK_INH CLK GND CLR E F G QH H SH_LD VCC',
                  (13,), (9, 15), WIDE_HC),
    'sn74hc393': ('Dual 4-bit ripple counter', '1CLK 1CLR 1QA 1QB 1QC 1QD GND 2QD 2QC 2QB 2QA 2CLR 2CLK VCC',
                  (3, 4, 5, 6, 8, 9, 10, 11), (), WIDE_HC),
    'sn74hc4040': ('12-bit ripple counter', 'QL QF QE QG QD QC QB GND QA CLK CLR QI QH QJ QK VCC',
                   (1, 2, 3, 4, 5, 6, 7, 9, 12, 13, 14, 15), (), WIDE_HC),
}

EXISTING_HC_VARIANTS = {
    'sn74hc00': SOIC_SOP_TSSOP, 'sn74hc02': SOIC_SOP_TSSOP,
    'sn74hc04': SOIC_SOP_TSSOP, 'sn74hc08': SOIC_SOP_TSSOP,
    'sn74hc32': SOIC_SOP_TSSOP, 'sn74hc86': SOIC_SOP_TSSOP,
    'sn74hc74': 'DR DBR NSR PWR', 'sn74hc138': 'DR DBR NSR PWR',
}

HCT_VARIANTS = {
    'sn74hct00': 'DR PWR', 'sn74hct02': SOIC_SOP_TSSOP,
    'sn74hct04': SOIC_SOP_TSSOP, 'sn74hct08': 'N DR PWR',
    'sn74hct32': 'N DR DBR PWR', 'sn74hct74': 'DR DBR PWR',
    'sn74hct138': COMMON_HC,
}


def logic_variants(family, base, suffixes):
    pin_count = len(base['pins'])
    for suffix in suffixes.split():
        code, outline = TI_PACKAGE_CODES[suffix]
        model = family.upper()+suffix
        spec = {
            **base,
            'name': f'{model} {base["logic_function"]} ({outline}-{pin_count})',
            'mpn': model,
            'package': f'{outline}-{pin_count} ({code})',
            'source': f'https://www.ti.com/lit/ds/symlink/{family}.pdf',
            'logic_levels': 'TTL compatible' if family.startswith('sn74hct') else 'HC CMOS',
            'supply_range': (4.5, 5.5) if family.startswith('sn74hct') else (2.0, 6.0),
        }
        yield model.lower(), spec


for family, (function, labels, outputs, active_low, suffixes) in LOGIC_FAMILIES.items():
    base = hc_package(family.upper()+'N', function, labels, outputs, active_low)
    PACKAGE_CATALOG.update(logic_variants(family, base, suffixes))

for family, suffixes in EXISTING_HC_VARIANTS.items():
    PACKAGE_CATALOG.update(logic_variants(family, PACKAGE_CATALOG[family+'n'], suffixes))

for family, suffixes in HCT_VARIANTS.items():
    hc = family.replace('hct', 'hc')+'n'
    PACKAGE_CATALOG.update(logic_variants(family, PACKAGE_CATALOG[hc], suffixes))


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

# The TO-252 and TO-220 pin tables use pin 2 and the tab for the same output.
# The minimum input values are the lower bounds of TI's fixed-output tests.
for package, order_code, outputs in (
    ('TO-252 (NDP)', 'DT', ((1.8, 3.2), (2.5, 3.9), (3.3, 4.75), (5.0, 6.5))),
    ('TO-220 (NDE)', 'T', ((2.5, 3.9), (3.3, 4.75), (5.0, 6.5))),
):
    for output, minimum_input in outputs:
        model = f'LM1117{order_code}-{output:.1f}/NOPB'
        key = f'lm1117{order_code.lower()}_{round(output*10)}'
        PACKAGE_CATALOG[key] = dict(
            analog_package(
                model, f'{output:g} V regulator', package, 'lm1117',
                (('GND', 'ground'), ('VOUT', 'power_out'), ('VIN', 'power_in')),
                ('1', '3'), '1', (minimum_input, 15),
            ),
            regulator_output='2',
        )
