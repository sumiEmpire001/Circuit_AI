"""Editable multi-component netlist, structural checks and limited ERC."""
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.catalog import CATALOG
ID = r'^[A-Za-z_][A-Za-z0-9_+-]{0,31}$'
PIN = r'^[A-Za-z0-9_+\-]{1,24}$'
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
class Position(Strict):
    x: float = Field(ge=170, le=100000)
    y: float = Field(ge=110, le=100000)
class CustomPart(Strict):
    name: str = Field(min_length=1,max_length=80)
    pins: dict[str, Literal['passive','input','output','bidirectional','power_in','power_out','ground']] = Field(min_length=1,max_length=64)
    required: list[str] = Field(default_factory=list,max_length=64)
    @model_validator(mode='after')
    def valid(self):
        if any(not re.fullmatch(PIN,p) for p in self.pins): raise ValueError('Invalid custom pin name')
        if not set(self.required) <= set(self.pins): raise ValueError('Unknown required pin')
        return self
class Component(Strict):
    ref: str = Field(pattern=ID)
    part: str = Field(pattern=ID)
    value: str = Field(default='',max_length=80)
    position: Position | None = None
class Net(Strict):
    name: str = Field(pattern=ID)
    pins: list[str] = Field(min_length=2,max_length=400)
class Design(Strict):
    title: str = Field(default='Circuit draft',min_length=1,max_length=120)
    components: list[Component] = Field(min_length=1,max_length=200)
    nets: list[Net] = Field(default_factory=list,max_length=1000)
    custom_parts: dict[str,CustomPart] = Field(default_factory=dict,max_length=100)
    notes: list[str] = Field(default_factory=list,max_length=40)
    @model_validator(mode='after')
    def valid(self):
        if any(len(n)>1000 for n in self.notes): raise ValueError('Note exceeds 1000 characters')
        if any(not re.fullmatch(ID,k) for k in self.custom_parts): raise ValueError('Invalid custom part identifier')
        if set(self.custom_parts) & set(CATALOG): raise ValueError('Custom parts cannot override built-in definitions')
        refs = {c.ref:c for c in self.components}
        if len(refs)!=len(self.components): raise ValueError('Duplicate component reference')
        catalog = self.catalog()
        for c in self.components:
            if c.part not in catalog: raise ValueError(f'Unknown part {c.part}; add a custom_parts definition with its exact pins')
        names, used = set(), set()
        for net in self.nets:
            if net.name in names: raise ValueError(f'Duplicate net {net.name}')
            names.add(net.name)
            for pin in net.pins:
                if pin in used: raise ValueError(f'Pin {pin} is repeated or assigned to multiple nets; merge the nets')
                used.add(pin)
                if pin.count('.')!=1: raise ValueError(f'Pin must be REF.PIN: {pin}')
                ref, number = pin.split('.')
                if ref not in refs or number not in catalog[refs[ref].part]['pins']:
                    raise ValueError(f'Unknown component or pin: {pin}')
        return self
    def catalog(self):
        return {**CATALOG, **{k:dict(v.model_dump(),symbol='custom',voltage=None,source=None) for k,v in self.custom_parts.items()}}
def voltage(value):
    match=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*[vV]\s*',value)
    return float(match[1]) if match else None

def check_design(design):
    catalog=design.catalog(); refs={c.ref:c for c in design.components}
    pin_net={p:n.name for n in design.nets for p in n.pins}
    capacitor_returns = set()
    for component in design.components:
        if component.part=='capacitor':
            ends = [pin_net.get(f'{component.ref}.{pin}') for pin in ('1', '2')]
            capacitor_returns.update((tuple(ends), tuple(reversed(ends))))
        elif component.part=='capacitor_polarized':
            capacitor_returns.add(tuple(pin_net.get(f'{component.ref}.{pin}') for pin in ('+', '-')))
    source_pairs = {}
    for c in design.components:
        if c.part != 'dc_source':
            continue
        positive, negative = (pin_net.get(f'{c.ref}.{pin}') for pin in ('+', '-'))
        if positive and negative and (source_voltage := voltage(c.value)) is not None:
            source_pairs.setdefault((positive, negative), []).append(source_voltage)
    errors=[]; warnings=[]
    def issue(target,code,message,error=False):
        (errors if error else warnings).append(dict(target=target,code=code,message=message))
    graph={r:set() for r in refs}
    for c in design.components:
        spec=catalog[c.part]
        for pin in spec['required']:
            if f'{c.ref}.{pin}' not in pin_net: issue(c.ref,'unconnected_required',f'{c.ref}.{pin} needs a connection',True)
        for pin in spec.get('no_connect', ()):
            if f'{c.ref}.{pin}' in pin_net:
                issue(c.ref, 'no_connect_pin', f'{c.ref}.{pin} is marked NC for this package and must remain open', True)
        if output_pin := spec.get('regulator_output'):
            output_net = pin_net.get(f'{c.ref}.{output_pin}')
            return_net = pin_net.get(f'{c.ref}.{spec["supply_return"]}')
            if output_net and return_net:
                if (output_net, return_net) not in capacitor_returns:
                    issue(c.ref, 'regulator_output_capacitor', 'Connect the required output capacitor from VOUT to GND with correct polarity.', True)
                else:
                    issue(c.ref, 'regulator_stability_review', 'Verify the output capacitor capacitance and ESR against the datasheet.')
        if spec.get('input_family') == 'CMOS':
            floating = [f'{pin} ({spec["pin_labels"][pin]})' for pin, role in spec['pins'].items()
                        if role == 'input' and f'{c.ref}.{pin}' not in pin_net]
            if floating:
                issue(c.ref, 'floating_cmos_input', 'Give these CMOS inputs a defined logic level: '+', '.join(floating))
        if c.part in ('servo_generic','relay_spdt','dc_motor','lcd1602_i2c_5v','ssd1306_i2c_3v3','capacitor_polarized','pnp','pmos','fuse'):
            issue(c.ref,'rating_review','Verify exact module pinout, voltage, current, polarity and interface requirements against its datasheet')
        if c.part in design.custom_parts: issue(c.ref,'custom_unverified','Custom symbol: verify pinout and voltage limits against the datasheet')
        if not c.value and c.part in ('resistor','capacitor','capacitor_polarized','inductor','potentiometer','dc_source','fuse'): issue(c.ref,'missing_value','Specify the component value',True)
        connected=[pin_net[f'{c.ref}.{p}'] for p in spec['pins'] if f'{c.ref}.{p}' in pin_net]
        if len(spec['pins'])==2 and len(connected)==2 and len(set(connected))==1: issue(c.ref,'shorted_component','Both terminals are on the same net',True)
        if c.part in ('led','lcd1602'): issue(c.ref,'current_limit_review','Verify LED/backlight current limiting and module-specific ratings')
        if c.part=='dc_source' and (voltage(c.value) is None or not 0<voltage(c.value)<=24): issue(c.ref,'supply_range','Use an explicit DC supply between 0 and 24 V',True)
    # Reference-mode LCD checks: RW must share the LCD ground in write-only mode.
    for c in design.components:
        if c.part in {'lcd1602','lm016l'}:
            g=pin_net.get(f'{c.ref}.1')
            rw=pin_net.get(f'{c.ref}.5')
            if g is not None and rw is not None and g!=rw:
                issue(c.ref,'lcd_rw_ground','This write-only LCD definition requires RW connected to VSS',True)
            for pin in ('15','16') if c.part=='lcd1602' else ():
                if f'{c.ref}.{pin}' not in pin_net:
                    issue(c.ref,'lcd_backlight_unconnected','Backlight terminal unconnected; display illumination is not assured')
        if c.part=='servo_generic':
            sig=pin_net.get(f'{c.ref}.SIG')
            if sig is not None and sig in (pin_net.get(f'{c.ref}.VCC'),pin_net.get(f'{c.ref}.GND')):
                issue(c.ref,'servo_signal_rail','Servo signal is tied directly to its power or ground rail',True)
    for n in design.nets:
        info=[]
        for p in n.pins:
            ref,pin=p.split('.'); c=refs[ref]; spec=catalog[c.part]
            info.append((ref,pin,spec['pins'][pin],spec))
        members={r for r,_,_,_ in info}; first=next(iter(members))
        for r in members-{first}: graph[first].add(r); graph[r].add(first)
        roles=[i[2] for i in info]
        sinks = [(r, p) for r, p, _, spec in info if p in spec.get('open_collector', ())]
        driven = roles.count('output')-len(sinks)
        if 'power_out' in roles and 'ground' in roles: issue(n.name,'power_short','Supply output and ground are directly connected',True)
        if driven>1: issue(n.name,'output_conflict','Multiple driven outputs share this net',True)
        if sinks and (driven or 'power_out' in roles):
            issue(n.name, 'open_collector_conflict', 'Open-collector output shares a net with a driven output or direct supply', True)
        if roles.count('power_out')>1: issue(n.name,'multiple_supplies','Multiple supply outputs share this net; isolation is not modeled',True)
        sources=[voltage(refs[r].value) for r,p,role,s in info if refs[r].part=='dc_source' and p=='+']
        for r,p,role,s in info:
            if s.get('input_family') == 'CMOS' and role == 'output' and {'power_out', 'ground'}.intersection(roles):
                issue(n.name, 'logic_output_on_rail', f'{r}.{p}: push-pull output is tied directly to a supply or ground', True)
            if role=='power_in' and (return_pin := s.get('supply_return')):
                return_net = pin_net.get(f'{r}.{return_pin}')
                if return_net is not None:
                    low, high = s['supply_range']
                    span = source_pairs.get((n.name, return_net), ())
                    if return_net==n.name or (return_net, n.name) in source_pairs:
                        issue(n.name, 'supply_polarity', f'{r}.{p} and {r}.{return_pin}: shorted or reversed supply pins', True)
                    elif any(not low<=value<=high for value in span):
                        issue(n.name, 'voltage_mismatch', f'{r}.{p} requires {low:g}–{high:g} V above {r}.{return_pin}', True)
                    elif not span:
                        issue(n.name, 'unverified_supply', f'{r}.{p}: verify voltage across both supply pins')
                continue
            if role=='power_in' and not sources:
                issue(n.name,'unverified_supply',f'{r}.{p}: supply voltage is not directly traceable to a DC source')
            if role=='power_in' and (limits := s.get('supply_range')):
                low, high = limits
                if any(v is not None and not low<=v<=high for v in sources):
                    issue(n.name,'voltage_mismatch',f'{r}.{p} requires {low:g}–{high:g} V',True)
            if role=='power_in' and s.get('voltage') and sources:
                if any(v is not None and abs(v-s['voltage'])>0.1 for v in sources): issue(n.name,'voltage_mismatch',f'{r} requires {s["voltage"]:g} V on this power pin',True)
    seen=set(); groups=[]
    for ref in graph:
        if ref in seen: continue
        group=set(); todo=[ref]
        while todo:
            node=todo.pop()
            if node in group: continue
            group.add(node); todo.extend(graph[node]-group)
        seen.update(group); groups.append(sorted(group))
    if len(groups)>1: issue('design','disconnected_groups',f'{len(groups)} disconnected circuit groups')
    if not any(c.part=='dc_source' for c in design.components): issue('design','no_supply','No explicit DC source; power delivery has not been checked')
    return dict(status='draft_with_errors' if errors else 'draft_checks_passed',errors=errors,warnings=warnings,
                connectivity_groups=groups,simulation='not_run',hardware_verified=False,
                scope='Pin existence, net uniqueness, required pins, basic shorts, direct supply voltage and fixed output conflicts only')
