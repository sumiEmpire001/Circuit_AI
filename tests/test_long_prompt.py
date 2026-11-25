from fastapi.testclient import TestClient
from app.main import app
PROMPT="Create a two-stage RC low-pass filter using a 5V DC source, a 1 kohm resistor R1, a 2.2 kohm resistor R2, and two 100 nF capacitors C1 and C2. Connect V1 positive to R1, R1 to R2 and C1, R2 to C2, and both capacitor returns to V1 negative. Show the output at R2 and C2 and draw junction dots."
def test_five_component_long_prompt():
    r=TestClient(app).post('/v2/draft',json={'prompt':PROMPT,'parser':'local'})
    assert r.status_code==200,r.text
    d=r.json()
    assert len(d['design']['components'])==5
    assert {n['name']:set(n['pins']) for n in d['design']['nets']}=={'IN':{'V1.+','R1.1'},'MID':{'R1.2','R2.1','C1.1'},'OUT':{'R2.2','C2.1'},'GND':{'V1.-','C1.2','C2.2'}}
    assert not d['validation']['errors']
    assert set(d['routed_nets'])|set(d['unrouted_nets'])=={'IN','MID','OUT','GND'}
def test_extra_constraint_not_silently_dropped():
    r=TestClient(app).post('/v2/draft',json={'prompt':PROMPT+' Add an amplifier.','parser':'local'})
    assert r.status_code==422
