"""Reproduce the independently trained classifier weights."""
import json
from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
def train():
    corpus = json.loads((ROOT/'training/corpus_v1.json').read_text())
    counts = {label: dict(Counter(t for row in rows for t in re.findall(r'[a-z0-9]+', row.lower()))) for label, rows in corpus.items()}
    return dict(version='CircuitLM-0.5', smoothing=0.1, counts=counts, totals={k:sum(v.values()) for k,v in counts.items()}, vocabulary=sorted({t for v in counts.values() for t in v}), documents=sum(map(len,corpus.values())))
if __name__ == '__main__':
    (ROOT/'app/circuitlm_weights.json').write_text(json.dumps(train(),indent=2)+'\n')
