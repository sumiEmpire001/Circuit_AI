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
    errors=[]; warnings=[]
    def issue(target,code,message,error=False):
        (errors if error else warnings).append(dict(target=target,code=code,message=message))
    graph={r:set() for r in refs}
    for c in design.components:
        spec=catalog[c.part]
        for pin in spec['required']:
            if f'{c.ref}.{pin}' not in pin_net: issue(c.ref,'unconnected_required',f'{c.ref}.{pin} needs a connection',True)
        if c.part in design.custom_parts: issue(c.ref,'custom_unverified','Custom symbol: verify pinout and voltage limits against the datasheet')
        if not c.value and c.part in ('resistor','capacitor','inductor','potentiometer','dc_source'): issue(c.ref,'missing_value','Specify the component value',True)
        connected=[pin_net[f'{c.ref}.{p}'] for p in spec['pins'] if f'{c.ref}.{p}' in pin_net]
        if len(spec['pins'])==2 and len(connected)==2 and len(set(connected))==1: issue(c.ref,'shorted_component','Both terminals are on the same net',True)
        if c.part in ('led','lcd1602'): issue(c.ref,'current_limit_review','Verify LED/backlight current limiting and module-specific ratings')
        if c.part=='dc_source' and (voltage(c.value) is None or not 0<voltage(c.value)<=24): issue(c.ref,'supply_range','Use an explicit DC supply between 0 and 24 V',True)
    for n in design.nets:
        info=[]
        for p in n.pins:
            ref,pin=p.split('.'); c=refs[ref]; spec=catalog[c.part]
            info.append((ref,pin,spec['pins'][pin],spec))
        members={r for r,_,_,_ in info}; first=next(iter(members))
        for r in members-{first}: graph[first].add(r); graph[r].add(first)
        roles=[i[2] for i in info]
        if 'power_out' in roles and 'ground' in roles: issue(n.name,'power_short','Supply output and ground are directly connected',True)
        if roles.count('output')>1: issue(n.name,'output_conflict','Multiple push-pull outputs share this net',True)
        if roles.count('power_out')>1: issue(n.name,'multiple_supplies','Multiple supply outputs share this net; isolation is not modeled',True)
        sources=[voltage(refs[r].value) for r,p,role,s in info if refs[r].part=='dc_source' and p=='+']
        for r,p,role,s in info:
            if role=='power_in' and not sources:
                issue(n.name,'unverified_supply',f'{r}.{p}: supply voltage is not directly traceable to a DC source')
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
