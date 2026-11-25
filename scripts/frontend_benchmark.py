import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

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
def main():
    out=Path('frontend-results');out.mkdir(exist_ok=True)
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
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
            page.locator('#canvas').screenshot(path=str(out/(label+'.png')))
            results.append(dict(case=label,components=parts,nets=nets,routed=len(data['routed_nets']),label_only=len(data['unrouted_nets']),contacts=len(data['routing_audit']['conflicts']),continuous=len(data['routing_audit']['continuous_nets']),interrupted=len(data['routing_audit']['interrupted_nets'])))
            (out/'results.json').write_text(json.dumps(results,indent=2))
            print(results[-1],flush=True)
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(out/'mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors,errors
        browser.close()
if __name__=='__main__':main()
