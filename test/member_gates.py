"""Portable owner gates, shared byte-for-byte by the FW02 member wave.

Stdlib only. Release validation checks the current workflow's structural contract,
not arbitrary YAML or shell semantics. Unknown workflow layouts fail closed.
"""
from pathlib import Path
import re


def cells(line):
    """Markdown pipes escaped by an odd number of backslashes are cell content."""
    result, start, escapes = [], 0, 0
    for index, char in enumerate(line):
        if char == '|' and escapes % 2 == 0:
            result.append(line[start:index].strip())
            start = index + 1
        escapes = escapes + 1 if char == '\\' else 0
    result.append(line[start:].strip())
    return result[1:-1] if not result[0] and not result[-1] else result


def label(value):
    value = value.strip().strip('*` ')
    link = re.fullmatch(r'\[([^\]]+)\]\([^)]*\)', value)
    return (link.group(1) if link else value).strip('*` ')


def board_errors(text):
    errors, seen, width, declares, count, fenced = [], {}, None, False, 0, False
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if line.startswith(('```', '~~~')):
            fenced = not fenced
            width = None
            continue
        if fenced:
            continue
        if not line.startswith('|'):
            width = None
            continue
        row = cells(line)
        first = label(row[0]) if row else ''
        if first.lower() in ('id', 'row'):
            width, declares = len(row), first.lower() == 'id'
            continue
        if row and all(re.fullmatch(r':?-+:?', c) for c in row):
            if width is not None and len(row) != width:
                errors.append(f'{number}: board row width: separator differs from header')
            continue
        identifier = re.fullmatch(r'[A-Z]{1,4}-\d+[a-z]?', first)
        if width is None:
            if identifier:
                errors.append(f'{number}: board row without ID header: {first}')
            continue
        if len(row) != width or not line.endswith('|'):
            errors.append(f'{number}: board row width: {first} has {len(row)} cells; header declares {width}')
        if not identifier:
            errors.append(f'{number}: board invalid ID: {first!r}')
            continue
        if declares:
            count += 1
            if first in seen:
                errors.append(f'{number}: board duplicate ID {first}; first at {seen[first]}')
            seen[first] = number
    if not count:
        errors.append('board has no declared rows')
    return errors


def release_errors(text):
    """Require the live release job's checkout and unconditional refusing guard.

    Bounded to this family's two-space job/six-space step layout; comments or
    matching text in another job/step cannot satisfy this contract.
    """
    errors = []
    active = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#'))
    job = re.search(r'^  release:\s*\n(?P<body>.*?)(?=^  [\w-]+:|\Z)', active, re.M | re.S)
    if not job:
        return ['release job missing or unsupported layout']
    body = job.group('body')
    if re.search(r'^    continue-on-error:\s*(?!false\s*(?:#.*)?$)\S', body, re.M):
        errors.append('release ancestry failure ignored at job scope')
    steps = re.split(r'(?=^      - )', body, flags=re.M)[1:]
    full, checkouts, guards = [], [], []
    for index, step in enumerate(steps):
        if re.search(r'^(?:      - |        )uses:\s*actions/checkout@', step, re.M):
            checkouts.append(index)
            options = re.search(r'^        with:\s*\n((?:          [^\n]*\n?|\n)*)', step, re.M)
            if (not re.search(r'^(?:      - |        )(?:if|continue-on-error):', step, re.M)
                and options and re.search(r'^          fetch-depth:\s*[\'"]?0[\'"]?\s*(?:#.*)?$', options.group(1), re.M)):
                full.append(index)
        run = re.search(r'^        run:\s*\|[-+]?\s*\n((?:          [^\n]*\n?|\n)*)', step, re.M)
        if not run:
            continue
        shell = run.group(1)
        guard = re.search(r'^          if ! git merge-base --is-ancestor HEAD [\'"]origin/\$DEF[\'"]; then\s*\n(?P<failure>.*?)(?=^          fi\s*$)', shell, re.M | re.S)
        if not guard:
            continue
        guards.append(index)
        if not re.search(r'^\s+exit 1\s*(?:#.*)?$', guard.group('failure'), re.M):
            errors.append('release ancestry guard has no refusing exit')
        if re.search(r'^(?:      - |        )if:', step, re.M):
            errors.append('release ancestry step conditional')
        if re.search(r'^(?:      - |        )continue-on-error:\s*(?!false\s*(?:#.*)?$)\S', step, re.M):
            errors.append('release ancestry failure ignored at step scope')
    if not guards:
        errors.append('release ancestry guard missing from a live run block')
    before = [i for i in checkouts if guards and i < guards[0]]
    if not full or (guards and (not before or before[-1] not in full)):
        errors.append('release full-history checkout missing before ancestry guard')
    return errors


def check(root, fail):
    root = Path(root)
    for relative, inspect, missing in [
        ('docs/evidence/backlog.md', board_errors, 'board missing'),
        ('.github/workflows/release.yml', release_errors, 'release workflow missing'),
    ]:
        try:
            text = (root / relative).read_text(encoding='utf-8')
        except OSError as exc:
            fail(f'{relative}: {missing}: {exc.__class__.__name__}')
            continue
        for error in inspect(text):
            fail(f'{relative}: {error}')
