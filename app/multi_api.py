"""V2 prompt-to-netlist and editable-render endpoints."""
import base64
import json
import os
import re
import secrets
from pathlib import Path
from typing import Literal
import resvg_py
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import Field
from starlette.concurrency import run_in_threadpool
from app.catalog import CATALOG
from app.circuitlm import draft_local
from app.design import Design, Strict, check_design
from app.design_examples import EXAMPLES, led_bank
from app.route_repair import render_repaired, route_names

router=APIRouter()

def authenticate(x_api_key: str | None=Header(default=None)):
    key=os.getenv('CIRCUIT_API_KEY')
    if key and not secrets.compare_digest(x_api_key or '',key): raise HTTPException(401,'Invalid API key')

class RenderRequest(Strict):
    design: Design
    image_format: Literal['svg','png']='svg'

class DraftRequest(Strict):
    prompt: str=Field(min_length=3,max_length=12000)
    parser: Literal['builtin','local']='builtin'
    previous_design: Design | None=None

class ModelProposal(Strict):
    design: Design | None
    unresolved: list[str]=Field(max_length=50)
    explanation: str=Field(max_length=2000)


def builtin_design(prompt):
    clean=prompt.strip().lower().rstrip('.')
    if clean in {'arduino uno with a 16x2 lcd','arduino uno + 16x2 lcd','controller_lcd','create an arduino uno with a 16x2 lcd'}:
        return EXAMPLES['controller_lcd']()
    if clean=='two-stage rc filter': return EXAMPLES['rc_ladder']()
    if clean in EXAMPLES: return EXAMPLES[clean]()
    if clean in {'5v led with 330 ohm resistor','three component led circuit'}: return led_bank(1)
    match=re.fullmatch(r'(?:create )?(\d{1,2})[- ](?:channel )?led bank',clean)
    if match:
        count=int(match[1])
        if not 1<=count<=64: raise ValueError('LED bank supports 1–64 channels')
        return led_bank(count)
    # Explicit connection language accommodates arbitrary combinations without
    # silently inventing pin assignments or ignoring unrecognized prose.
    components=[];nets=[];title='Custom circuit draft'
    for number,line in enumerate(prompt.splitlines(),1):
        line=line.strip()
        if not line or line.startswith('#'): continue
        fields=line.split(maxsplit=3)
        if fields[0].lower()=='component' and len(fields)>=3:
            components.append(dict(ref=fields[1],part=fields[2],value=fields[3] if len(fields)==4 else ''))
        elif fields[0].lower()=='net' and len(fields)>=3:
            tail=line.split(maxsplit=2)[2]
            nets.append(dict(name=fields[1],pins=re.split(r'[,\s]+',tail.strip())))
        elif line.lower().startswith('title '): title=line[6:]
        else: raise ValueError(f'Line {number} needs clarification. Built-in mode accepts the exact example prompts or component/net lines. Select AI mode for free-form requests; no unrecognized components have been dropped.')
    return Design(title=title,components=components,nets=nets)

async def ai_design(req):
    return draft_local(req.prompt, req.previous_design)

def result_for(design,image_format='svg'):
    validation=check_design(design)
    svg,boxes,size,routing_audit=render_repaired(design,validation)
    # Persist positions to make drag/edit/import round trips deterministic.
    data=design.model_dump(exclude_none=True)
    for c in data['components']:
        x,y,_,_=boxes[c['ref']];c['position']={'x':x,'y':y}
    image={'mime_type':'image/svg+xml','svg':svg}
    if image_format=='png':
        zoom=min(2,4096/max(size))
        png=resvg_py.svg_to_bytes(svg_string=svg,zoom=zoom,font_files=[str(Path(__file__).with_name('fonts')/'SchematicSans.ttf')])
        image={'mime_type':'image/png','base64':base64.b64encode(png).decode()}
    return dict(schema_version='2.0',design=data,validation=validation,image=image,
                routing='Continuous wire routes where feasible; matching labels connect unrouted nets. Interior wire crossings connect only at junction dots.',
                routing_audit=routing_audit,
                routed_nets=sorted(route_names(svg)),
                unrouted_nets=sorted(set(n.name for n in design.nets)-route_names(svg)),
                bill_of_materials=[dict(ref=c.ref,part=c.part,value=c.value) for c in design.components])

@router.get('/studio',response_class=HTMLResponse)
def studio(): return Path(__file__).with_name('studio.html').read_text()

@router.get('/v2/catalog')
def catalog():
    return dict(version='0.4.0',parts=CATALOG,limits=dict(components=200,nets=1000,custom_parts=100,pins_per_custom_part=64),
                ai_configured=True,
                notes='Definitions with pin_labels use the cited package pin numbers. Generic symbols use logical terminal names.')

@router.get('/v2/examples')
def examples(): return {k:f().model_dump(exclude_none=True) for k,f in EXAMPLES.items()}

@router.post('/v2/render',dependencies=[Depends(authenticate)])
async def render(req:RenderRequest): return await run_in_threadpool(result_for,req.design,req.image_format)

@router.post('/v2/validate',dependencies=[Depends(authenticate)])
def validate(design:Design): return check_design(design)

@router.post('/v2/draft',dependencies=[Depends(authenticate)])
async def draft(req:DraftRequest):
    if req.parser=='builtin' and req.previous_design:
        raise HTTPException(422,'Use AI mode to revise an existing design with prose, or edit the component/net tables directly.')
    try: design=await ai_design(req) if req.parser=='local' else builtin_design(req.prompt)
    except ValueError as exc: raise HTTPException(422,str(exc))
    result=await run_in_threadpool(result_for,design)
    result['parser']=req.parser
    result['validation']['prompt_interpretation_requires_review']=True
    return result
