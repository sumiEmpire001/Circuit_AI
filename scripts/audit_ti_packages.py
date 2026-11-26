"""Check reviewed package records against TI package-option addendum text."""
import argparse
import re
from pathlib import Path

from app.package_catalog import PACKAGE_CATALOG


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('datasheets', type=Path, help='Directory of pdftotext -layout output, named by TI family')
    args = parser.parse_args()
    missing = []
    total = 0
    sources = {}
    for spec in PACKAGE_CATALOG.values():
        source = args.datasheets / f'{Path(spec["source"]).stem}.txt'
        if source not in sources:
            sources[source] = source.read_text(encoding='utf-8') if source.is_file() else None
        if sources[source] is None:
            missing.append(f'{spec["mpn"]}: missing {source}')
            continue
        package = re.sub(r'^(PDIP|SOIC|SSOP|SOP|TSSOP)-\d+', r'\1', spec['package'])
        head = rf'^\s*{re.escape(spec["mpn"])}\s+Active\s+Production'
        outline = rf'{re.escape(package)}\s*\|\s*{len(spec["pins"])}\b'
        if package.startswith('TO-263'):
            # The KTT addendum splits the package alias and the count across lines.
            pattern = rf'{head}[^\n]*DDPAK/[^\n]*\n\s*{outline}'
        else:
            pattern = rf'{head}\s+{outline}'
        if re.search(pattern, sources[source], re.MULTILINE):
            total += 1
        else:
            missing.append(f'{spec["mpn"]}: no active {spec["package"]} addendum row')
    print(f'Matched {total} active orderables across {len(sources)} family datasheets.')
    if missing:
        parser.exit(1, '\n'.join(missing) + '\n')


if __name__ == '__main__':
    main()
