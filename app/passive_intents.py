"""Complete topology-and-value requests for two passive circuit families."""
import re

from app.constraint_parser import IDENTIFIER, NUMBER, parse_component
from app.design import Design, voltage

HEADING = re.compile(
    r'(?:design|build|create|make|draw)(?: me)? (?:a |an )?'
    r'(?P<family>(?:resistive )?voltage divider|first[- ]order RC low[- ]pass filter)', re.I,
)
VALUE = rf'{NUMBER}\s*[A-Za-zµμΩ]+'
SOURCE = re.compile(
    rf'(?:use (?:a )?(?P<value>{NUMBER}\s*V) (?:DC )?(?:source|supply)'
    rf'(?: named (?P<ref>{IDENTIFIER}))?|use (?P<input>{NUMBER}\s*V) at the input)', re.I,
)
PART = re.compile(
    rf'(?:the )?(?P<role>upper resistor|top resistor|lower resistor|bottom resistor|series resistor|shunt capacitor)'
    rf'(?: (?P<ref>{IDENTIFIER}))? (?:is|=) (?P<value>{VALUE})', re.I,
)
ROLES = {'top resistor':'upper resistor', 'bottom resistor':'lower resistor'}
FAMILIES = {
    'divider': ('upper resistor','lower resistor','Voltage divider','output voltage'),
    'low_pass': ('series resistor','shunt capacitor','First-order RC low-pass filter','cutoff frequency'),
}
PARTS = {
    'source': ('dc_source','V1'),
    'upper resistor': ('resistor','R1'),
    'lower resistor': ('resistor','R2'),
    'series resistor': ('resistor','R1'),
    'shunt capacitor': ('capacitor','C1'),
}


def parse_passive_intent(prompt):
    """Return None for another request family, or reject any unhandled clause."""
    clauses = [s.strip().removesuffix('.') for s in re.split(r'[;\n]+|(?<=\.)\s+', prompt.strip()) if s.strip()]
    if not clauses or not (heading := HEADING.fullmatch(clauses[0])):
        return None
    family = 'divider' if heading['family'].lower().endswith('divider') else 'low_pass'
    upper, lower, title, quantity = FAMILIES[family]
    expected = ('source',upper,lower)
    parts = {}
    asked_calculation = False
    for clause in clauses[1:]:
        if source := SOURCE.fullmatch(clause):
            role, value, ref = 'source', source['value'] or source['input'], source['ref']
        elif part := PART.fullmatch(clause):
            raw_role = part['role'].lower()
            role, value, ref = ROLES.get(raw_role,raw_role), part['value'], part['ref']
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

    if missing := [role for role in expected if role not in parts]:
        raise ValueError(f'Request needs clarification. Provide {", ".join(missing)}.')
    source, series, shunt = (parts[role] for role in expected)
    if not 0 < voltage(source['value']) <= 24:
        raise ValueError('Request needs clarification. Use an input above 0 V and at most 24 V.')
    v, a, b = (p['ref'] for p in (source,series,shunt))
    return Design(title=title, components=[source,series,shunt], nets=[
        dict(name='INPUT', pins=[f'{v}.+',f'{a}.1']),
        dict(name='OUT', pins=[f'{a}.2',f'{b}.1']),
        dict(name='RETURN', pins=[f'{b}.2',f'{v}.-']),
    ])
