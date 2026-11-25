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


def test_reference_first_declarations_and_unnamed_connections():
    prompt = """V1 is a 5 V DC source. R1 is a 330 ohm resistor. D1 is a red LED.
    Join V1 positive and R1.1. Connect R1.2 to D1.A on net N1.
    Join D1.K to V1 negative."""
    response=submit(prompt)
    assert response.status_code==200,response.text
    assert {n['name']:set(n['pins']) for n in response.json()['design']['nets']}=={
        'N2':{'V1.+','R1.1'},'N1':{'R1.2','D1.A'},'N3':{'D1.K','V1.-'},
    }


def test_unnamed_join_extends_named_net_without_inventing_a_second_node():
    prompt=PROMPT.replace('R2.2, R3.1, C4.1, and J2.1 on net OUTPUT',
                          'R2.2 and R3.1 on net OUTPUT. Join R3.1, C4.1 and J2.1')
    result=submit(prompt)
    assert result.status_code==200,result.text
    assert next(n['pins'] for n in result.json()['design']['nets'] if n['name']=='OUTPUT')==[
        'R2.2','R3.1','C4.1','J2.1'
    ]


def test_unnamed_join_cannot_short_two_named_nets_silently():
    result=submit(PROMPT+' Join R2.2 and R3.2.')
    assert result.status_code==422
    assert 'OUTPUT, RETURN' in result.json()['detail']
