import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PROMPT = """Title: Adjustable divider with RC output.
Use a 5 V DC source named V1, a 22 kΩ resistor named R2, and a 3.3 kΩ resistor named R3.
Use a 22 nF capacitor named C4 and a connector named J2.
Connect V1 positive to R2 pin 1 on net SUPPLY.
Connect R2.2, R3.1, C4.1, and J2.1 on net OUTPUT.
Connect V1 negative, R3 pin 2, C4 pin 2, and J2 pin 2 on net RETURN."""


def submit(prompt):
    return client.post('/v2/draft',json={'parser':'local','prompt':prompt})


def test_unfamiliar_pin_prose_preserves_values_nets_and_polarity():
    response = submit(PROMPT)
    assert response.status_code==200, response.text
    result = response.json()
    assert {c['ref']:c['value'] for c in result['design']['components']} == {
        'V1':'5 V', 'R2':'22 kohm', 'R3':'3.3 kohm', 'C4':'22 nF', 'J2':'',
    }
    assert {n['name']:set(n['pins']) for n in result['design']['nets']} == {
        'SUPPLY': {'V1.+','R2.1'},
        'OUTPUT': {'R2.2','R3.1','C4.1','J2.1'},
        'RETURN': {'V1.-','R3.2','C4.2','J2.2'},
    }
    assert not result['validation']['errors']


@pytest.mark.parametrize('change',[
    lambda p:p+' Make the output exactly 3.3 V.',
    lambda p:p+' Connect R2.2 to J2.2 on net SHORT.',
    lambda p:p.replace('J2 pin 2','J2 pin 7'),
    lambda p:p.replace('22 nF','22 kg'),
    lambda p:p.replace('22 nF','22 MF'),
    lambda p:p.replace('22 kΩ resistor named R2','22 kΩ resistor named r3'),
])
def test_unrecognized_conflicting_and_incorrect_constraints_are_rejected(change):
    assert submit(change(PROMPT)).status_code==422


def test_timer_draft_and_verified_supply_range():
    result = submit('Make an NE555P astable timer.').json()
    design=result['design']
    assert len(design['nets'])==6
    assert result['routing_audit']['continuous_nets']==sorted(n['name'] for n in design['nets'])
    assert not result['validation']['errors']
    next(c for c in design['components'] if c['ref']=='V1')['value']='3.3 V'
    assert any(e['code']=='voltage_mismatch' for e in client.post('/v2/validate',json=design).json()['errors'])
