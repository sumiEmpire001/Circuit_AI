from math import pi

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
DIVIDER = ('Design a voltage divider. Use a 12 V source. The upper resistor is 33 kohm. '
           'The lower resistor is 10 kohm. Calculate the nominal output voltage.')
FILTER = ('Make a first-order RC low-pass filter; the shunt capacitor CX is 47 nF; '
          'use 5 V at the input; the series resistor RX is 2.2 kΩ.')


@pytest.mark.parametrize('prompt,values,expected_pins,kind,quantity,expected_value', [
    (DIVIDER, {'V1':'12 V','R1':'33 kohm','R2':'10 kohm'},
     {'OUT':{'R1.2','R2.1'},'INPUT':{'V1.+','R1.1'},'RETURN':{'R2.2','V1.-'}},
     'ideal_voltage_divider','output_v',120/43),
    ('Build me a resistive voltage divider; the bottom resistor R9 = 18 kΩ; '
     'use a 9 V DC supply named B1; the top resistor R8 is 82 kohm',
     {'B1':'9 V','R8':'82 kohm','R9':'18 kohm'},
     {'OUT':{'R8.2','R9.1'},'INPUT':{'B1.+','R8.1'},'RETURN':{'R9.2','B1.-'}},
     'ideal_voltage_divider','output_v',1.62),
    (FILTER, {'V1':'5 V','RX':'2.2 kohm','CX':'47 nF'},
     {'OUT':{'RX.2','CX.1'},'INPUT':{'V1.+','RX.1'},'RETURN':{'CX.2','V1.-'}},
     'ideal_rc_lowpass','cutoff_hz',1/(2*pi*2200*47e-9)),
    ('Create a first order RC low pass filter. Use a 3.3 V source named VS. '
     'The series resistor is 4.7 kohm. The shunt capacitor is 0.22 µF. Calculate the nominal cutoff frequency.',
     {'VS':'3.3 V','R1':'4.7 kohm','C1':'0.22 uF'},
     {'OUT':{'R1.2','C1.1'},'INPUT':{'VS.+','R1.1'},'RETURN':{'C1.2','VS.-'}},
     'ideal_rc_lowpass','cutoff_hz',1/(2*pi*4700*0.22e-6)),
])
def test_parameterized_topology_intent(prompt,values,expected_pins,kind,quantity,expected_value):
    response=client.post('/v2/draft',json={'parser':'local','prompt':prompt})
    assert response.status_code==200,response.text
    body=response.json()
    assert not body['validation']['errors']
    assert {c['ref']:c['value'] for c in body['design']['components']}==values
    assert {n['name']:set(n['pins']) for n in body['design']['nets']}==expected_pins
    assert set(body['routing_audit']['continuous_nets'])==expected_pins.keys()
    (estimate,)=body['calculations']
    assert estimate['kind']==kind
    assert estimate['net']=='OUT'
    assert estimate[quantity]==pytest.approx(expected_value)


@pytest.mark.parametrize('prompt', [
    DIVIDER.replace('The lower resistor is 10 kohm. ', ''),
    DIVIDER+' Add a 1 kohm load across the output.',
    DIVIDER+' The bottom resistor is 100 kohm.',
    DIVIDER.replace('12 V', '25 V'),
    DIVIDER.replace('The lower resistor is 10 kohm.', 'The shunt capacitor is 10 nF.'),
    FILTER.replace('47 nF', '47 kohm'),
])
def test_passive_intents_reject_missing_values_and_extra_constraints(prompt):
    assert client.post('/v2/draft',json={'parser':'local','prompt':prompt}).status_code==422


DIVIDER_TARGET = 'Design a voltage divider. Use a 12 V source. Target an output of 3.3 V.'
FILTER_TARGET = 'Create a first-order RC low-pass filter. Use 5 V at the input. Target a cutoff of 1 kHz.'


@pytest.mark.parametrize('prompt,supplied,solved,quantity,target,series,shunt', [
    (DIVIDER_TARGET+' The upper resistor is 33 kohm.', '33 kohm', '12.51724138 kohm',
     'output_v', 3.3, 'R1', 'R2'),
    (DIVIDER_TARGET+' The lower resistor R1 is 11 kohm.', '11 kohm', '29 kohm',
     'output_v', 3.3, 'R2', 'R1'),
    (FILTER_TARGET+' The shunt capacitor is 100 nF.', '100 nF', '1.591549431 kohm',
     'cutoff_hz', 1000, 'R1', 'C1'),
    (FILTER_TARGET+' The series resistor is 10 kohm.', '10 kohm', '15.91549431 nF',
     'cutoff_hz', 1000, 'R1', 'C1'),
])
def test_passive_target_solves_missing_part(prompt,supplied,solved,quantity,target,series,shunt):
    response = client.post('/v2/draft', json={'parser':'local','prompt':prompt})
    assert response.status_code==200,response.text
    body = response.json()
    assert not body['validation']['errors']
    assert {c['value'] for c in body['design']['components']} >= {supplied,solved}
    assert {n['name']:set(n['pins']) for n in body['design']['nets']} == {
        'INPUT': {'V1.+',f'{series}.1'},
        'OUT': {f'{series}.2',f'{shunt}.1'},
        'RETURN': {f'{shunt}.2','V1.-'},
    }
    assert set(body['routing_audit']['continuous_nets']) == {'INPUT','OUT','RETURN'}
    assert any('calculated nominal value' in note for note in body['design']['notes'])
    assert body['calculations'][0][quantity] == pytest.approx(target,rel=1e-8)


@pytest.mark.parametrize('prompt', [
    DIVIDER_TARGET,
    DIVIDER_TARGET+' The upper resistor is 33 kohm. The lower resistor is 10 kohm.',
    DIVIDER_TARGET.replace('3.3 V','12 V')+' The upper resistor is 33 kohm.',
    DIVIDER_TARGET.replace('3.3 V','13 V')+' The upper resistor is 33 kohm.',
    DIVIDER_TARGET+' The upper resistor is 33 kohm. Target an output of 5 V.',
    DIVIDER_TARGET+' The upper resistor is 33 kohm. Add a 1 kohm load.',
    FILTER_TARGET.replace('1 kHz','0 Hz')+' The shunt capacitor is 100 nF.',
    FILTER_TARGET.replace('1 kHz','1 V')+' The shunt capacitor is 100 nF.',
])
def test_passive_target_rejects_invalid_or_incomplete_specification(prompt):
    assert client.post('/v2/draft',json={'parser':'local','prompt':prompt}).status_code==422
