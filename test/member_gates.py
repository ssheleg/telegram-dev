# shared-mechanism: sshlg-skills/member-gates-v1
# diverges: none
# Copies: telegram-dev, xr-dev, web3d-dev; change and verify the family together.
"""Portable owner gates, shared byte-for-byte by the FW02 member wave.

Stdlib only. Release validation checks the current workflow's structural contract,
not arbitrary YAML or shell semantics. Unknown workflow layouts fail closed.
"""
from pathlib import Path
import re
import shlex


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
    pending = None
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        row = cells(line) if line.startswith('|') else []
        separator = bool(row) and all(re.fullmatch(r':?-{3,}:?', c) for c in row)
        if pending is not None:
            if separator and len(row) == width and line.endswith('|'):
                pending = None
                continue
            errors.append(f'{pending}: board header needs an immediate matching separator')
            pending = None
        if line.startswith(('```', '~~~')):
            fenced = not fenced
            width = None
            continue
        if fenced:
            continue
        if not line.startswith('|'):
            width = None
            continue
        first = label(row[0]) if row else ''
        if first.lower() == 'row':
            errors.append(f'{number}: board Row header unsupported; use ID for declarations')
            width = None
            continue
        if first.lower() == 'id':
            width, declares, pending = len(row), True, number
            continue
        if separator:
            if width is not None:
                errors.append(f'{number}: board misplaced separator')
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
    if pending is not None:
        errors.append(f'{pending}: board header needs an immediate matching separator')
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
    if re.search(r'^\s*(?:-\s*)?<<\s*:', active, re.M):
        return ['release ancestry guard merge keys require explicit review']
    if re.search(r'^\s*(?:-\s*)?[\'"][^\'"\n]+[\'"]\s*:', active, re.M):
        return ['release ancestry guard quoted mapping keys require explicit review']
    if len(re.findall(r'^jobs:', active, re.M)) != 1 or len(re.findall(r'^  release:', active, re.M)) != 1:
        return ['release ancestry guard job is missing or ambiguous']
    if re.search(r'^(?:defaults:|    defaults:)', active, re.M):
        return ['release ancestry guard defaults require explicit review']
    job = re.search(r'^  release:\s*\n(?P<body>.*?)(?=^  [\w-]+:|\Z)', active, re.M | re.S)
    if not job:
        return ['release job missing or unsupported layout']
    body = job.group('body')
    if len(re.findall(r'^    steps:', body, re.M)) != 1:
        return ['release ancestry guard steps are missing or ambiguous']
    if re.search(r'^    continue-on-error:\s*(?!false\s*(?:#.*)?$)\S', body, re.M):
        errors.append('release ancestry failure ignored at job scope')
    steps = re.split(r'(?=^      - )', body, flags=re.M)[1:]
    full, checkouts, guards = [], [], []
    for index, step in enumerate(steps):
        if re.search(r'^(?:      - |        )uses:\s*actions/checkout@', step, re.M):
            checkouts.append(index)
            options = re.findall(r'^        with:\s*\n((?:          [^\n]*\n?|\n)*)', step, re.M)
            depth = re.findall(r'^          fetch-depth:\s*(.*?)\s*(?:#.*)?$', options[0], re.M) if len(options) == 1 else []
            uses = re.findall(r'^(?:      - |        )uses:', step, re.M)
            if (len(uses) == 1 and len(re.findall(r'^        with:', step, re.M)) == 1
                and not re.search(r'^(?:      - |        )if:', step, re.M)
                and not re.search(r'^(?:      - |        )continue-on-error:\s*(?!false\s*(?:#.*)?$)\S', step, re.M)
                and len(depth) == 1 and depth[0].strip('\'"') == '0'):
                full.append(index)
        run = re.search(r'^        run:\s*\|[-+]?\s*\n((?:          [^\n]*\n?|\n)*)', step, re.M)
        if not run:
            continue
        shell = run.group(1)
        guard = re.search(r'^          if ! git merge-base --is-ancestor HEAD [\'"]origin/\$DEF[\'"]; then\s*\n(?P<failure>.*?)(?=^          fi\s*$)', shell, re.M | re.S)
        if not guard:
            continue
        guards.append(index)
        # This is the supported shell setup, not a substring hunt through arbitrary
        # programs. Unknown setup/control flow must be reviewed with new fixtures.
        prefix = [line.strip() for line in shell[:guard.start()].splitlines() if line.strip()]
        expected = ['set -eu', 'DEF="$(gh api "repos/$GITHUB_REPOSITORY" --jq .default_branch)"',
                    'git fetch --no-tags origin "$DEF"']
        if prefix != expected or len(re.findall(r'^(?:      - |        )run:', step, re.M)) != 1:
            errors.append('release ancestry guard has unsupported setup or duplicate run')
        commands = [line.strip() for line in guard.group('failure').replace('\\\n', '').splitlines() if line.strip()]
        try:
            refusal = shlex.split(commands[-1], comments=True) == ['exit', '1']
            for command in commands[:-1]:
                tokens = list(shlex.shlex(command, posix=True, punctuation_chars=';&|'))
                if not tokens or tokens[0] != 'echo' or any(t and set(t) <= set(';&|') for t in tokens) or '$(' in command or '`' in command:
                    refusal = False
        except (ValueError, IndexError):
            refusal = False
        if not refusal:
            errors.append('release ancestry guard refusal has unsupported control flow')
        shell_option = re.findall(r'^(?:      - |        )shell:\s*(.*?)\s*$', step, re.M)
        if shell_option and shell_option != ['bash']:
            errors.append('release ancestry guard shell requires explicit review')
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
