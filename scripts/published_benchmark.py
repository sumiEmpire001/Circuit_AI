"""Score natural language and independently supplied routing fixtures in Studio."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from routing_measurement import DOM_SNAPSHOT, measure

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'training' / 'benchmarks' / 'published_v1.json'


def electrical_match(design, case):
    expected_parts = {(c['ref'], c['part'], c['value']) for c in case['components']}
    actual_parts = {(c['ref'], c['part'], c['value']) for c in design['components']}
    expected_nets = {frozenset(pins) for pins in case['nets'].values()}
    actual_nets = {frozenset(n['pins']) for n in design['nets']}
    return {
        'components_and_values_match': actual_parts == expected_parts,
        'terminal_membership_matches': actual_nets == expected_nets,
    }


def explicit_input(case):
    lines = [f'title {case["id"]}']
    for c in case['components']:
        lines.append(f'component {c["ref"]} {c["part"]} {c["value"]}'.rstrip())
    lines.extend(f'net {name} {" ".join(pins)}' for name, pins in case['nets'].items())
    return '\n'.join(lines)


def submit(page, parser, prompt):
    page.locator('#parser').select_option(parser)
    page.locator('#prompt').fill(prompt)
    with page.expect_response(lambda r: r.url.endswith('/v2/draft') and r.request.method == 'POST') as pending:
        page.locator('#generate').click()
    response = pending.value
    page.wait_for_function("!document.getElementById('generate').disabled")
    return response


def run(page, cases, out):
    results = []
    for case in cases:
        response = submit(page, 'local', case['prompt'])
        interpreted = {'status': response.status, 'outcome': 'clarification' if response.status==422 else 'unexpected_error'}
        if response.ok:
            draft=response.json()
            interpreted.update(electrical_match(draft['design'],case))
            matched=interpreted['components_and_values_match'] and interpreted['terminal_membership_matches']
            interpreted['outcome']='exact' if matched and not draft['validation']['errors'] else 'incorrect'
        else:
            interpreted['detail']=response.json().get('detail')
        if interpreted['outcome']=='unexpected_error':
            raise RuntimeError(f'Unexpected local-mode status for {case["id"]}: {response.status}')

        response = submit(page, 'builtin', explicit_input(case))
        if not response.ok:
            raise RuntimeError(f'Explicit fixture rejected for {case["id"]}: {response.status}')
        draft = response.json()
        expected = {name:set(pins) for name,pins in case['nets'].items()}
        assert all(electrical_match(draft['design'],case).values())
        assert {net['name']:set(net['pins']) for net in draft['design']['nets']}==expected
        rendered = page.locator('#canvas svg')
        geometry = measure(rendered.evaluate(DOM_SNAPSHOT), expected)
        page.locator('#canvas').screenshot(path=str(out / f'{case["id"]}.png'))
        results.append({
            'id':case['id'], 'source_url':case['source_url'],
            'interpretation':interpreted, 'expected_nets':len(expected),
            'electrical_rule_errors':draft['validation']['errors'],
            'label_only_nets':draft['routing_audit']['label_only_nets'],
            **geometry,
        })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=FIXTURE,
                        help='Path to the frozen reference JSON. Defaults to the published-v1 pilot.')
    args = parser.parse_args()
    fixture_bytes = args.fixture.read_bytes()
    fixture = json.loads(fixture_bytes)
    case_ids = [case['id'] for case in fixture['cases']]
    if not case_ids or len(set(case_ids)) != len(case_ids):
        parser.error('The fixture must contain at least one case, with a unique id for each case.')
    if any(not case_id or not case_id.replace('_', '').replace('-', '').isalnum() for case_id in case_ids):
        parser.error('Case ids must contain only letters, digits, underscores, or hyphens.')
    out = Path(os.getenv('PUBLISHED_RESULTS_DIR', 'published-results'))
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=os.getenv('BROWSER_EXECUTABLE'))
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.goto(os.getenv('STUDIO_TEST_URL','http://127.0.0.1:8765/studio'))
        results=run(page,fixture['cases'],out)
        browser.close()
    report={
        'fixture_version':fixture['version'],
        'fixture_sha256':hashlib.sha256(fixture_bytes).hexdigest(),
        'prompts_exact':sum(case['interpretation']['outcome']=='exact' for case in results),
        'prompts_total':len(results),
        'routing_nets_passed':sum(case['strict_passed'] for case in results),
        'routing_nets_total':sum(case['expected_nets'] for case in results),
        'cases_with_unintended_contacts':sum(
            any({'foreign terminal', 'ambiguous crossing or overlap'}.intersection(reasons)
                for reasons in case['strict_failures'].values()) for case in results
        ),
        'cases':results,
    }
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
