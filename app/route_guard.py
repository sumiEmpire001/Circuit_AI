"""Audit emitted route geometry, independently of the routing algorithm."""
from collections import defaultdict
import re
import xml.etree.ElementTree as ET

def audit_routes(svg):
    root=ET.fromstring(svg)
    dot_style = root.get('data-crossing-style') == 'junction-dot'
    junctions = {(float(node.get('cx')),float(node.get('cy')))
                 for node in root.iter() if node.get('data-junction-net')}
    segments=[]
    for node in root.iter():
        net=node.get('data-route-net')
        if net is None: continue
        x=y=None
        for cmd,a,b in re.findall(r'(M|H|V)\s+(-?\d+(?:\.\d+)?)(?:\s+(-?\d+(?:\.\d+)?))?',node.get('d','')):
            a=float(a)
            if cmd=='M': x,y=a,float(b);continue
            nx,ny=(a,y) if cmd=='H' else (x,a)
            if (x,y)!=(nx,ny): segments.append((net,x,y,nx,ny))
            x,y=nx,ny
    conflicts=[]
    crossings=set()
    for i,(n,x,y,u,v) in enumerate(segments):
        for m,a,b,c,d in segments[i+1:]:
            if n==m: continue
            if y==v and b==d:
                hit=y==b and max(min(x,u),min(a,c))<=min(max(x,u),max(a,c))
            elif x==u and a==c:
                hit=x==a and max(min(y,v),min(b,d))<=min(max(y,v),max(b,d))
            else:
                if x==u: hx,hy,hu,vy,vx,vv=a,b,c,y,x,v
                else: hx,hy,hu,vy,vx,vv=x,y,u,b,a,d
                hit=min(hx,hu)<=vx<=max(hx,hu) and min(vy,vv)<=hy<=max(vy,vv)
                if (dot_style and min(hx,hu)<vx<max(hx,hu)
                        and min(vy,vv)<hy<max(vy,vv) and (vx,hy) not in junctions):
                    crossings.add((vx,hy))
                    hit=False
            if hit: conflicts.append({'nets':sorted([n,m]),'reason':'visible cross-net contact'})
    # Strict geometric continuity: a visual gap is not a connected segment.
    # This deliberately distinguishes bridged crossings from uninterrupted paths.
    groups=defaultdict(list)
    terminals=defaultdict(list)
    for n,x,y,u,v in segments: groups[n].append((x,y,u,v))
    for node in root.iter():
        if node.get('data-pin') and node.get('data-net'):
            terminals[node.get('data-net')].append((node.get('data-pin'),float(node.get('cx')),float(node.get('cy'))))
    def touches(a,b):
        x,y,u,v=a; p,q,r,s=b
        return max(min(x,u),min(p,r))<=min(max(x,u),max(p,r)) and max(min(y,v),min(q,s))<=min(max(y,v),max(q,s))
    continuous=[]; interrupted=[]; label_only=[]
    for name,pins in terminals.items():
        lines=groups[name]
        if not lines: label_only.append(name);continue
        seen={0}; stack=[0]
        while stack:
            i=stack.pop()
            for j,b in enumerate(lines):
                if j not in seen and touches(lines[i],b):
                    seen.add(j);stack.append(j)
        missing=[ref for ref,x,y in pins if not any(touches(lines[i],(x,y,x,y)) for i in seen)]
        if missing or len(seen)!=len(lines): interrupted.append({'net':name,'unreached_pins':missing,'disconnected_segments':len(lines)-len(seen)})
        else: continuous.append(name)
    return {'segments':len(segments),'undotted_crossings':len(crossings),'conflicts':conflicts,'passed':not conflicts,
            'continuous_nets':sorted(continuous),'interrupted_nets':interrupted,'label_only_nets':sorted(label_only)}
