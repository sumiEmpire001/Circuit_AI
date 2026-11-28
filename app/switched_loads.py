"""Parse a counted list of low-voltage loads controlled by one switch."""
from collections import Counter
import re

from app.design import Design

NUMBERS = dict(zip('one two three four five six seven eight'.split(), range(1, 9)))
ITEM = re.compile(
    r'(?P<count>[1-8]|one|two|three|four|five|six|seven|eight|a|an|single)\s+'
    r'(?P<part>(?:light\s+)?bulbs?|lamps?|(?:dc\s+)?fans?|(?:on/off\s+)?switch(?:es)?)\b'
)
SEPARATOR = re.compile(
    r'^\s*(?:(?:[,;]|\b(?:and|plus|with|controls?|(?:all )?controlled by)\b)\s*)*'
)
INTRO = re.compile(
    r'^(?:(?:please )?(?:i (?:need|want)|draw|generate|design|create|show me|wire|connect) )?'
    r'(?:(?:a |the )?(?:connection|(?:circuit )?diagram)(?: for| of| showing| with)? |(?:a )?circuit (?:for|with) )?'
)
END = re.compile(r'[.!?]*\s+(?:i need (?:the |a )?(?:circuit )?diagram(?: for this)?|(?:in )?parallel)$')
SUPPLY = re.compile(
    r'\s+(?:powered by|using|on|with)\s+(?:a )?(\d+(?:\.\d+)?)\s*(?:v|volts?)\s*dc'
    r'(?:\s+(?:supply|source|battery))?$'
)


def parse_switched_loads(prompt):
    request = ' '.join(prompt.lower().strip().rstrip('.!?').split())
    request = END.sub('', request)
    request = INTRO.sub('', request, count=1)
    supply = SUPPLY.search(request)
    if supply:
        request = request[:supply.start()]
    request = END.sub('', request)
    request = re.sub(r'\s+in parallel(?=\s*(?:,?\s+(?:all )?controlled by)\b)', '', request)
    counts = Counter()
    remaining = request
    while remaining:
        item = ITEM.match(remaining)
        if not item:
            return None
        part = item['part']
        kind = 'switch' if 'switch' in part else 'fan' if 'fan' in part else 'lamp'
        count = item['count']
        counts[kind] += int(count) if count.isdigit() else NUMBERS.get(count, 1)
        tail = remaining[item.end():]
        separator = SEPARATOR.match(tail)
        remaining = tail[separator.end():]
        if tail and (not remaining or not separator.end()):
            return None

    if not counts['switch'] or not (counts['lamp'] or counts['fan']):
        return None
    if counts['switch'] != 1 or counts['lamp'] + counts['fan'] > 8:
        raise ValueError('Specify one shared switch and one to eight bulbs or DC fans for a parallel circuit.')
    volts = float(supply[1]) if supply else 12
    if not 0 < volts <= 24:
        raise ValueError('Specify a low-voltage DC supply between 0 and 24 V for this draft.')

    components = [
        {'ref': 'V1', 'part': 'dc_source', 'value': f'{volts:g} V', 'position': {'x': 215, 'y': 130}},
        {'ref': 'S1', 'part': 'switch', 'position': {'x': 565, 'y': 130}},
    ]
    switched = ['S1.2']
    returned = ['V1.-']
    for kind, prefix, model, terminals in (
        ('lamp', 'L', 'lamp_bulb', ('1', '2')), ('fan', 'F', 'dc_fan', ('+', '-')),
    ):
        for index in range(1, counts[kind] + 1):
            ref = f'{prefix}{index}'
            components.append({'ref': ref, 'part': model, 'value': f'{volts:g} V DC',
                               'position': {'x': 730, 'y': 305 + 155*(len(components)-2)}})
            switched.append(f'{ref}.{terminals[0]}')
            returned.append(f'{ref}.{terminals[1]}')
    assumption = 'Assumed 12 V DC because the request did not specify a supply.' if supply is None else f'Requested supply: {volts:g} V DC.'
    return Design(title='One switch controlling parallel loads', components=components, nets=[
        {'name': 'SUPPLY', 'pins': ['V1.+', 'S1.1']},
        {'name': 'SWITCHED', 'pins': switched},
        {'name': 'RETURN', 'pins': returned},
    ], notes=[
        assumption,
        'S1 controls all loads. Each bulb or two-wire DC fan is across the switched supply and return.',
        'Low-voltage concept diagram only. Verify load ratings, fan startup current and DC switch rating before building. For household mains, use a qualified electrician.',
    ])
