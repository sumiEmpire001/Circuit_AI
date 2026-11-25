"""Try alternative net orders and remove conflicting visible routes, not electrical nets."""
from html import unescape
import re
from collections import Counter
from app.multi_render import render_design
from app.route_guard import audit_routes
from app.route_search import route_grid, route_parallel_led

def route_names(svg):
    return {unescape(n) for n in re.findall(r'data-route-net="([^"]+)"',svg)}

def remove_routes(svg,names):
    return re.sub(r'<(?:path|circle)\b[^>]*\bdata-(?:route|junction)-net="([^"]+)"[^>]*/>',lambda m:'' if unescape(m[1]) in names else m[0],svg)

def compact_net_labels(svg, continuous):
    """A physically complete wire needs one label. Preserve fallback labels."""
    complete=set(continuous)
    labeled=set()

    def retain(match):
        net=unescape(match[1])
        if net in labeled:
            return ''
        if net in complete:
            labeled.add(net)
        return match[0]

    return re.sub(r'<text\b[^>]*\bdata-label-net="([^"]+)"[^>]*>[^<]*</text>',retain,svg)


AUDIT_SCOPE = ('Cross-net overlaps, endpoint contacts, junctions and visible pin-to-pin continuity. '
               'Undotted interior crossings are separate nets.')

def render_repaired(design,validation):
    nets=list(design.nets)
    orders=[nets,list(reversed(nets)),sorted(nets,key=lambda n:(-len(n.pins),n.name)),sorted(nets,key=lambda n:(len(n.pins),n.name))]
    if sum(len(n.pins) for n in nets)>150: orders=orders[:1]
    best=None
    seen=set()
    attempts=0
    repeated=route_parallel_led(design,validation)
    if repeated is not None:
        svg,boxes,size=repeated
        audit=audit_routes(svg)
        attempts+=1
        if audit['passed'] and len(audit['continuous_nets'])==len(nets):
            audit.update(attempts=attempts,removed_routes=[],initial_conflicts=0,scope=AUDIT_SCOPE)
            return compact_net_labels(svg,audit['continuous_nets']),boxes,size,audit
    grid=route_grid(design,validation)
    if grid is not None:
        for allow_crossings,rails_first in ((False,False),(True,False),(True,True)):
            svg,boxes,size=route_grid(design,validation,allow_crossings=True,rails_first=rails_first) if allow_crossings else grid
            audit=audit_routes(svg)
            attempts+=1
            if audit['passed']:
                score=(len(audit['continuous_nets']),len(route_names(svg)),0,0,-audit['undotted_crossings'],-size[1])
                if best is None or score>best[0]:
                    best=(score,svg,boxes,size,audit,[],0)
            if best is not None and best[0][0]==len(nets) and best[4]['undotted_crossings']==0:
                break
    for order in orders[:1] if grid is not None else orders:
        if best is not None and best[0][0]==len(nets) and best[0][1]==len(nets): break
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
        score=(len(audit['continuous_nets']),coverage,-len(removed),-initial,-audit['undotted_crossings'],-size[1])
        if best is None or score>best[0]:
            best=(score,svg,boxes,size,audit,sorted(removed),initial)
        if coverage==len(nets) and len(audit['continuous_nets'])==len(nets): break
    _,svg,boxes,size,audit,removed,initial=best
    audit.update(attempts=attempts,removed_routes=removed,initial_conflicts=initial,scope=AUDIT_SCOPE)
    return compact_net_labels(svg,audit['continuous_nets']),boxes,size,audit
