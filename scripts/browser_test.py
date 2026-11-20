"""Optional browser integration test. Run the app on port 8765 first.
Requires playwright and Chromium; BROWSER_EXECUTABLE can override the path.
"""
import os
def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=os.getenv('BROWSER_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(os.getenv('STUDIO_TEST_URL','http://127.0.0.1:8765/studio'))
        page.wait_for_function("document.getElementById('aiStatus').textContent.includes('configured')")
        page.get_by_role('button',name='Load example',exact=True).click();page.wait_for_selector('#canvas svg')
        assert page.locator('#components tr').count()==5
        field=page.locator('#components tr').nth(4).locator('input').nth(1)
        field.fill('330 ohm');field.press('Tab')
        page.get_by_role('button',name='Apply edits & check',exact=True).click()
        page.wait_for_function("document.querySelector('#canvas svg').textContent.includes('330 ohm')")
        # Drag a symbol and verify its position is serialized after the redraw.
        symbol=page.locator('#canvas .component').first;box=symbol.bounding_box()
        previous=page.locator('#jsonEditor').input_value()
        page.mouse.move(box['x']+60,box['y']+40);page.mouse.down();page.mouse.move(box['x']+90,box['y']+70,steps=5);page.mouse.up()
        page.wait_for_function("(previous) => document.getElementById('jsonEditor').value !== previous",arg=previous)
        page.wait_for_function("!document.getElementById('render').disabled")
        for name in ['Download SVG','Download PNG','Download editable JSON']:
            with page.expect_download() as dl:page.get_by_role('button',name=name,exact=True).click()
            download=dl.value;assert download.failure() is None;download.save_as('/tmp/'+download.suggested_filename)
        page.get_by_role('button',name='Run example tests',exact=True).click()
        page.wait_for_function("document.getElementById('testResults').textContent.includes('rc_ladder')")
        assert page.locator('#testResults').inner_text().count('PASS')==3
        page.locator('#import').set_input_files('/tmp/circuit-editable.json')
        page.wait_for_function("document.querySelector('#canvas svg').textContent.includes('330 ohm')")
        page.screenshot(path='/tmp/circuit-studio-desktop.png',full_page=True)
        page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/tmp/circuit-studio-mobile.png',full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors,errors
        print('PASS: browser load, edits, drag, SVG/PNG/JSON downloads, example tests, import, mobile layout, no JS errors')
        browser.close()

if __name__ == "__main__":
    main()
