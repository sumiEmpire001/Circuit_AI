from math import isclose, pi
import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient

from app.image_reference import ADC_PROMPT
from app.main import app
from app.route_repair import compact_net_labels

client=TestClient(app)
RC="""Use a 5 V DC source named V1, a 1 kohm resistor named R1, and a 100 nF capacitor named C1.
Connect V1 positive to R1 pin 1 on net INPUT.
Connect R1 pin 2 to C1 pin 1 on net OUT.
Connect C1 pin 2 to V1 negative on net RETURN."""


def draft(prompt):
    return client.post('/v2/draft',json={'prompt':prompt,'parser':'local'})


def test_image_adc_long_prompt_wires_parallel_bus_and_analog_input():
    response=draft(ADC_PROMPT)
    assert response.status_code==200,response.text
    result=response.json()
    nets={n['name']:set(n['pins']) for n in result['design']['nets']}
    for bit in range(8):
        assert nets[f'DB{bit}']=={f'U1.{21+bit}',f'U2.{18-bit}'}
    assert nets['TEMP_ANALOG']=={'U2.6','U3.VOUT'}
    assert nets['ADC_CLK_IN']=={'U2.4','R2.1','C4.1'}
    assert 'U2.9' not in set().union(*nets.values())
    assert nets['ADC_RD']=={'U1.17','U2.2'}
    assert not result['validation']['errors']
    assert len(result['routing_audit']['continuous_nets'])==19
    svg=ET.fromstring(result['image']['svg'])
    assert sorted(el.get('data-label-net') for el in svg.iter() if 'data-label-net' in el.attrib)==sorted(nets)


def test_label_only_and_interrupted_nets_keep_all_endpoint_labels():
    svg='<svg><text data-label-net="A">A</text><text data-label-net="B">B</text><text data-label-net="B">B</text><text data-label-net="A">A</text></svg>'
    compact=compact_net_labels(svg,['A'])
    assert compact.count('data-label-net="A"')==1
    assert compact.count('data-label-net="B"')==2


def test_nominal_rc_math_on_recognized_topology_only():
    response=draft(RC)
    assert response.status_code==200,response.text
    result=response.json()
    (calc,)=result['calculations']
    assert calc['net']=='OUT'
    assert isclose(calc['time_constant_s'],0.0001)
    assert isclose(calc['cutoff_hz'],1/(2*pi*0.0001))
    assert draft('Make an NE555P astable timer.').json()['calculations']==[]
