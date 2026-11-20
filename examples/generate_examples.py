"""Run from project root: python -m examples.generate_examples"""
import json
from pathlib import Path
import resvg_py
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for name,prompt in [('voltage-divider','voltage divider; supply_v=5; r1_ohm=10000; r2_ohm=10000'),('led','led; supply_v=5; led_vf=2; led_current_ma=10'),('rc-lowpass','rc lowpass; supply_v=5; r1_ohm=1000; capacitance_f=1e-7')]:
    response=c.post('/v1/generate',json={'prompt':prompt})
    response.raise_for_status()
    d=response.json()
    Path(f'examples/{name}.json').write_text(json.dumps(d,indent=2))
    Path(f'examples/{name}.svg').write_text(d['image']['svg'])
    Path(f'examples/{name}.png').write_bytes(resvg_py.svg_to_bytes(svg_string=d['image']['svg'], zoom=2, dpi=96))
Path('openapi.json').write_text(json.dumps(app.openapi(),indent=2))
