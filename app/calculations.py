"""Nominal calculations for explicitly recognized circuit topologies."""
from math import isfinite, pi
import re

RESISTANCE = {'ohm':1, 'mohm':1e-3, 'kohm':1e3, 'Mohm':1e6}
CAPACITANCE = {'pF':1e-12, 'nF':1e-9, 'uF':1e-6, 'mF':1e-3, 'F':1}
VALUE = re.compile(r'(\d+(?:\.\d+)?)\s*([A-Za-z]+)')


def scaled(value, units):
    match = VALUE.fullmatch(value.strip())
    if match and match[2] in units:
        return float(match[1])*units[match[2]]
    return 0


def calculate(design, validation):
    if validation['errors'] or len(design.components)!=3 or len(design.nets)!=3:
        return []
    parts={c.part:c for c in design.components}
    if set(parts)!={'dc_source','resistor','capacitor'}:
        return []
    source, resistor, capacitor = (parts[p] for p in ('dc_source','resistor','capacitor'))
    by_terminal={pin:net for net in design.nets for pin in net.pins}
    positive=by_terminal[f'{source.ref}.+']
    negative=by_terminal[f'{source.ref}.-']
    resistor_nets={by_terminal[f'{resistor.ref}.{pin}'].name for pin in ('1','2')}
    capacitor_nets={by_terminal[f'{capacitor.ref}.{pin}'].name for pin in ('1','2')}
    middle=resistor_nets & capacitor_nets
    if len(middle)!=1 or resistor_nets-middle!={positive.name} or capacitor_nets-middle!={negative.name}:
        return []
    tau=scaled(resistor.value,RESISTANCE)*scaled(capacitor.value,CAPACITANCE)
    if not isfinite(tau) or tau<=0:
        return []
    cutoff=(1/(2*pi))/tau
    if not isfinite(cutoff):
        return []
    return [dict(
        kind='ideal_rc_lowpass', net=middle.pop(),
        time_constant_s=tau, cutoff_hz=cutoff,
        assumptions='Ideal source, nominal components and unloaded output. Analytical estimate.',
    )]
