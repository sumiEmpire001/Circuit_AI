"""Try alternative net orders and remove conflicting visible routes, not electrical nets."""
from html import unescape
import re
from collections import Counter
from app.multi_render import render_design
from app.route_guard import audit_routes

def route_names(svg):
    return {unescape(n) for n in re.findall(r'data-route-net="([^"]+)"',svg)}

def remove_routes(svg,names):
    return re.sub(r'<(?:path|circle)\b[^>]*\bdata-(?:route|junction)-net="([^"]+)"[^>]*/>',lambda m:'' if unescape(m[1]) in names else m[0],svg)

def render_repaired(design,validation):
    nets=list(design.nets)
    orders=[nets,list(reversed(nets)),sorted(nets,key=lambda n:(-len(n.pins),n.name)),sorted(nets,key=lambda n:(len(n.pins),n.name))]
    if sum(len(n.pins) for n in nets)>150: orders=orders[:1]
    best=None
    seen=set()
    attempts=0
    for order in orders:
        key=tuple(n.name for n in order)
        if key in seen: continue
        seen.add(key)
        attempts+=1
        svg,boxes,size=render_design(design,validation,route_order=order)
        audit=audit_routes(svg)
        initial=len(audit['conflicts'])
        removed=set()
        while audit['conflicts']:
            counts=Counter(n for conflict in audit['conflicts'] for n in conflict['nets'])
            victim=max(counts,key=lambda n:(counts[n],n))
            removed.add(victim)
            svg=remove_routes(svg,{victim})
            audit=audit_routes(svg)
        coverage=len(route_names(svg))
        score=(coverage,-len(removed),-initial,-size[1])
        if best is None or score>best[0]:
            best=(score,svg,boxes,size,audit,sorted(removed),initial)
        if coverage==len(nets): break
    _,svg,boxes,size,audit,removed,initial=best
    audit.update(attempts=attempts,removed_routes=removed,initial_conflicts=initial,scope='Visible route segments only; not electrical simulation or continuity proof')
    return svg,boxes,size,audit
