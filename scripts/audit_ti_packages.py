"""Check reviewed package records against TI package-option addendum text."""
import argparse
import re
from pathlib import Path

from app.package_catalog import (
    EXISTING_HC_VARIANTS, HCT_VARIANTS, LOGIC_FAMILIES, PACKAGE_CATALOG, TI_PACKAGE_CODES,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('datasheets', type=Path, help='Directory of pdftotext -layout output, named by TI family')
    args = parser.parse_args()
    matrix = {**{family: details[-1] for family, details in LOGIC_FAMILIES.items()},
              **EXISTING_HC_VARIANTS, **HCT_VARIANTS}
    missing = []
    total = 0
    for family, suffixes in matrix.items():
        source = args.datasheets / f'{family}.txt'
        if not source.is_file():
            missing.append(f'{family}: missing {source}')
            continue
        text = source.read_text(encoding='utf-8')
        for suffix in suffixes.split():
            key = family + suffix.lower()
            spec = PACKAGE_CATALOG[key]
            code, outline = TI_PACKAGE_CODES[suffix]
            pattern = (rf'^\s*{spec["mpn"]}\s+Active\s+Production\s+'
                       rf'{outline} \({code}\)\s*\|\s*{len(spec["pins"])}\b')
            if re.search(pattern, text, re.MULTILINE):
                total += 1
            else:
                missing.append(f'{spec["mpn"]}: no active {spec["package"]} addendum row')
    print(f'Matched {total} active orderables across {len(matrix)} family datasheets.')
    if missing:
        parser.exit(1, '\n'.join(missing) + '\n')


if __name__ == '__main__':
    main()
