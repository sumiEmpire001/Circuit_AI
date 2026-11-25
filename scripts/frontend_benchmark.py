import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from routing_measurement import DOM_SNAPSHOT, measure

CASES=[
 ('led','builtin','5V LED with 330 ohm resistor',3,3),
 ('rc','builtin','rc_ladder',5,4),
 ('rc_long','local','Create a two-stage RC low-pass filter using a 5V DC source, a 1 kohm resistor R1, a 2.2 kohm resistor R2, and two 100 nF capacitors C1 and C2. Connect V1 positive to R1, R1 to R2 and C1, R2 to C2, and both capacitor returns to V1 negative. Show the output at R2 and C2 and draw junction dots.',5,4),
 ('bridge','local','four diode bridge rectifier',7,4),
 ('bridge_long','local',"Create a full-wave bridge rectifier using four 1N4007 diodes D1 D2 D3 D4, a 100 nF capacitor C1, a two-pin isolated low-voltage AC input J1 and a two-pin DC output J2. Connect J1 pin 1 to D1 cathode and D2 anode, J1 pin 2 to D3 cathode and D4 anode, D2 and D4 cathodes to positive output J2 pin 1 and C1 pin 2, and D1 and D3 anodes to negative output J2 pin 2 and C1 pin 1.",7,4),
 ('lcd','local','Arduino Uno with a 16x2 LCD',5,10),
 ('servo','builtin','mega_ldr_servo',6,5),
 ('ledbank','builtin','4-channel LED bank',9,6),
 ('temperature_motor','builtin','temperature_motor',8,9),
]
FIXTURES = json.loads(Path(__file__).with_name('frontend_netlists.json').read_text())
IMAGE_PROMPT = json.loads((Path(__file__).resolve().parents[1] / 'training/corpus_v1.json').read_text())['at89c51_lcd'][1]
REFERENCE_CASES = {'rc_long':'rc', 'bridge_long':'bridge', 'temperature_motor_local':'temperature_motor'}
PIN_PROSE = (
    'Title: Twin RC outputs. Use a 5 V DC source named V1, a 4.7 kΩ resistor named R4, '
    'and a 10 kohm resistor named R5. Use a 100 nF capacitor named C4 and a 220 nF capacitor named C5. '
    'Connect V1 positive, R4.1 and R5 pin 1 on net POWER. Connect R4 pin 2 to C4 pin 1 on net FAST. '
    'Connect R5 pin 2 to C5 pin 1 on net SLOW. Connect V1 negative, C4.2, and C5.2 on net RETURN.'
)
CASES += [
    ('pin_prose_novel','local',PIN_PROSE,5,4),
    ('ne555_astable','local','Make an NE555P astable timer.',8,6),
    ('at89c51_lcd','local',IMAGE_PROMPT,9,16),
    ('temperature_motor_local','local','Control a 6V DC motor using an Arduino Uno, LM35 temperature sensor and L293D driver.',8,9),
    ('ldr','local','Arduino Mega with an LDR light sensor',4,3),
    ('schmitt_inverter','local','Make a 5V SN74HC14N inverter with input and output connectors.',5,4),
]
EXPLICIT_COMPONENTS = {
    'unseen_buffer': 'V1 dc_source 5 V; U1 lm358n; C1 capacitor 100 nF; J1 connector2; J2 connector2',
    'unseen_dual_filter': 'V1 dc_source 5 V; R1 resistor 1 kohm; R2 resistor 2 kohm; C1 capacitor 100 nF; R3 resistor 10 kohm; C2 capacitor 10 nF; J1 connector2',
    'unseen_dual_load': 'V1 dc_source 5 V; R1 resistor 330 ohm; R2 resistor 330 ohm; R3 resistor 10 kohm; R4 resistor 10 kohm; D1 led Red; D2 led Red; Q1 npn; Q2 npn; J1 connector3',
}
for label, component_string in EXPLICIT_COMPONENTS.items():
    components = component_string.split('; ')
    lines = ['component '+component for component in components]
    lines += [f'net {name} {pins}' for name,pins in FIXTURES[label].items()]
    CASES.append((label,'builtin','\n'.join(lines),len(components),len(FIXTURES[label])))

STRESS_CASES = {'ledbank_16': 16, 'ledbank_32': 32, 'ledbank_64': 64}
for label, channels in STRESS_CASES.items():
    FIXTURES[label] = {
        'VCC': ' '.join(['V1.+', *(f'R{i}.1' for i in range(1,channels+1))]),
        'GND': ' '.join(['V1.-', *(f'D{i}.K' for i in range(1,channels+1))]),
        **{f'LED_{i}': f'R{i}.2 D{i}.A' for i in range(1,channels+1)},
    }
    CASES.append((label,'builtin',f'{channels}-channel LED bank',2*channels+1,channels+2))


def main():
    out=Path(os.getenv('STUDIO_RESULTS_DIR','frontend-results'));out.mkdir(exist_ok=True)
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True, executable_path=os.getenv('BROWSER_EXECUTABLE'))
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(os.getenv('STUDIO_TEST_URL','http://127.0.0.1:8765/studio'))
        for label,parser,prompt,parts,nets in CASES:
            page.locator('#parser').select_option(parser)
            page.locator('#prompt').fill(prompt)
            with page.expect_response(lambda r:'/v2/draft' in r.url and r.request.method=='POST',timeout=90000) as req:
                page.locator('#generate').click()
            r=req.value;assert r.ok,(label,r.text())
            data=r.json()
            page.wait_for_function("(n)=>document.querySelectorAll('#canvas .component').length===n",arg=parts)
            page.wait_for_function("!document.getElementById('generate').disabled")
            assert len(data['design']['components'])==parts
            assert len(data['design']['nets'])==nets
            assert not data['validation']['errors'],data['validation']
            assert data['routing_audit']['passed'],data['routing_audit']
            assert page.locator('#canvas [data-pin]').count()==sum(len(n['pins']) for n in data['design']['nets'])
            expected = {name:set(pins.split()) for name,pins in FIXTURES[REFERENCE_CASES.get(label,label)].items()}
            assert {n['name']:set(n['pins']) for n in data['design']['nets']} == expected
            measured = measure(page.locator('#canvas svg').evaluate(DOM_SNAPSHOT), expected)
            page.locator('#canvas').screenshot(path=str(out/(label+'.png')))
            results.append(dict(case=label,components=parts,nets=nets,routed=len(data['routed_nets']),label_only=len(data['unrouted_nets']),contacts=len(data['routing_audit']['conflicts']),continuous=len(data['routing_audit']['continuous_nets']),interrupted=len(data['routing_audit']['interrupted_nets']), **measured))
            (out/'results.json').write_text(json.dumps(results,indent=2))
            print(results[-1],flush=True)
        for result in results:
            assert result['strict_passed'] == result['nets'], result
        page.locator('#parser').select_option('local')
        page.locator('#prompt').fill('Make a 5V SN74HC14N inverter with input and output connectors. Add a relay.')
        with page.expect_response(lambda r:'/v2/draft' in r.url and r.request.method=='POST') as req:
            page.locator('#generate').click()
        assert req.value.status == 422
        page.locator('#status').get_by_text('Request needs clarification.', exact=False).wait_for()
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(out/'mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors,errors
        browser.close()
if __name__=='__main__':main()
