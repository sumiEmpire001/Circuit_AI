"""Coordinate-compressed orthogonal A* router for small and medium schematics.

A complete net is committed atomically. A second search can pass
perpendicularly through the interior of a straight wire, without a junction.
"""
from collections import defaultdict
from functools import lru_cache
from heapq import heappop, heappush
from html import escape
from app.multi_render import layout, render_design
from app.parallel_led import led_branches

def find_path(start, goals, neighbors, occupied, limit=16000, extra_cost=None):
    goals=set(goals)
    def h(p):
        return min(abs(p[0]-g[0])+abs(p[1]-g[1]) for g in goals)
    queue=[(h(start),0,start)]
    distance={start:0}
    parent={}
    while queue and limit:
        limit-=1
        _,cost,p=heappop(queue)
        if cost!=distance[p]: continue
        if p in goals:
            path=[p]
            while p in parent:
                p=parent[p];path.append(p)
            return path[::-1]
        for q in neighbors(p):
            if q in occupied: continue
            new=cost+abs(p[0]-q[0])+abs(p[1]-q[1])
            if extra_cost:
                new+=extra_cost(p,q)
            if new<distance.get(q,float('inf')):
                distance[q]=new;parent[q]=p
                heappush(queue,(new+h(q),new,q))
    return None

def straight_runs(graph, axis):
    """Join grid edges into visible segments, splitting at bends and junctions."""
    for a, neighbors in graph.items():
        for b in neighbors:
            if a >= b:
                continue
            direction = axis(a, b)
            if (len(neighbors)==2 and any(c<a and axis(c,a)==direction for c in neighbors)):
                continue
            end=b
            while len(graph[end])==2:
                forward=next((c for c in graph[end] if c>end and axis(end,c)==direction),None)
                if forward is None:
                    break
                end=forward
            yield a,end


def route_parallel_led(design, validation):
    bank = led_branches(design)
    if bank is None:
        return None
    source, power, ground, branches = bank
    boxes, points = layout(design)
    # The rail construction applies only to its aligned layout, including
    # positions restored from the editor. Other placements use normal search.
    if len({boxes[r][0] for r,_,_ in branches})!=1 or len({boxes[d][0] for _,d,_ in branches})!=1:
        return None
    rows = sorted(branches, key=lambda branch: boxes[branch[0]][1])
    vr, vd = (points[f'{source}.{pin}'] for pin in ('+','-'))
    grounds = [points[f'{led}.K'] for _,led,_ in rows]
    powers = [points[f'{resistor}.1'] for resistor,_,_ in rows]
    if vr[2]!='left' or vd[2]!='right' or vr[1]>=powers[0][1]-110:
        return None
    if any(p[1]!=g[1] or p[0]>=g[0] or p[2]!='left' or g[2]!='right' for p,g in zip(powers,grounds)):
        return None
    if any(b[1]-a[1]<110 for a,b in zip(powers,powers[1:])):
        return None
    connections = [(points[f'{r}.2'],points[f'{d}.A'],net) for r,d,net in rows]
    if any(a[0]>=b[0] for a,b,_ in connections):
        return None

    def horizontal(name, x, y, end):
        return f'<path d="M {x} {y} H {end}" class="wire" data-route-net="{escape(name)}"/>'

    output = [horizontal(name,a[0],a[1],b[0]) for a,b,name in connections]
    for net, terminal, pins, direction in ((power,vr,powers,-1),(ground,vd,grounds,1)):
        x = (min if direction<0 else max)(p[0] for p in [terminal,*pins])+direction*54
        if x<10:
            return None
        name = escape(net)
        output.append(horizontal(net,terminal[0],terminal[1],x))
        output.append(f'<path d="M {x} {terminal[1]} V {pins[-1][1]}" class="wire" data-route-net="{name}"/>')
        for px,y,_ in pins:
            output.append(horizontal(net,px,y,x))
        for _,y,_ in pins[:-1]:
            output.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#285b36" data-junction-net="{name}"/>')

    svg,_,size = render_design(design,validation,route_order=[])
    svg = svg.replace('<g class="component"', '\n'.join(output)+'\n<g class="component"',1)
    return svg, boxes, size


def route_grid(design,validation,allow_crossings=False, rails_first=False):
    boxes,points=layout(design)
    if len(points)>100 or sum(len(n.pins) for n in design.nets)>56:
        return None
    svg,boxes,size=render_design(design,validation,route_order=[])
    width,height=size
    rects=[(x-27,y-5,x+w+27,y+h+5) for x,y,w,h in boxes.values()]
    terminal_dirs={(x,y):side for x,y,side in points.values()}
    if len(terminal_dirs)!=len(points): return None
    xs={20,width-20};ys={80,height-20}
    for a,b,c,d in rects:
        xs.update((a-15,c+15));ys.update((b-15,d+15))
    for x,y,side in points.values():
        direction=-1 if side=='left' else 1
        xs.update(x+direction*offset for offset in (0,4,8,12,16))
        ys.update((y,y-12,y+12))
    xs=sorted(x for x in xs if 10<=x<=width-10)
    ys=sorted(y for y in ys if 70<=y<=height-10)
    if len(xs)*len(ys)>16000: return None
    ix={x:i for i,x in enumerate(xs)};iy={y:i for i,y in enumerate(ys)}
    def legal(p,q):
        for t,other in ((p,q),(q,p)):
            side=terminal_dirs.get(t)
            if side and (t[1]!=other[1] or (other[0]-t[0])*(-1 if side=='left' else 1)<=0):
                return False
        return not any(min(p[0],q[0])<=c and max(p[0],q[0])>=a and min(p[1],q[1])<=d and max(p[1],q[1])>=b for a,b,c,d in rects)
    @lru_cache(maxsize=None)
    def neighbors(p):
        x,y=p;i,j=ix[x],iy[y]
        candidates=[]
        for a,b in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):
            if 0<=a<len(xs) and 0<=b<len(ys):
                q=(xs[a],ys[b])
                if legal(p,q): candidates.append(q)
        return tuple(candidates)
    def axis(a,b):
        return int(a[0]==b[0])

    def step(a,b):
        return abs(ix[a[0]]-ix[b[0]])+abs(iy[a[1]]-iy[b[1]])

    def expand(a,b):
        if a[0]==b[0]:
            dy=1 if b[1]>a[1] else -1
            return [(a[0],ys[j]) for j in range(iy[a[1]],iy[b[1]]+dy,dy)]
        dx=1 if b[0]>a[0] else -1
        return [(xs[i],a[1]) for i in range(ix[a[0]],ix[b[0]]+dx,dx)]

    occupied={}
    output=[]
    catalog = design.catalog()
    parts = {component.ref: catalog[component.part] for component in design.components}
    def is_supply(net):
        return any(parts[ref]['pins'][pin] in {'power_out','power_in','ground'}
                   for ref,pin in (terminal.split('.') for terminal in net.pins))

    def order(net):
        if allow_crossings and not rails_first:
            return (is_supply(net), len(net.pins), net.name)
        return (False,-len(net.pins),net.name)

    for net in sorted(design.nets,key=order):
        pins=sorted(points[p][:2] for p in net.pins)
        if len(pins)<2 or any(x not in ix or y not in iy for x,y in pins):
            continue
        blocked=set(occupied) | (set(terminal_dirs)-set(pins))
        graph=defaultdict(set)
        tree={pins[0]}
        crossed=set()
        def crossing_neighbors(p):
            for q in neighbors(p):
                direction=axis(p,q)
                previous=p
                while q in occupied and occupied[q]==1-direction and q not in crossed:
                    following=next((r for r in neighbors(q) if r!=previous and axis(q,r)==direction),None)
                    if following is None:
                        break
                    previous,q=q,following
                yield q

        for pin in pins[1:]:
            path=find_path(pin,tree,crossing_neighbors if allow_crossings else neighbors,blocked,
                           extra_cost=(lambda a,b: 45*(step(a,b)-1)) if allow_crossings else None)
            if path is None:
                break
            tree.update(path)
            for a,b in zip(path,path[1:]):
                expanded=expand(a,b)
                crossed.update(expanded[1:-1])
                for p,q in zip(expanded,expanded[1:]):
                    graph[p].add(q)
                    graph[q].add(p)
        else:
            name=escape(net.name)
            for location, adjacent in graph.items():
                directions={axis(location, other) for other in adjacent}
                can_cross=len(adjacent)==2 and len(directions)==1 and location not in terminal_dirs
                occupied[location]=next(iter(directions)) if can_cross and location not in occupied else None
            for a,b in sorted(straight_runs(graph,axis)):
                command=f'H {b[0]}' if a[1]==b[1] else f'V {b[1]}'
                output.append(f'<path d="M {a[0]} {a[1]} {command}" class="wire" data-route-net="{name}"/>')
            for (x,y),adjacent in sorted(graph.items()):
                if len(adjacent)>=3:
                    output.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#285b36" data-junction-net="{name}"/>')
    svg=svg.replace('<g class="component"', '\n'.join(output)+'\n<g class="component"',1)
    return svg,boxes,size
