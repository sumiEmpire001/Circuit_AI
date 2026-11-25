"""Independent, deliberately constrained multinomial naive Bayes intent model."""
import json
import math
import re
from pathlib import Path
from functools import lru_cache

def tokens(text):
    return re.findall(r'[a-z0-9]+', text.lower())

@lru_cache(maxsize=1)
def weights():
    return json.loads(Path(__file__).with_name('circuitlm_weights.json').read_text())

def classify(prompt):
    m = weights()
    vocab = set(m['vocabulary'])
    words = tokens(prompt)
    known = [w for w in words if w in vocab]
    if not known:
        return 'unsupported'
    smoothing = m['smoothing']
    scores = (
        (sum(math.log((counts.get(w, 0)+smoothing)/(m['totals'][label]+smoothing*len(vocab)))
             for w in known), label)
        for label, counts in m['counts'].items()
    )
    return max(scores)[1]


def draft_local(prompt, previous_design=None):
    from app.design_examples import EXAMPLES
    if previous_design is not None:
        # Explicit bounded value edit; no topology changes or silent constraint drops.
        match = re.fullmatch(r'change ([A-Za-z][A-Za-z0-9_+-]*) to ([0-9]+(?:\.[0-9]+)? (?:ohm|kohm|nF|uF|pF))', prompt.strip(), re.I)
        if not match:
            raise ValueError('Use change R1 to 330 ohm, or edit the tables directly.')
        ref, value = match.groups()
        from app.design import Design
        data = previous_design.model_dump()
        for component in data['components']:
            if component['ref'].lower() == ref.lower():
                unit = value.split()[-1].lower()
                if not ((component['part']=='resistor' and unit in {'ohm','kohm'}) or (component['part']=='capacitor' and unit in {'nf','uf','pf'})):
                    raise ValueError('Value unit does not match supported component type.')
                if float(value.split()[0]) <= 0:
                    raise ValueError('Value must be positive.')
                component['value'] = value
                return Design.model_validate(data)
        raise ValueError('Unknown component reference.')
    label = classify(prompt)
    # Classifier alone cannot prove that every constraint is supported.
    # Only exact reviewed aliases are accepted until constraint extraction is trained.
    approved = {
        'bridge_rectifier': {'four diode bridge rectifier', "create a full wave bridge rectifier using four 1n4007 diodes d1 d2 d3 d4 a 100 nf capacitor c1 a two pin isolated low voltage ac input j1 and a two pin dc output j2 connect j1 pin 1 to d1 cathode and d2 anode j1 pin 2 to d3 cathode and d4 anode d2 and d4 cathodes to positive output j2 pin 1 and c1 pin 2 and d1 and d3 anodes to negative output j2 pin 2 and c1 pin 1"},
        'temperature_motor': {
            'arduino temperature controlled motor',
            'arduino uno lm35 l293d motor control',
            'control a 6v dc motor using an arduino uno lm35 temperature sensor and l293d driver',
        },
        'mega_ldr': {'arduino mega with an ldr light sensor', 'mega 2560 photoresistor divider'},
        'mega_ldr_servo': {'arduino mega ldr and separately powered servo', 'mega 2560 photoresistor with a separate 5 v servo supply'},
        'schmitt_inverter': {
            '5 v sn74hc14 schmitt trigger inverter',
            'make a 5v sn74hc14n inverter with input and output connectors',
        },
        'controller_lcd': {'arduino uno with a 16x2 lcd','connect uno to parallel lcd','wire lcd to uno','arduino uno hd44780 parallel display'},
        'led_bank': {'four channel led bank','4 channel led bank'},
        'rc_ladder': {'two stage rc filter','two stage passive rc filter','cascade rc ladder', "create a two stage rc low pass filter using a 5v dc source a 1 kohm resistor r1 a 2 2 kohm resistor r2 and two 100 nf capacitors c1 and c2 connect v1 positive to r1 r1 to r2 and c1 r2 to c2 and both capacitor returns to v1 negative show the output at r2 and c2 and draw junction dots"},
    }
    normalized = ' '.join(tokens(prompt))
    if normalized not in approved.get(label, set()):
        raise ValueError('Request needs clarification. Try a reviewed circuit example from Studio, or use explicit component and net input for other designs.')
    return EXAMPLES[label]()
