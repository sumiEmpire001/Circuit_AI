import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

CASES=[
 ('led','builtin','5V LED with 330 ohm resistor',3,3),
 ('rc','builtin','rc_ladder',5,4),
 ('bridge','local','four diode bridge rectifier',7,4),
 ('lcd','local','Arduino Uno with a 16x2 LCD',5,10),
 ('servo','builtin','mega_ldr_servo',6,5),
 ('ledbank','builtin','4-channel LED bank',9,6),
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
            results.append(dict(case=label,components=parts,nets=nets,routed=len(data['routed_nets']),label_only=len(data['unrouted_nets']),contacts=len(data['routing_audit']['conflicts'])))
            (out/'results.json').write_text(json.dumps(results,indent=2))
            print(results[-1],flush=True)
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(out/'mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors,errors
        browser.close()
if __name__=='__main__':main()
