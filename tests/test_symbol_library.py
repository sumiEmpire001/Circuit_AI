"""End-to-end symbol and wiring checks with independently written expected pins."""
import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.symbol_library import drawings, names, registry
from scripts.routing_measurement import measure
from scripts.routing_stress import snapshot

client = TestClient(app)

REGULATOR = """Title: 5 V test rail with a switched indicator.
Use a 9 V DC source named V1, a L7805 named U1, a SW_Push named S1, a 330 ohm resistor named R1, a red LED named D1, a 330 nF capacitor named C1 and a 100 nF capacitor named C2.
Connect V1 positive to U1 IN and C1 pin 1 on net VIN.
Connect V1 negative to U1 GND, D1 K, C1 pin 2 and C2 pin 2 on net GND.
Connect U1 OUT to S1 pin 1 and C2 pin 1 on net V5.
Connect S1 pin 2 to R1 pin 1 on net ENABLE.
Connect R1 pin 2 to D1 A on net LED_A."""

SENSOR = """Title: Bare BME280 in I2C mode with a four-pin host connector.
Use a 3.3 V DC source named V1, a BME280 named U1, a connector4 named J1, a 4.7 kohm resistor named RX and a 4.7 kohm resistor named RY, a 100 nF capacitor named C1 and a 100 nF capacitor named C2.
Connect V1 positive to U1 VDD, U1 VDDIO, U1 CSB, RX pin 1, RY pin 1, J1 pin 1, C1 pin 1 and C2 pin 1 on net V33.
Connect V1 negative to U1 pin 1, U1 pin 7, U1 SDO, J1 pin 2, C1 pin 2 and C2 pin 2 on net GND.
Connect U1 SDI to RX pin 2 and J1 pin 3 on net SDA.
Connect U1 SCK to RY pin 2 and J1 pin 4 on net SCL."""

TRANSISTOR = """Title: Common-emitter NPN indicator with a defined low input.
Use a 5 V DC source named V1, a 2N3904 named Q1, a 1 kohm resistor named R1, a 10 kohm resistor named R2, a 470 ohm resistor named R3, a green LED named D1 and a connector2 named J1.
Connect V1 positive to R3 pin 1 on net V5.
Connect R3 pin 2 to D1 A on net ANODE.
Connect D1 K to Q1 C on net COLLECTOR.
Connect J1 pin 1 to R1 pin 1 on net INPUT.
Connect R1 pin 2 to R2 pin 1 and Q1 B on net BASE.
Connect V1 negative to Q1 E, J1 pin 2 and R2 pin 2 on net GND."""

CASES = [
    (REGULATOR, {'VIN': 'V1.+ U1.1 C1.1', 'GND': 'V1.- U1.2 D1.K C1.2 C2.2',
                 'V5': 'U1.3 S1.1 C2.1', 'ENABLE': 'S1.2 R1.1', 'LED_A': 'R1.2 D1.A'}),
    (SENSOR, {'V33': 'V1.+ U1.8 U1.6 U1.2 RX.1 RY.1 J1.1 C1.1 C2.1',
              'GND': 'V1.- U1.1 U1.7 U1.5 J1.2 C1.2 C2.2',
              'SDA': 'U1.3 RX.2 J1.3', 'SCL': 'U1.4 RY.2 J1.4'}),
    (TRANSISTOR, {'V5': 'V1.+ R3.1', 'ANODE': 'R3.2 D1.A', 'COLLECTOR': 'D1.K Q1.3',
                  'INPUT': 'J1.1 R1.1', 'BASE': 'R1.2 R2.1 Q1.2', 'GND': 'V1.- Q1.1 J1.2 R2.2'}),
]


@pytest.mark.parametrize('prompt, expected', CASES, ids=['regulator', 'sensor', 'transistor'])
def test_long_prompt_selects_correct_symbols_and_routes(prompt, expected):
    response = client.post('/v2/draft', json={'prompt': prompt})
    assert response.status_code == 200, response.text[:500]
    draft = response.json()
    expected = {net: set(pins.split()) for net, pins in expected.items()}
    assert {n['name']: set(n['pins']) for n in draft['design']['nets']}==expected
    assert not draft['validation']['errors']
    assert not draft['routing_audit']['conflicts']
    assert measure(snapshot(draft['image']['svg']), expected)['strict_passed']==len(expected)
    assert len(draft['symbol_parts']) >= 1


def test_symbol_only_preserves_datasheet_pin_labels_and_native_reference():
    response = client.post('/v2/draft',json={'prompt':'Draw the schematic symbol for BME280.'})
    assert response.status_code==200
    draft = response.json()
    assert not draft['design']['nets']
    nodes = ET.fromstring(draft['image']['svg']).iter()
    assert {node.get('data-pin-label'):node.text for node in nodes
            if node.get('data-pin-label')} == {
                'U1.1':'GND','U1.2':'CSB','U1.3':'SDI','U1.4':'SCK',
                'U1.5':'SDO','U1.6':'VDDIO','U1.7':'GND','U1.8':'VDD',
            }


def test_ambiguous_pin_label_needs_physical_number():
    response = client.post('/v2/draft',json={'prompt':SENSOR.replace('U1 pin 1','U1 GND')})
    assert response.status_code==422
    assert 'Ambiguous pin label U1.GND' in response.json()['detail']


def test_generated_registry_has_independent_geometry_and_stable_exact_names():
    entries = registry()
    art = {key:data for chunk in range(4) for key,data in drawings(chunk).items()}
    assert len({repr(data['shapes']) for data in art.values()})>1000
    assert {key for _,_,_,key in entries.values()}==art.keys()
    for key, (origin,_,_,_) in entries.items():
        assert names()[origin.casefold()]==(key,)
    response = client.get('/v2/symbols?q=BME280')
    assert response.status_code==200
    assert next(iter(response.json()['parts'].values()))['name']=='BME280'
