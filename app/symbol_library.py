"""Resolve CircuitLM symbol names and expose their exact library pin definitions."""
from collections import defaultdict
from functools import lru_cache
import gzip
import json
from pathlib import Path
import re

DATA = Path(__file__).with_name('symbol_data')
PIN_SIDES = {0:'left', 90:'bottom', 180:'right', 270:'top'}
LICENSE = 'https://www.kicad.org/libraries/license/'
SOURCE = 'https://kicad.github.io/symbols/'
# Preserve terminal direction for ERC. Open collectors and unused pins do
# not imply a driven or internally tied connection.
ROLES = dict(input='input', output='output', bidirectional='bidirectional',
             tri_state='output', passive='passive', power_in='power_in', power_out='power_out',
             open_collector='passive', open_emitter='passive', free='passive',
             unspecified='passive', no_connect='passive')
SYMBOL_REQUEST = re.compile(
    r'(?:(?:please\s+)?(?:show|draw|generate|display)(?:\s+me)?\s+(?:(?:the|a)\s+)?)?'
    r'(?:schematic\s+|circuit\s+)?symbol\s+(?:for|of)\s+(.+)', re.I)


def normalized(name):
    return ' '.join(name.casefold().split())


def load(name):
    with gzip.open(DATA/f'{name}.json.gz','rt',encoding='utf-8') as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def registry():
    return load('registry')['entries']


@lru_cache(maxsize=4)
def drawings(chunk):
    return load(f'drawings_{chunk}')


def drawing(part):
    key = registry()[part][3]
    return drawings(int(key[0],16)%4)[key]


@lru_cache(maxsize=1)
def names():
    """Train a case-insensitive exact-name index with explicit ambiguity."""
    candidates = defaultdict(set)
    for part, (origin, _, _, _) in registry().items():
        for name in (part, origin, origin.split(':',1)[1]):
            candidates[normalized(name)].add(part)
    return {name: tuple(sorted(parts)) for name,parts in candidates.items()}


def lookup(name):
    parts = names().get(normalized(name), ())
    if len(parts)>1:
        examples = ', '.join(registry()[part][0] for part in parts[:6])
        raise ValueError(f'Symbol name is ambiguous. Use its library-qualified name, such as {examples}.')
    return parts[0] if parts else None


@lru_cache(maxsize=256)
def specification(part):
    origin, ref, datasheet, _ = registry()[part]
    terminals = drawing(part)['terminals']
    labels = {pin: meta[5] for pin,meta in terminals.items() if meta[5] not in {'','~'}}
    return dict(name=origin.split(':',1)[1], symbol='kicad', reference=ref,
                library_id=origin, pins={pin:ROLES[m[6]] for pin,m in terminals.items()},
                pin_labels=labels, required=[], voltage=None,
                no_connect=[pin for pin,meta in terminals.items() if meta[6]=='no_connect'],
                source=datasheet if datasheet.startswith(('https://','http://')) else SOURCE,
                license=LICENSE)
