"""SVG schematic renderer. Shared net labels are electrical connections.
Only unobstructed facing pins receive direct wires; other nets use explicit labels.
"""
from collections import defaultdict
from html import escape
from app.catalog import LCD_LABELS
from app.parallel_led import bank_placement

def passive_loop_placement(design, nets_by_pin):
    """Align the output terminals of a three-part passive loop."""
    if len(design.components)!=3 or len(design.nets)!=3 or any(c.position for c in design.components):
        return {}
    source = next((c for c in design.components if c.part=='dc_source'), None)
    if source is None:
        return {}
    passive = {c.ref:c for c in design.components if c.part in {'resistor','capacitor'}}
    if len(passive)!=2 or not any(c.part=='resistor' for c in passive.values()):
        return {}
    rails = [nets_by_pin.get(f'{source.ref}.{pin}') for pin in ('+','-')]
    if rails[0] is rails[1] or any(net is None or len(net.pins)!=2 for net in rails):
        return {}
    series, shunt = (next(pin for pin in net.pins if not pin.startswith(source.ref+'.')) for net in rails)
    a, b = series.removesuffix('.1'), shunt.removesuffix('.2')
    if {a,b}!=passive.keys() or a==b:
        return {}
    if {frozenset(net.pins) for net in design.nets} != {
        frozenset((f'{source.ref}.+',series)),
        frozenset((f'{a}.2',f'{b}.1')),
        frozenset((f'{source.ref}.-',shunt)),
    }:
        return {}
    return {a:(210,130), b:(560,130), source.ref:(385,310)}


def signal_placement(design, catalog):
    """Place a directed signal chain in columns, with shared support below it."""
    if len(design.components)>12 or any(c.position for c in design.components):
        return {}
    specs={c.ref:catalog[c.part] for c in design.components}
    loads={c.ref for c in design.components if c.part in {'dc_motor','servo_generic'}}
    followers=defaultdict(set)
    incoming=defaultdict(set)
    groups=defaultdict(set)
    for net in design.nets:
        pins=[p.split('.') for p in net.pins]
        roles={specs[ref]['pins'][pin] for ref,pin in pins}
        if {'ground','power_out','power_in'} & roles:
            if 'power_out' in roles:
                refs={ref for ref,_ in pins}
                for ref in refs:
                    groups[ref].update(refs-{ref})
            continue
        drivers=[ref for ref,pin in pins if specs[ref]['pins'][pin] in {'output','bidirectional'}]
        if len(drivers)!=1:
            continue
        driver=drivers[0]
        for ref,pin in pins:
            if ref!=driver and (ref in loads or specs[ref]['pins'][pin]=='input'):
                followers[driver].add(ref)
                incoming[ref].add(driver)
    ranks={ref:0 for ref in followers if ref not in incoming}
    pending=set(incoming)
    while ready := {ref for ref in pending if incoming[ref]<=ranks.keys()}:
        for ref in sorted(ready):
            ranks[ref]=1+max(ranks[parent] for parent in incoming[ref])
        pending-=ready
    if pending or max(ranks.values(),default=0)<2:
        return {}
    columns=defaultdict(list)
    for ref in sorted(ranks):
        columns[ranks[ref]].append(ref)
    if any(len(refs)>1 for refs in columns.values()):
        return {}
    positions={ref:(210+rank*540,130) for rank,refs in columns.items() for ref in refs}
    below=defaultdict(int)
    for ref in sorted(specs.keys()-ranks.keys()):
        neighbors=sorted(ranks[other] for other in groups[ref] if other in ranks)
        col=neighbors[len(neighbors)//2] if neighbors else 0
        positions[ref]=(210+col*540,650+below[col]*250)
        below[col]+=1
    return positions


def layout(design):
    catalog=design.catalog(); boxes={}; points={}
    cols=min(2 if len(design.components)<=12 else 3,len(design.components))
    row_tops={0:130}
    nets_by_pin={pin:net for net in design.nets for pin in net.pins}
    adc_interrupts={f'{c.ref}.5' for c in design.components if c.part=='adc0804lcn'}
    adc_ports={pin for terminal in adc_interrupts if terminal in nets_by_pin
               for pin in nets_by_pin[terminal].pins}
    compact=bank_placement(design) or passive_loop_placement(design,nets_by_pin) or signal_placement(design,catalog)
    # Recognize the actual series-loop topology rather than the prompt title.
    bypart={c.part:c.ref for c in design.components}
    if len(design.components)==3 and set(bypart)=={'dc_source','resistor','led'}:
        v,r,d=(bypart[k] for k in ('dc_source','resistor','led'))
        expected={frozenset((v+'.+',r+'.1')),frozenset((r+'.2',d+'.A')),frozenset((d+'.K',v+'.-'))}
        if {frozenset(n.pins) for n in design.nets}==expected:
            compact={r:(210,130),d:(610,130),v:(410,370)}
    for index,c in enumerate(design.components):
        spec=catalog[c.part]; pins=list(spec['pins'])
        # Stable placement, serialized in the returned design for subsequent edits.
        x=c.position.x if c.position else compact.get(c.ref,(210+(index%cols)*620,0))[0]
        row=index//cols
        y=c.position.y if c.position else compact.get(c.ref,(0,row_tops.get(row,130)))[1]
        if c.part=='arduino_uno':
            left=['5V','GND']+[f'A{i}' for i in range(6)]
            right=['D12','D11','D5','D4','D3','D2']+[f'D{i}' for i in [0,1,6,7,8,9,10,13]]
        elif c.part=='at89c51_pdip40' and f'{c.ref}.12' in adc_ports:
            right=[*map(str,range(21,29)),'17','16','12',*map(str,range(1,9))]
            left=[p for p in ['40','19','18','9','31','20',*pins] if p not in right]
            left=list(dict.fromkeys(left))
        elif c.part=='adc0804lcn':
            left=[*map(str,range(18,10,-1)),'2','3','5']
            right=['6','7','4','19','9','1','8','10','20']
        elif c.part=='at89c51_pdip40':
            left=['40','19','18','9','31','20','29','30',*map(str,range(32,40)),*map(str,range(10,18))]
            right=[*map(str,range(1,9)),'22','23','21',*map(str,range(24,29))]
        elif c.part=='lm016l':
            left=[*map(str,range(7,15)),'4','6','1','2','3','5']
            right=[]
        elif c.part=='lcd1602':
            left=['4','6','11','12','13','14','1','2','3','5']; right=['7','8','9','10','15','16']
        elif c.part=='uln2003a': left=[f'IN{i}' for i in range(1,8)]+['E']; right=[f'OUT{i}' for i in range(1,8)]+['COM']
        elif c.part=='l293d': left=['EN12','IN1','IN2','VCC1','VCC2','EN34','IN3','IN4','GND1','GND2','GND3','GND4']; right=['OUT1','OUT2','OUT3','OUT4']
        elif c.part=='lm35': left=['VS','GND']; right=['VOUT']
        elif spec.get('pin_labels'):
            left=[p for role in ('input','power_in','ground','passive','bidirectional') for p in pins if spec['pins'][p]==role]
            right=[p for p in pins if p not in left]
        elif spec['symbol']=='pot': left=['1','W']; right=['2']
        elif c.part=='npn': left=['B']; right=['C','E']
        elif c.part=='nmos': left=['G']; right=['D','S']
        elif len(pins)==2: left=pins[:1];right=pins[1:]
        else: left=pins[:(len(pins)+1)//2];right=pins[(len(pins)+1)//2:]
        h=max(110,70+max(len(left),len(right))*22);w=230
        if spec['symbol']=='lcd': w=340; h+=48
        boxes[c.ref]=(x,y,w,h)
        row_tops[row+1]=max(row_tops.get(row+1,0),y+h+140)
        for side,ps in [('left',left),('right',right)]:
            for i,pin in enumerate(ps):
                points[f'{c.ref}.{pin}']=(x-28 if side=='left' else x+w+28,y+(118 if spec['symbol']=='lcd' else 70)+i*22,side)
    # Swap the entire glyph and its two endpoints when the neighboring nets
    # predominantly approach from the opposite sides.
    for c in design.components:
        output=nets_by_pin.get(f'{c.ref}.VOUT')
        if c.part!='lm35' or output is None:
            continue
        x,_,w,_=boxes[c.ref]
        sinks={terminal.split('.')[0] for terminal in output.pins if not terminal.startswith(c.ref+'.')}
        if sinks and all(boxes[ref][0]+boxes[ref][2]<x for ref in sinks):
            for pin in catalog[c.part]['pins']:
                qualified=f'{c.ref}.{pin}'
                px,py,side=points[qualified]
                points[qualified]=(2*x+w-px,py,'right' if side=='left' else 'left')
    for c in design.components:
        pins=list(catalog[c.part]['pins'])
        if len(pins)!=2:
            continue
        first,second=(f'{c.ref}.{pin}' for pin in pins)
        if first not in nets_by_pin or second not in nets_by_pin:
            continue
        x,_,w,_=boxes[c.ref]
        def side_preference(terminal):
            neighbors=[boxes[p.split('.')[0]] for p in nets_by_pin[terminal].pins if not p.startswith(c.ref+'.')]
            if not neighbors:
                return 0
            return sum((nx+nw/2>x+w/2)-(nx+nw/2<x+w/2) for nx,_,nw,_ in neighbors)/len(neighbors)
        if side_preference(first)>side_preference(second):
            points[first],points[second]=points[second],points[first]
    return boxes,points

def render_design(design,validation,route_order=None):
    cat=design.catalog();boxes,points=layout(design)
    width=max(x+w+200 for x,y,w,h in boxes.values());height=max(y+h+100 for x,y,w,h in boxes.values())
    width=max(width,900);height=max(height,450)
    parts=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title" data-crossing-style="junction-dot">
<title id="title">{escape(design.title)}</title>
<defs><pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="#c4c8ad" stroke-width="0.5"/></pattern></defs>
<rect width="100%" height="100%" fill="#eeeedb"/><rect width="100%" height="100%" fill="url(#grid)"/>
<style>text{{font-family:DejaVu Sans,sans-serif;fill:#303d2b;font-size:12px}}.wire{{fill:none;stroke:#285b36;stroke-width:1.7}}.symbol{{fill:none;stroke:#874d3d;stroke-width:2}}.label{{font-size:11px;fill:#285b36}}.pin{{font-size:10px;fill:#874d3d}}.component{{cursor:move}}</style>
<text x="30" y="30" style="font-size:20px">{escape(design.title)}</text>
<text x="30" y="54">DRAFT • {len(validation['errors'])} ERC errors • Not simulated • Matching net labels are connected; crossings without junction dots are not connected</text>''']
    def line(d,cls='symbol',attrs=''):
        parts.append(f'<path d="{d}" class="{cls}" {attrs}/>')
    def text(x,y,s,cls='',anchor='start',attrs=''):
        parts.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" {attrs}>{escape(str(s))}</text>')
    # Route each net on its own horizontal bus below all component bodies.
    # Vertical branches use unique x tracks; crossings are explicitly not junctions.
    # A branch is omitted if its escape corridor would intersect another body.
    # Such nets retain labels rather than displaying a misleading partial wire.
    routes=[]
    occupied=set()
    horizontal=[]
    vertical=[]
    pin_positions={(p[0],p[1]) for p in points.values()}
    for index,net in enumerate(design.nets if route_order is None else route_order):
        bus=height+40+index*24
        branches=[]
        for pin in net.pins:
            px,py,side=points[pin]
            direction=-1 if side=='left' else 1
            chosen=None
            for offset in range(12,181,8):
                tx=px+direction*offset
                if tx<20 or tx>width-20 or tx in occupied or any(t==tx for _,_,t in branches): continue
                if any(tx==qx and qy>=py for qx,qy in pin_positions): continue
                if any(min(px,tx)<=vx<=max(px,tx) and vy<=py<=vb and (vx in (px,tx) or py in (vy,vb)) for vx,vy,vb in vertical): continue
                if any(lo<=tx<=hi and py<=hy<=bus and (tx in (lo,hi) or hy==py) for hy,lo,hi in horizontal): continue
                if any(py==by and min(px,tx)<=max(bp,bt) and max(px,tx)>=min(bp,bt) for bp,by,bt in branches): continue
                if any(py==hy and min(px,tx)<=hi and max(px,tx)>=lo for hy,lo,hi in horizontal): continue
                if any(min(px,tx)<x+w+5 and max(px,tx)>x-5 and y-5<=py<=y+h+5 for x,y,w,h in boxes.values()): continue
                if any(x-5<=tx<=x+w+5 and y+h+5>=py for x,y,w,h in boxes.values()): continue
                chosen=tx;break
            if chosen is None: break
            branches.append((px,py,chosen))
        if len(branches)!=len(net.pins): continue
        occupied.update(t for _,_,t in branches)
        horizontal.extend((py,min(px,t),max(px,t)) for px,py,t in branches)
        vertical.extend((t,py,bus) for px,py,t in branches)
        routes.append((net.name,bus,branches))
    for name,bus,branches in routes:
        attrs=f'data-route-net="{escape(name)}"'
        xs=[t for _,_,t in branches]
        line(f'M {min(xs)} {bus} H {max(xs)}','wire',attrs)
        for px,py,tx in branches:
            line(f'M {px} {py} H {tx}','wire',attrs)
            line(f'M {tx} {py} V {bus}','wire',attrs)
            if min(xs)<tx<max(xs):
                parts.append(f'<circle cx="{tx}" cy="{bus}" r="3.5" fill="#285b36" data-junction-net="{escape(name)}"/>')
    # Extend canvas to include buses; preserve component positions.
    if routes:
        newheight=max(bus for _,bus,_ in routes)+65
        parts[0]=parts[0].replace(f'height="{height}" viewBox="0 0 {width} {height}"',f'height="{newheight}" viewBox="0 0 {width} {newheight}"')
        height=newheight
    pin_net={p:n.name for n in design.nets for p in n.pins}
    for c in design.components:
        x,y,w,h=boxes[c.ref]; spec=cat[c.part]; kind=spec['symbol'];cy=y+70
        parts.append(f'<g class="component" data-ref="{c.ref}" data-x="{x}" data-y="{y}" data-width="{w}" data-height="{h}">')
        display_part = {'lamp_bulb': 'Lamp bulb', 'dc_fan': 'DC fan'}.get(c.part, c.part)
        text(x,y-25,c.ref+' · '+display_part)
        text(x,y-7,c.value[:40])
        two=len(spec['pins'])==2
        if two:
            mirrored=points[f"{c.ref}.{next(iter(spec['pins']))}"][2]=='right'
            if mirrored:
                parts.append(f'<g transform="translate({2*x+w} 0) scale(-1 1)">')
            line(f'M {x} {cy} H {x+70} M {x+160} {cy} H {x+w}','wire')
            if kind in ('resistor','ldr','thermistor'):
                parts.append(f'<rect class="symbol" x="{x+70}" y="{cy-10}" width="90" height="20"/>')
                if kind=='ldr':
                    line(f'M {x+78} {cy-40} l 16 18 m -9 -2 l 9 2 l -1 -9 M {x+110} {cy-40} l 16 18 m -9 -2 l 9 2 l -1 -9')
                elif kind=='thermistor':
                    line(f'M {x+85} {cy+22} L {x+145} {cy-22} h 12')
            elif kind=='crystal':
                line(f'M {x+70} {cy} H {x+96} M {x+96} {cy-17} V {cy+17} M {x+134} {cy-17} V {cy+17} M {x+134} {cy} H {x+160}')
                parts.append(f'<rect class="symbol" x="{x+104}" y="{cy-14}" width="22" height="28"/>')
            elif kind=='capacitor':
                line(f'M {x+70} {cy} H {x+105} M {x+105} {cy-20} V {cy+20} M {x+125} {cy-20} V {cy+20} M {x+125} {cy} H {x+160}')
            elif kind in ('led','diode'):
                line(f'M {x+70} {cy} H {x+95} M {x+95} {cy-16} V {cy+16} L {x+128} {cy} Z M {x+130} {cy-16} V {cy+16} M {x+130} {cy} H {x+160}')
                if kind=='led': line(f'M {x+115} {cy-25} l 16 -16 m -7 0 h 7 v 7 M {x+136} {cy-25} l 16 -16 m -7 0 h 7 v 7')
            elif kind=='source':
                parts.append(f'<circle class="symbol" cx="{x+115}" cy="{cy}" r="25"/>')
                line(f'M {x+70} {cy} H {x+90} M {x+140} {cy} H {x+160} M {x+98} {cy} h 10 m -5 -5 v 10 M {x+123} {cy} h 10')
            elif kind=='switch': line(f'M {x+70} {cy} H {x+90} L {x+140} {cy-25} M {x+140} {cy} H {x+160}')
            elif kind=='lamp':
                parts.append(f'<circle class="symbol" cx="{x+115}" cy="{cy}" r="24"/>')
                line(f'M {x+70} {cy} H {x+91} M {x+139} {cy} H {x+160} M {x+99} {cy-16} L {x+131} {cy+16} M {x+99} {cy+16} L {x+131} {cy-16}')
            elif kind=='motor':
                parts.append(f'<circle class="symbol" cx="{x+115}" cy="{cy}" r="24"/>')
                line(f'M {x+70} {cy} H {x+91} M {x+139} {cy} H {x+160}')
            elif kind=='inductor': line(f'M {x+70} {cy} '+''.join('a 11.25 13 0 0 1 22.5 0 ' for _ in range(4)))
            else:
                parts.append(f'<rect class="symbol" x="{x+70}" y="{cy-15}" width="90" height="30"/>')
            if mirrored:
                parts.append('</g>')
            if kind=='motor':
                text(x+115,cy+4,'FAN' if c.part=='dc_fan' else 'M',anchor='middle')
            elif kind not in {'resistor','ldr','thermistor','capacitor','led','diode','source','switch','inductor','crystal','lamp'}:
                text(x+115,cy+4,spec['name'][:12],anchor='middle')
        elif kind=='pot':
            line(f'M {x} {cy} H {x+70} M {x+160} {cy} H {x+w}','wire')
            parts.append(f'<rect class="symbol" x="{x+70}" y="{cy-10}" width="90" height="20"/>')
            line(f'M {x} {cy+22} H {x+115} V {cy+10} m -5 6 l 5 -6 l 5 6')
        elif kind=='npn':
            line(f'M {x} {cy} H {x+100} M {x+100} {cy-8} V {cy+28} M {x+100} {cy+2} L {x+140} {cy-15} H {x+180} V {cy} H {x+w} M {x+100} {cy+20} L {x+140} {cy+38} H {x+180} V {cy+22} H {x+w}')
            line(f'M {x+124} {cy+23} L {x+140} {cy+38} L {x+120} {cy+37}')
        elif kind=='nmos':
            line(f'M {x} {cy} H {x+100} M {x+100} {cy-12} V {cy+33} M {x+110} {cy-12} V {cy-1} M {x+110} {cy+4} V {cy+17} M {x+110} {cy+22} V {cy+33} M {x+110} {cy-8} H {x+175} V {cy} H {x+w} M {x+110} {cy+30} H {x+175} V {cy+22} H {x+w}')
        else:
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#e4e5c7" stroke="#874d3d" stroke-width="2"/>')
            if kind=='lcd':
                parts.append(f'<rect x="{x+14}" y="{y+10}" width="{w-28}" height="92" rx="5" fill="#17694c" stroke="#315846"/>')
                for dx in (23,w-23):
                    for dy in (19,93):
                        parts.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="4" fill="#eeeedb" stroke="#c8ad62"/>')
                parts.append(f'<rect x="{x+35}" y="{y+20}" width="{w-70}" height="70" rx="3" fill="#20262c"/>')
                parts.append(f'<rect x="{x+45}" y="{y+29}" width="{w-90}" height="52" rx="2" fill="#163e99"/>')
                for row in range(2):
                    for col in range(16):
                        parts.append(f'<rect x="{x+53+col*14}" y="{y+34+row*22}" width="11" height="17" fill="#8bb8ff" opacity=".23"/>')
                parts.append(f'<text x="{x+w/2}" y="{y+47}" text-anchor="middle" style="fill:#e5f1ff;font-family:monospace">16 × 2 LCD</text>')
                parts.append(f'<text x="{x+w/2}" y="{y+69}" text-anchor="middle" style="fill:#e5f1ff;font-family:monospace">HD44780 parallel</text>')
            elif kind in {'logic_package', 'analog_package'}:
                text(x+w/2,y+23,spec['mpn'],anchor='middle')
                text(x+w/2,y+43,spec.get('logic_function') or spec['function'],anchor='middle')
            else: text(x+w/2,y+30,('Arduino Uno R3' if c.part=='arduino_uno' else spec['name'][:28]),anchor='middle')
        for pin in spec['pins']:
            px,py,side=points[f'{c.ref}.{pin}'];left=side=='left';edge=x if left else x+w
            net=pin_net.get(f'{c.ref}.{pin}')
            if pin in spec.get('active_low', ()):
                direction = -1 if left else 1
                line(f'M {px} {py} H {edge+8*direction}','wire')
                parts.append(f'<circle class="symbol" cx="{edge+4*direction}" cy="{py}" r="4" data-active-low="{c.ref}.{pin}"/>')
            else:
                line(f'M {px} {py} H {edge}','wire')
            label=pin+(' '+LCD_LABELS[pin] if c.part=='lcd1602' else ' '+spec['pin_labels'][pin] if spec.get('pin_labels') else '')
            if pin in spec.get('open_collector', ()):
                label += ' (OC)'
            if pin in spec.get('open_drain', ()):
                label += ' (OD)'
            text(edge+5 if left else edge-5,py-5,label,'pin','start' if left else 'end')
            if net:
                text(px-5 if left else px+5,py-5,net,'label','end' if left else 'start',f'data-label-net="{escape(net)}"')
                parts.append(f'<circle cx="{px}" cy="{py}" r="2.7" fill="#285b36" data-pin="{c.ref}.{pin}" data-net="{net}"/>')
            else:
                line(f'M {px-3} {py-3} l 6 6 M {px-3} {py+3} l 6 -6')
        parts.append('</g>')
    text(30,height-22,'Draft schematic. Crossed unused pins. Named nets connect across the sheet. Verify package pinouts before building.')
    parts.append('</svg>')
    return '\n'.join(parts),boxes,(width,height)
