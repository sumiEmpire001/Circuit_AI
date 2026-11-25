from fastapi.testclient import TestClient

from app.image_reference import LCD_PROMPTS
from app.main import app


def test_image_reference_long_prompt_wires_the_full_eight_bit_bus():
    result = TestClient(app).post('/v2/draft', json={'parser':'local','prompt':LCD_PROMPTS[1]})
    assert result.status_code==200, result.text
    body=result.json()
    nets={net['name']:set(net['pins']) for net in body['design']['nets']}
    assert len(nets)==16
    for bit in range(8):
        assert nets[f'D{bit}']=={f'U1.{bit+1}',f'LCD1.{bit+7}'}
    assert nets['RS']=={'U1.22','LCD1.4'}
    assert nets['EN']=={'U1.23','LCD1.6'}
    assert nets['XTAL1']=={'U1.19','X2.1','C2.1'}
    assert nets['XTAL2']=={'U1.18','X2.2','C3.1'}
    assert nets['RST']=={'U1.9','C1.-','R1.1'}
    assert nets['CONTRAST']=={'LCD1.3','RV1.W'}
    assert {'U1.40','U1.31','C1.+'}<=nets['VCC']
    assert {'LCD1.1','LCD1.5','U1.20'}<=nets['GND']
    assert not body['validation']['errors']
    assert set(body['routing_audit']['continuous_nets'])==set(nets)


def test_image_reference_requires_review_for_changed_pin_assignments():
    changed=LCD_PROMPTS[1].replace('P2.1 to LCD RS', 'P2.0 to LCD RS')
    result=TestClient(app).post('/v2/draft', json={'parser':'local','prompt':changed})
    assert result.status_code==422
