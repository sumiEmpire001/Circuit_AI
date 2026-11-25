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
    scores = sorted(((sum(math.log((counts.get(w, 0)+1)/(m['totals'][label]+len(vocab))) for w in known), label) for label, counts in m['counts'].items()), reverse=True)
    return scores[0][1]

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
        'controller_lcd': {'arduino uno with a 16x2 lcd','connect uno to parallel lcd','wire lcd to uno','arduino uno hd44780 parallel display'},
        'led_bank': {'four channel led bank','4 channel led bank'},
        'rc_ladder': {'two stage rc filter','two stage passive rc filter','cascade rc ladder', "create a two stage rc low pass filter using a 5v dc source a 1 kohm resistor r1 a 2 2 kohm resistor r2 and two 100 nf capacitors c1 and c2 connect v1 positive to r1 r1 to r2 and c1 r2 to c2 and both capacitor returns to v1 negative show the output at r2 and c2 and draw junction dots"},
    }
    normalized = ' '.join(tokens(prompt))
    if normalized not in approved.get(label, set()):
        raise ValueError('Request needs clarification. CircuitLM currently supports reviewed Uno LCD, four-channel LED bank and two-stage RC examples only. Use explicit component/net input for other designs.')
    return EXAMPLES[label]()
