"""Coordinate-compressed orthogonal A* router for small and medium schematics.

Different nets cannot share grid vertices or edges. A complete net is
committed atomically; failed nets remain label-only. No crossing bridges.
"""
from collections import defaultdict
from functools import lru_cache
from heapq import heappop, heappush
from html import escape
from app.multi_render import layout, render_design

def find_path(start, goals, neighbors, occupied, limit=16000):
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
            if new<distance.get(q,float('inf')):
                distance[q]=new;parent[q]=p
                heappush(queue,(new+h(q),new,q))
    return None

def route_grid(design,validation):
    boxes,points=layout(design)
    if len(points)>64 or sum(len(n.pins) for n in design.nets)>40:
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
        xs.update((x,x+(-12 if side=='left' else 12)));ys.update((y,y-12,y+12))
    xs=sorted(x for x in xs if 10<=x<=width-10)
    ys=sorted(y for y in ys if 70<=y<=height-10)
    if len(xs)*len(ys)>12000: return None
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
    taken=set();output=[]
    for net in sorted(design.nets,key=lambda n:(-len(n.pins),n.name)):
        pins=[points[p][:2] for p in net.pins]
        if len(pins)<2 or any(x not in ix or y not in iy for x,y in pins): continue
        blocked=taken | (set(terminal_dirs)-set(pins))
        tree={pins[0]};edges=set()
        for pin in pins[1:]:
            path=find_path(pin,tree,neighbors,blocked)
            if path is None: break
            tree.update(path)
            edges.update(tuple(sorted((a,b))) for a,b in zip(path,path[1:]))
        else:
            taken.update(tree)
            degree=defaultdict(int)
            name=escape(net.name)
            for a,b in sorted(edges):
                degree[a]+=1;degree[b]+=1
                output.append(f'<path d="M {a[0]} {a[1]} {"H "+str(b[0]) if a[1]==b[1] else "V "+str(b[1])}" class="wire" data-route-net="{name}"/>')
            for (x,y),count in sorted(degree.items()):
                if count>=3: output.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#285b36" data-junction-net="{name}"/>')
    svg=svg.replace('<g class="component"', '\n'.join(output)+'\n<g class="component"',1)
    return svg,boxes,size
