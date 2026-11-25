import json
from pathlib import Path
from app.circuitlm import classify, weights
from training.train import train

def test_reproducible_weights():
    assert train() == weights()

def test_recorded_holdout():
    report = json.loads((Path(__file__).resolve().parents[1]/'training/evaluation.json').read_text())
    assert all(classify(row['prompt']) == row['expected'] for row in report['results'])

def test_unknown_vocabulary():
    assert classify('zzzzzz qqqqqq') == 'unsupported'
