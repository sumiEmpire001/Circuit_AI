import base64
import copy
import json
import random
import struct
import xml.etree.ElementTree as ET
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.design import Design, check_design
from app.design_examples import controller_lcd, led_bank, rc_ladder
from app.multi_render import render_design
from app.multi_api import builtin_design
client=TestClient(app)

def data(): return controller_lcd().model_dump(exclude_none=True)
def post(d,**kw): return client.post('/v2/render',json={'design':d,**kw})

def test_controller_real_pin_mapping():
    r=post(data());assert r.status_code==200
    d=r.json();assert not d['validation']['errors']
    nets={n['name']:n['pins'] for n in d['design']['nets']}
    assert nets['RS']==['U1.D12','LCD1.4']
    assert nets['DATA7']==['U1.D2','LCD1.14']
    assert 'LCD1.5' in nets['GND']
    assert 'LCD1.3' in nets['CONTRAST']
    assert 'R1.2' in nets['BACKLIGHT']
    root=ET.fromstring(d['image']['svg'])
    connected={n.attrib['data-pin']:n.attrib['data-net'] for n in root.iter() if 'data-pin' in n.attrib}
    assert connected=={p:n for n,ps in nets.items() for p in ps}
    assert len([n for n in root.iter() if n.attrib.get('class')=='component'])==5
    assert d['validation']['simulation']=='not_run'

@pytest.mark.parametrize('change', ['duplicate_ref','unknown_part','bad_pin','pin_reused','duplicate_net','override','missing_pin_format'])
def test_reject_structural_errors(change):
    d=data()
    if change=='duplicate_ref':d['components'].append(d['components'][0])
    if change=='unknown_part':d['components'][0]['part']='mystery'
    if change=='bad_pin':d['nets'][0]['pins'].append('U1.D99')
    if change=='pin_reused':d['nets'][1]['pins'].append('U1.5V')
    if change=='duplicate_net':d['nets'][1]['name']=d['nets'][0]['name']
    if change=='override':d['custom_parts']={'arduino_uno':{'name':'Override','pins':{'1':'passive'}}}
    if change=='missing_pin_format':d['nets'][0]['pins'].append('U1')
    assert post(d).status_code==422

@pytest.mark.parametrize('change,code',[('short','power_short'),('voltage','voltage_mismatch'),('missing','unconnected_required'),('value','missing_value')])
def test_erc_reports_invalid_draft(change,code):
    d=data()
    if change=='short':d['nets'][0]['pins']+=d['nets'][1]['pins'];del d['nets'][1]
    if change=='voltage':d['components'][2]['value']='12 V'
    if change=='missing':d['nets'][0]['pins'].remove('LCD1.2')
    if change=='value':d['components'][4]['value']=''
    r=post(d);assert r.status_code==200
    assert r.json()['validation']['status']=='draft_with_errors'
    assert code in {e['code'] for e in r.json()['validation']['errors']}
    assert 'ERC errors' in r.json()['image']['svg']

def test_custom_parts_and_output_conflict():
    d={'title':'Custom device test','custom_parts':{'logic':{'name':'Exact user part','pins':{'OUT':'output','GND':'ground'}}},'components':[{'ref':'U1','part':'logic'},{'ref':'U2','part':'logic'}],'nets':[{'name':'SIGNAL','pins':['U1.OUT','U2.OUT']},{'name':'GND','pins':['U1.GND','U2.GND']}]}
    r=post(d);assert r.status_code==200
    assert 'output_conflict' in {e['code'] for e in r.json()['validation']['errors']}
    assert 'custom_unverified' in {e['code'] for e in r.json()['validation']['warnings']}

def test_edit_roundtrip():
    d=post(data()).json()['design'];d['components'][4]['value']='330 ohm';d['components'][0]['position']={'x':240,'y':170}
    r=post(d);assert r.status_code==200
    assert r.json()['design']==d
    assert '330 ohm' in r.json()['image']['svg']
    assert 'data-x="240.0"' in r.json()['image']['svg']

def test_svg_escaping():
    d=data();d['title']='<script>alert(1)</script>';d['components'][0]['value']='<image onload="alert(1)">'
    svg=post(d).json()['image']['svg'];ET.fromstring(svg)
    assert '<script>' not in svg and '<image onload=' not in svg

@pytest.mark.parametrize('prompt',['Arduino Uno with a 16x2 LCD','4-channel LED bank','two-stage RC filter'])
def test_prompt_examples(prompt):
    r=client.post('/v2/draft',json={'prompt':prompt})
    assert r.status_code==200 and not r.json()['validation']['errors']

@pytest.mark.parametrize('prompt',['Arduino Uno with a 16x2 LCD and a relay','ESP32 with LCD','Arduino Uno with a 16x2 LCD at 12 V','100-channel LED bank'])
def test_no_silent_component_or_constraint_drops(prompt):
    assert client.post('/v2/draft',json={'prompt':prompt}).status_code==422

def test_explicit_custom_connections():
    prompt='component V1 dc_source 5 V\ncomponent R1 resistor 1 kohm\ncomponent C1 capacitor 100 nF\nnet IN V1.+ R1.1\nnet OUT R1.2 C1.1\nnet GND C1.2 V1.-'
    r=client.post('/v2/draft',json={'prompt':prompt});assert r.status_code==200
    assert not r.json()['validation']['errors']

def test_auth_all_write_endpoints(monkeypatch):
    monkeypatch.setenv('CIRCUIT_API_KEY','secret-test')
    for path,body in [('/v2/render',{'design':data()}),('/v2/draft',{'prompt':'controller_lcd'}),('/v2/validate',data())]:
        assert client.post(path,json=body).status_code==401
        assert client.post(path,json=body,headers={'X-API-Key':'secret-test'}).status_code==200

@pytest.mark.parametrize('mode',['valid','clarify','malformed','offline'])
def test_ai_proposal_boundary(monkeypatch,mode):
    monkeypatch.setenv('OLLAMA_URL','http://model.test');monkeypatch.setenv('OLLAMA_MODEL','model')
    async def fake(self,url,**kwargs):
        assert kwargs['json']['format']['type']=='object'
        request=json.loads(kwargs['json']['messages'][1]['content'])
        assert request['previous_design']['title']==data()['title']
        if mode=='offline':raise httpx.ConnectError('offline')
        proposal={'design':data() if mode=='valid' else None,'unresolved':[] if mode=='valid' else ['Which controller?'],'explanation':'Review draft'}
        return httpx.Response(200,json={'message':{'content':'bad JSON' if mode=='malformed' else json.dumps(proposal)}},request=httpx.Request('POST',url))
    with patch.object(httpx.AsyncClient,'post',fake):
        r=client.post('/v2/draft',json={'prompt':'Use a 330 ohm backlight resistor','parser':'ollama','previous_design':data()})
    assert r.status_code=={'valid':200,'clarify':422,'malformed':502,'offline':502}[mode]

def test_unconfigured_ai(monkeypatch):
    monkeypatch.delenv('OLLAMA_MODEL',raising=False)
    assert client.post('/v2/draft',json={'prompt':'Make a circuit','parser':'ollama'}).status_code==503

def test_png_and_limits():
    r=post(data(),image_format='png');assert r.status_code==200
    png=base64.b64decode(r.json()['image']['base64']);assert png[:8]==b'\x89PNG\r\n\x1a\n'
    assert max(struct.unpack('>II',png[16:24]))<=4096
    d=data();d['components']=[{'ref':f'R{i}','part':'resistor','value':'1 kohm'} for i in range(201)]
    assert post(d).status_code==422

def test_large_design_and_long_net():
    d=led_bank(64);r=post(d.model_dump());assert r.status_code==200
    assert len(r.json()['design']['components'])==129
    assert not r.json()['validation']['errors']


def test_1000_deterministic_design_variations():
    """1,000 software cases, not 1,000 validated circuit families."""
    rng=random.Random(17)
    for i in range(1000):
        d=[controller_lcd,rc_ladder,lambda:led_bank(rng.randint(1,12))][i%3]().model_dump(exclude_none=True)
        for c in d['components']:
            if c['part']=='resistor':c['value']=f'{rng.randint(220,100000)} ohm'
        model=Design.model_validate(d);checks=check_design(model)
        assert not checks['errors']
        svg,_,_=render_design(model,checks);root=ET.fromstring(svg)
        rendered={n.attrib['data-pin']:n.attrib['data-net'] for n in root.iter() if 'data-pin' in n.attrib}
        assert rendered=={p:n.name for n in model.nets for p in n.pins}

def test_max_component_layout_can_be_reimported():
    d=Design(components=[{'ref':f'U{i}','part':'arduino_uno'} for i in range(200)])
    from app.multi_api import result_for
    result=result_for(d)
    assert len(Design.model_validate(result['design']).components)==200
