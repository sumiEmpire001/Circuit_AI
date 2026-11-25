"""Recognize repeated LED branches with a shared DC supply."""


def led_branches(design):
    parts = {c.ref: c.part for c in design.components}
    if len(parts)<9 or set(parts.values())!={'dc_source','resistor','led'}:
        return None
    sources = [c.ref for c in design.components if c.part=='dc_source']
    if len(sources)!=1:
        return None
    source = sources[0]
    nets = {pin: net for net in design.nets for pin in net.pins}
    power, ground = nets.get(f'{source}.+'), nets.get(f'{source}.-')
    if power is None or ground is None or power==ground:
        return None

    branches = []
    for ref in sorted(parts):
        if parts[ref]!='resistor':
            continue
        channel = nets.get(f'{ref}.2')
        if nets.get(f'{ref}.1')!=power or channel is None or len(channel.pins)!=2:
            return None
        pin = next(p for p in channel.pins if p!=f'{ref}.2')
        led, terminal = pin.split('.')
        if parts[led]!='led' or terminal!='A' or nets.get(f'{led}.K')!=ground:
            return None
        branches.append((ref, led, channel.name))
    if len(branches)*2+1!=len(parts) or len({led for _,led,_ in branches})!=len(branches):
        return None
    if len(power.pins)!=len(ground.pins) or len(power.pins)!=1+len(branches):
        return None
    return source, power.name, ground.name, branches


def bank_placement(design):
    bank = led_branches(design)
    if bank is None or any(c.position for c in design.components):
        return {}
    source, _, _, branches = bank
    positions = {source:(480,130)}
    for row,(resistor, led, _) in enumerate(branches):
        y = 310 + 155*row
        positions[resistor] = (210,y)
        positions[led] = (750,y)
    return positions
