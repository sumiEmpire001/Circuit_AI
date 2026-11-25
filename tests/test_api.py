import base64
import math
import pytest
from fastapi.testclient import TestClient
from app.main import app, check_graph

client = TestClient(app)
DIV = 'voltage divider; supply_v=5; r1_ohm=10000; r2_ohm=10000'
def generate(prompt=DIV, **kwargs):
    return client.post('/v1/generate',json={'prompt':prompt,**kwargs})

def test_divider():
    r=generate(); assert r.status_code==200
    d=r.json(); assert d['calculations']['output_voltage_v_unloaded']==2.5
    assert 'R1 IN OUT 10000' in d['spice_netlist']
    assert 'R2 OUT 0 10000' in d['spice_netlist']
    assert '<svg' in d['image']['svg']
    assert d['validation']['simulation']=='not_run'

def test_led_nominal():
    d=generate('led; supply_v=5; led_vf=2; led_current_ma=10').json()
    assert d['components'][1]['value']==300
    assert d['calculations']['led_current_ma_nominal']==10
    assert d['spice_netlist'] is None

def test_rc():
    d=generate('rc lowpass; supply_v=5; r1_ohm=1000; capacitance_f=1e-7').json()
    assert math.isclose(d['calculations']['cutoff_hz'],1591.5494309189535)
    assert d['components'][2]['pins']=={'1':'OUT','2':'0'}

def test_png():
    d=generate(image_format='png').json()
    assert base64.b64decode(d['image']['base64']).startswith(b'\x89PNG\r\n\x1a\n')

@pytest.mark.parametrize('prompt',[
    'make a 555 timer','voltage divider; supply_v=5',
    DIV+'; supply_v=12',DIV+'; gain=9',DIV+'; r1_ohm=0',
    'voltage divider; supply_v=NaN; r1_ohm=10; r2_ohm=10',
    'voltage divider; supply_v=5; r1_ohm=inf; r2_ohm=10',
    'led; supply_v=2; led_vf=3; led_current_ma=10',
    'led; supply_v=5; led_vf=2; led_current_ma=10; r1_ohm=10',
    'rc lowpass; supply_v=5; r1_ohm=100; capacitance_f=-1',
    DIV+'; capacitance_f=1e-6', 'voltage divider; supply_v=240; r1_ohm=10; r2_ohm=10'])
def test_invalid_requests(prompt): assert generate(prompt).status_code==422

def test_api_key(monkeypatch):
    monkeypatch.setenv('CIRCUIT_API_KEY','test-only-key')
    assert generate().status_code==401
    assert client.post('/v1/generate',headers={'X-API-Key':'test-only-key'},json={'prompt':DIV}).status_code==200

def test_remote_parser_removed():
    assert generate(parser='ollama').status_code==422

def test_graph_rejects_short():
    with pytest.raises(ValueError):
        check_graph([{'ref':'R1','pins':{'1':'0','2':'0'}}])

def test_graph_rejects_disconnected():
    with pytest.raises(ValueError):
        check_graph([{'ref':str(k),'pins':{'1':a,'2':b}} for k,(a,b) in enumerate([('0','a'),('a','0'),('x','y'),('y','x')])])

def test_ui_and_contract():
    assert client.get('/').status_code==200
    assert '/v1/generate' in client.get('/openapi.json').json()['paths']

@pytest.mark.parametrize('prompt',[DIV,'led; supply_v=5; led_vf=2; led_current_ma=10','rc lowpass; supply_v=5; r1_ohm=1000; capacitance_f=1e-7'])
def test_styles_preserve_circuit(prompt):
    import xml.etree.ElementTree as ET
    grid = generate(prompt).json()
    classic = generate(prompt, diagram_style='classic').json()
    assert grid['diagram_style'] == 'proteus'
    for key in ('components', 'calculations', 'spice_netlist'):
        assert grid[key] == classic[key]
    root = ET.fromstring(grid['image']['svg'])
    assert {p.attrib['data-net'] for p in root.iter() if 'data-net' in p.attrib} == {'IN','OUT','0'}
    labels = [p.text for p in root.iter() if p.tag.endswith('}text')]
    assert all(c['ref'] in labels for c in grid['components'])
    assert 'GND (0)' in labels
    assert 'url(#grid)' in grid['image']['svg']
    assert 'url(#grid)' not in classic['image']['svg']

@pytest.mark.parametrize('style',['proteus','classic'])
def test_style_png(style):
    import struct
    response = generate(diagram_style=style, image_format='png')
    assert response.status_code == 200
    png = base64.b64decode(response.json()['image']['base64'])
    assert png[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', png[16:24])
    assert width > 100 and height > 100


def test_unsupported_style():
    assert generate(diagram_style='unknown').status_code == 422


def test_style_capabilities():
    caps = client.get('/v1/capabilities').json()
    assert caps['default_diagram_style'] == 'proteus'
    assert caps['native_proteus_export'] is False
