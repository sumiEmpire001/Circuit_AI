"""Complete topology-and-value requests for simple passive circuit families."""
from decimal import Decimal
from math import isfinite, pi
import re

from app.calculations import CAPACITANCE, RESISTANCE, scaled
from app.constraint_parser import IDENTIFIER, NUMBER, parse_component
from app.design import Design, voltage

HEADING = re.compile(
    r'(?:(?:design|build|create|make|draw)(?: me)?|I (?:need|want)) (?:a |an )?'
    r'(?P<family>(?:resistive )?voltage divider|(?:first[- ]order )?RC (?:low|high)[- ]pass filter)', re.I,
)
VALUE = rf'{NUMBER}\s*[A-Za-zµμΩ]+'
SOURCE = re.compile(
    rf'(?:use (?:a )?(?P<value>{NUMBER}\s*V) (?:DC )?(?:source|supply)'
    rf'(?: named (?P<ref>{IDENTIFIER}))?|use (?P<input>{NUMBER}\s*V) at the input)', re.I,
)
PART = re.compile(
    rf'(?:the )?(?P<role>upper resistor|top resistor|lower resistor|bottom resistor|'
    rf'series resistor|shunt capacitor|series capacitor|shunt resistor)'
    rf'(?: (?P<ref>{IDENTIFIER}))? (?:is|=) (?P<value>{VALUE})', re.I,
)
TARGET = re.compile(
    rf'target (?:an? )?(?P<kind>output(?: voltage)?|cutoff(?: frequency)?) of '
    rf'(?P<number>{NUMBER})\s*(?P<unit>V|[mkM]?Hz)', re.I,
)
FREQUENCY_MULTIPLIERS = {'Hz':1,'kHz':1e3,'mHz':1e-3,'MHz':1e6}
RESISTOR_SCALES = ((1e6,'Mohm'),(1e3,'kohm'),(1,'ohm'),(1e-3,'mohm'))
CAPACITOR_SCALES = ((1,'F'),(1e-3,'mF'),(1e-6,'uF'),(1e-9,'nF'),(1e-12,'pF'))
ROLES = {'top resistor':'upper resistor', 'bottom resistor':'lower resistor'}
FAMILIES = {
    'divider': ('upper resistor','lower resistor','Voltage divider','output voltage'),
    'low_pass': ('series resistor','shunt capacitor','First-order RC low-pass filter','cutoff frequency'),
    'high_pass': ('series capacitor','shunt resistor','First-order RC high-pass filter','cutoff frequency'),
}
PARTS = {
    'source': ('dc_source','V1'),
    'upper resistor': ('resistor','R1'),
    'lower resistor': ('resistor','R2'),
    'series resistor': ('resistor','R1'),
    'shunt capacitor': ('capacitor','C1'),
    'series capacitor': ('capacitor','C1'),
    'shunt resistor': ('resistor','R1'),
}


def parse_passive_intent(prompt):
    """Return None for another request family, or reject any unhandled clause."""
    clauses = [s.strip().removesuffix('.') for s in re.split(r'[;\n]+|(?<=\.)\s+', prompt.strip()) if s.strip()]
    if not clauses or not (heading := HEADING.fullmatch(clauses[0])):
        return None
    name = heading['family'].lower()
    family = 'divider' if name.endswith('divider') else 'high_pass' if 'high' in name else 'low_pass'
    upper, lower, title, quantity = FAMILIES[family]
    expected = ('source',upper,lower)
    parts = {}
    asked_calculation = False
    target = None
    for clause in clauses[1:]:
        if source := SOURCE.fullmatch(clause):
            role, value, ref = 'source', source['value'] or source['input'], source['ref']
        elif part := PART.fullmatch(clause):
            raw_role = part['role'].lower()
            role, value, ref = ROLES.get(raw_role,raw_role), part['value'], part['ref']
        elif match := TARGET.fullmatch(clause):
            if target is not None:
                raise ValueError('Request needs clarification. Specify only one target.')
            target = parse_target(match, family)
            continue
        elif clause.casefold() == f'calculate the nominal {quantity}' and not asked_calculation:
            asked_calculation = True
            continue
        else:
            raise ValueError(f'Request needs clarification. Unsupported clause “{clause[:100]}”.')

        if role not in expected:
            raise ValueError(f'Request needs clarification. {role.capitalize()} is not part of this topology.')
        if role in parts:
            raise ValueError(f'Request needs clarification. Specify {role} once.')
        part_id, default_ref = PARTS[role]
        parts[role] = parse_component(f'{value} {part_id} named {ref or default_ref}')

    if 'source' not in parts:
        raise ValueError('Request needs clarification. Provide the input source voltage.')
    input_v = voltage(parts['source']['value'])
    if not 0 < input_v <= 24:
        raise ValueError('Request needs clarification. Use an input above 0 V and at most 24 V.')

    missing = [role for role in (upper,lower) if role not in parts]
    notes = []
    if target is not None:
        if len(missing)!=1:
            raise ValueError('Request needs clarification. Specify exactly one passive value when setting a target.')
        role = missing[0]
        known = parts[lower if role==upper else upper]
        value = solve_value(family, role, known, input_v, target)
        part_id, default_ref = PARTS[role]
        used_refs = {part['ref'] for part in parts.values()}
        ref = default_ref
        if ref in used_refs:
            ref = next(f'{ref[0]}{i}' for i in range(1,4) if f'{ref[0]}{i}' not in used_refs)
        parts[role] = parse_component(f'{value} {part_id} named {ref}')
        label = f'{target:g} V output' if family=='divider' else f'{target:g} Hz cutoff'
        notes.append(f'{ref} = {value} is the calculated nominal value for a {label}. '
                     'Uses ideal, unloaded output and nominal component values.')
    elif missing:
        raise ValueError(f'Request needs clarification. Provide {", ".join(missing)}.')
    source, series, shunt = (parts[role] for role in expected)
    v, a, b = (p['ref'] for p in (source,series,shunt))
    return Design(title=title, components=[source,series,shunt], notes=notes, nets=[
        dict(name='INPUT', pins=[f'{v}.+',f'{a}.1']),
        dict(name='OUT', pins=[f'{a}.2',f'{b}.1']),
        dict(name='RETURN', pins=[f'{b}.2',f'{v}.-']),
    ])



def parse_target(match, family):
    kind, unit = match['kind'].lower(), match['unit']
    if family=='divider':
        if not kind.startswith('output') or unit.lower()!='v':
            raise ValueError('Request needs clarification. Set an output target in volts for a divider.')
        multiplier = 1
    else:
        if not kind.startswith('cutoff') or not unit.lower().endswith('hz'):
            raise ValueError('Request needs clarification. Set a cutoff target in Hz, mHz, kHz or MHz.')
        prefix = unit[:-2]
        key = ('M' if prefix=='M' else prefix.lower())+'Hz'
        multiplier = FREQUENCY_MULTIPLIERS[key]
    value = float(match['number'])*multiplier
    if not isfinite(value) or value<=0:
        raise ValueError('Request needs clarification. The target must be positive and finite.')
    return value


def solve_value(family, missing, known, input_v, target):
    if family=='divider':
        if target>=input_v:
            raise ValueError('Request needs clarification. Divider output must be below the input voltage.')
        known_value = scaled(known['value'],RESISTANCE)
        headroom = input_v-target
        ratio = headroom/target if missing=='upper resistor' else target/headroom
        value = known_value*ratio
    else:
        units = CAPACITANCE if known['part']=='capacitor' else RESISTANCE
        known_value = scaled(known['value'],units)
        denominator = target*known_value
        value = (1/(2*pi))/denominator if denominator else 0
    if not isfinite(value) or value<=0:
        raise ValueError('Request needs clarification. The required value is outside the numerical range.')

    scales = CAPACITOR_SCALES if PARTS[missing][0]=='capacitor' else RESISTOR_SCALES
    multiplier,unit = next((pair for pair in scales if value>=pair[0]),scales[-1])
    normalized = value/multiplier
    if not isfinite(normalized):
        raise ValueError('Request needs clarification. The required value is outside the numerical range.')
    number = format(Decimal(f'{normalized:.10g}'),'f')
    if len(number)+len(unit)+1>80:
        raise ValueError('Request needs clarification. The required value is outside the supported value format.')
    return f'{number} {unit}'
