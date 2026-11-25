"""Translate complete, pin-explicit prose into the existing Design model."""
from math import isfinite
import re

from app.catalog import CATALOG
from app.design import Design

IDENTIFIER = r'[A-Za-z_][A-Za-z0-9_+\-]{0,31}'
DECLARATION = re.compile(
    rf'(?:an?\s+)?(?P<part_value>.+?)\s+named\s+(?P<ref>{IDENTIFIER})', re.I
)
CONNECTION = re.compile(rf'connect\s+(.+?)\s+(?:on|as)\s+net\s+({IDENTIFIER})', re.I)
TERMINAL = re.compile(
    rf'({IDENTIFIER})(?:\s+pin\s+|\s+|\.)([A-Za-z0-9_+\-]{{1,24}}(?:\.[A-Za-z0-9_+\-]{{1,12}})?)', re.I
)
LIST_SEPARATOR = re.compile(r'\s*,\s*(?:and\s+)?|\s+(?:and|to)\s+', re.I)
NUMBER = r'(?:\d+(?:\.\d+)?|\.\d+)'

PART_NAMES = {
    'dc source': 'dc_source', 'resistor': 'resistor', 'capacitor': 'capacitor',
    'polarized capacitor': 'capacitor_polarized', 'inductor': 'inductor',
    'potentiometer': 'potentiometer', 'connector': 'connector2',
    'led': 'led', 'ne555p': 'ne555p', 'lm324n': 'lm324n',
}
UNIT_FAMILIES = {
    'dc_source': {'v': 'V'},
    'resistor': {'ohm': 'ohm', 'kohm': 'kohm', 'Mohm': 'Mohm', 'mohm': 'mohm'},
    'potentiometer': {'ohm': 'ohm', 'kohm': 'kohm', 'Mohm': 'Mohm', 'mohm': 'mohm'},
    'capacitor': {'pf': 'pF', 'nf': 'nF', 'uf': 'uF', 'mf': 'mF', 'f': 'F'},
    'inductor': {'nh': 'nH', 'uh': 'uH', 'mh': 'mH', 'h': 'H'},
}
UNIT_FAMILIES['capacitor_polarized'] = UNIT_FAMILIES['capacitor']
VALUE = re.compile(rf'({NUMBER})\s*([a-zA-ZµμΩ]+)')
NAMES = {**{part: part for part in CATALOG}, **PART_NAMES}
ORDERED_NAMES = sorted(NAMES, key=len, reverse=True)


def matches_constraint_prompt(prompt):
    return bool(re.match(r'^\s*(?:title\s*:|use\s+.+?\bnamed\s+|create a circuit\.)', prompt, re.I))


def parse_component(description):
    match = DECLARATION.fullmatch(description)
    if not match:
        raise ValueError('Declare parts as “Use a 330 ohm resistor named R1.”')
    declaration = ' '.join(match['part_value'].split())
    lowered = declaration.lower()
    name = next((name for name in ORDERED_NAMES
                 if lowered==name or lowered.endswith(' '+name)), None)
    if name is None:
        raise ValueError(f'Unknown part in declaration for {match["ref"]}.')
    part = NAMES[name]
    value = declaration[:-len(name)].strip()
    family = UNIT_FAMILIES.get(part)
    if family:
        value = value.replace('µ','u').replace('μ','u').replace('Ω','ohm').replace('ω','ohm')
        parsed = VALUE.fullmatch(value)
        unit = None
        if parsed:
            spelling = parsed[2]
            if spelling.startswith('M'):
                unit = family.get(spelling)
            else:
                unit = family.get(spelling.lower())
        if not unit or not isfinite(float(parsed[1])) or not float(parsed[1]) > 0:
            raise ValueError(f'Provide a positive value in a supported unit for {match["ref"]}.')
        number = '0' + parsed[1] if parsed[1].startswith('.') else parsed[1]
        value = f'{number} {unit}'
    elif part == 'led' and value.lower() in {'red','green','blue','amber','yellow','white'}:
        value = value.capitalize()
    elif value:
        raise ValueError(f'Unrecognized value or constraint for {match["ref"]}.')
    return dict(ref=match['ref'].upper(), part=part, value=value)


def resolve_terminal(token, components):
    match = TERMINAL.fullmatch(token)
    if not match:
        raise ValueError(f'Use a pin number or label for “{token}”.')
    ref, pin = match[1].upper(), match[2].upper()
    component = components.get(ref)
    if component is None:
        raise ValueError(f'Unknown component {ref}.')
    spec = CATALOG[component['part']]
    if component['part']=='dc_source':
        pin = {'POSITIVE': '+', 'NEGATIVE': '-'}.get(pin, pin)
    if pin not in spec['pins']:
        pin = next((number for number,label in spec.get('pin_labels', {}).items()
                    if label.upper()==pin), pin)
    if pin not in spec['pins']:
        raise ValueError(f'Unknown pin {ref}.{pin}.')
    return f'{ref}.{pin}'


def parse_constraints(prompt):
    """Consume every clause and validate the explicit assignments as a single graph."""
    title = 'Circuit from pin-level prompt'
    title_seen = False
    components = {}
    claims = []
    clauses = re.split(r'[;\n]+|(?<=\.)[ \t]+', prompt.strip())
    for raw_clause in clauses:
        clause = raw_clause.strip().removesuffix('.').strip()
        if not clause or clause.lower() == 'create a circuit':
            continue
        subject, _, description = clause.partition(' ')
        if subject.lower()=='use':
            for declaration in LIST_SEPARATOR.split(description):
                component = parse_component(declaration)
                ref = component['ref']
                if ref in components:
                    raise ValueError(f'Duplicate component {ref}.')
                components[ref] = component
        elif clause.lower().startswith('title:'):
            if title_seen or not clause[6:].strip():
                raise ValueError('Provide at most one nonempty title.')
            title = clause[6:].strip()
            title_seen = True
        elif claim := CONNECTION.fullmatch(clause):
            claims.append((claim[2].upper(), LIST_SEPARATOR.split(claim[1])))
        else:
            raise ValueError(f'Unsupported clause “{clause[:100]}”. Use explicit, named pin connections.')

    nets = {}
    for name, terminals in claims:
        pins = [resolve_terminal(token, components) for token in terminals]
        if len(set(pins)) < 2 or len(set(pins))!=len(pins):
            raise ValueError(f'Net {name} needs at least two distinct terminals without repetitions.')
        nets.setdefault(name, {}).update(dict.fromkeys(pins))
    if not nets:
        raise ValueError('Provide at least one named net with two or more terminals.')
    return Design(title=title, components=list(components.values()),
                  nets=[dict(name=name, pins=list(pins)) for name, pins in nets.items()])
