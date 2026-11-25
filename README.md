# Circuit AI — independent model development branch

CircuitLM-0.1 is an experimental locally trained intent classifier, not a general circuit synthesis model. No external model API is used. See [training documentation](training/README.md).

## Run

```sh
pip install -r requirements-dev.txt
python training/train.py
python -m pytest -q
uvicorn app.main:app --port 8000
```

Open `/studio` or `/docs`. Configure `CIRCUIT_API_KEY` in the server environment to protect generation, rendering and validation. Send it as `X-API-Key`. Do not commit real keys.

## API

POST `/v2/draft` with `{"prompt":"Arduino Uno with a 16x2 LCD","parser":"local"}`. Local mode accepts reviewed aliases for Uno LCD, four-channel LED bank and two-stage RC filter. Unsupported or additional constraints are rejected. Built-in mode accepts explicit component/net lines and existing examples. `/v2/render` and `/v2/validate` accept editable designs. `/v1/generate` retains explicit named SI parameters for LED, divider and RC circuits. Remote parser values are rejected. Conversational revisions are not supported.

Outputs are draft schematics, not physically validated designs. No simulation or universal synthesis. Runtime OpenAPI at `/openapi.json` is authoritative; the checked-in snapshot is historical until regenerated. Existing examples and validation limits remain unchanged. This branch is not deployed.
