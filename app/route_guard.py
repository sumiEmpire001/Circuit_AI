"""Audit emitted route geometry, independently of the routing algorithm."""
import re
import xml.etree.ElementTree as ET

def audit_routes(svg):
    root=ET.fromstring(svg)
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
            if hit: conflicts.append({'nets':sorted([n,m]),'reason':'visible cross-net contact'})
    return {'segments':len(segments),'conflicts':conflicts,'passed':not conflicts}
