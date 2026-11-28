import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.routing_measurement import measure
from scripts.routing_stress import snapshot

PROMPT = 'I need a connection for two light bulb one switch one fan I need the circuit diagram for this.'
client = TestClient(app)


def test_circuit_from_fresh_plain_language_prompt():
    response = client.post('/v2/draft', json={'prompt': PROMPT})
    assert response.status_code == 200
    body = response.json()
    expected = {
        'SUPPLY': {'V1.+', 'S1.1'},
        'SWITCHED': {'S1.2', 'L1.1', 'L2.1', 'F1.+'},
        'RETURN': {'V1.-', 'L1.2', 'L2.2', 'F1.-'},
    }
    assert {net['name']: set(net['pins']) for net in body['design']['nets']} == expected
    assert body['validation']['errors'] == []
    assert measure(snapshot(body['image']['svg']), expected)['strict_passed'] == 3
    assert 'L1 · Lamp bulb' in body['image']['svg']
    assert 'L2 · Lamp bulb' in body['image']['svg']
    assert 'F1 · DC fan' in body['image']['svg']
    assert 'Assumed 12 V DC' in body['design']['notes'][0]


@pytest.mark.parametrize('prompt', [
    'Connect two light bulbs and a fan in parallel, all controlled by one switch using 12V DC.',
    'One switch controls 2 light bulbs and a fan with a 12 V DC supply.',
    'Generate a circuit diagram showing 1 fan, two lamps and one switch.',
])
def test_common_wording_produces_the_same_load_connections(prompt):
    response = client.post('/v2/draft', json={'prompt': prompt})
    assert response.status_code == 200
    assert response.json()['design']['nets'] == client.post('/v2/draft', json={'prompt': PROMPT}).json()['design']['nets']


def test_count_and_voltage_variation():
    response = client.post('/v2/draft', json={
        'prompt': 'Draw a circuit for three lamps and 2 DC fans controlled by one switch on a 9 V DC battery.',
    })
    assert response.status_code == 200
    design = response.json()['design']
    assert [p['part'] for p in design['components']].count('lamp_bulb') == 3
    assert [p['part'] for p in design['components']].count('dc_fan') == 2
    assert design['components'][0]['value'] == '9 V'


@pytest.mark.parametrize('prompt', [
    'Two bulbs, one switch and one fan on 230 V AC.',
    'Two bulbs and one fan with two switches.',
    'Two bulbs and one switch plus one fan and a timer.',
])
def test_clarifies_unsupported_or_incompatible_requirements(prompt):
    assert client.post('/v2/draft', json={'prompt': prompt}).status_code == 422
