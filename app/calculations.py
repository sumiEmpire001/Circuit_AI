"""Nominal calculations for explicitly recognized circuit topologies."""
from math import isfinite, pi
import re

from app.design import voltage

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
    if len(parts)==2 and set(parts)=={'dc_source','resistor'}:
        return voltage_divider(design, parts['dc_source'])
    if set(parts)!={'dc_source','resistor','capacitor'}:
        return []
    source, resistor, capacitor = (parts[p] for p in ('dc_source','resistor','capacitor'))
    by_terminal={pin:net for net in design.nets for pin in net.pins}
    positive=by_terminal[f'{source.ref}.+']
    negative=by_terminal[f'{source.ref}.-']
    resistor_nets={by_terminal[f'{resistor.ref}.{pin}'].name for pin in ('1','2')}
    capacitor_nets={by_terminal[f'{capacitor.ref}.{pin}'].name for pin in ('1','2')}
    middle=resistor_nets & capacitor_nets
    if len(middle)!=1:
        return []
    if resistor_nets-middle=={positive.name} and capacitor_nets-middle=={negative.name}:
        kind = 'ideal_rc_lowpass'
    elif capacitor_nets-middle=={positive.name} and resistor_nets-middle=={negative.name}:
        kind = 'ideal_rc_highpass'
    else:
        return []
    tau=scaled(resistor.value,RESISTANCE)*scaled(capacitor.value,CAPACITANCE)
    if not isfinite(tau) or tau<=0:
        return []
    cutoff=(1/(2*pi))/tau
    if not isfinite(cutoff):
        return []
    assumptions = 'Ideal source, nominal components and unloaded output. Analytical estimate.'
    if kind=='ideal_rc_highpass':
        assumptions += ' Steady DC is blocked by the series capacitor.'
    return [dict(
        kind=kind, net=middle.pop(),
        time_constant_s=tau, cutoff_hz=cutoff,
        assumptions=assumptions,
    )]



def voltage_divider(design, source):
    by_pin={pin:net for net in design.nets for pin in net.pins}
    high=by_pin[f'{source.ref}.+']
    low=by_pin[f'{source.ref}.-']
    midpoint=next(net for net in design.nets if net.name not in {high.name,low.name})
    resistors={c.ref: c for c in design.components if c.part=='resistor'}
    upper_refs={pin.split('.')[0] for pin in high.pins} & resistors.keys()
    lower_refs={pin.split('.')[0] for pin in low.pins} & resistors.keys()
    if len(upper_refs)!=1 or len(lower_refs)!=1 or upper_refs==lower_refs:
        return []
    if {pin.split('.')[0] for pin in midpoint.pins}!=resistors.keys():
        return []
    upper,lower=(scaled(resistors[next(iter(refs))].value,RESISTANCE) for refs in (upper_refs,lower_refs))
    if not all(isfinite(r) and r>0 for r in (upper,lower)):
        return []
    scale=max(upper,lower)
    gain=(lower/scale)/(upper/scale+lower/scale)
    return [dict(
        kind='ideal_voltage_divider',net=midpoint.name,
        output_v=voltage(source.value)*gain, gain=gain,
        assumptions='Ideal source and nominal resistors. Output is unloaded. Analytical estimate.',
    )]
