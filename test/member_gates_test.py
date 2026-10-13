#!/usr/bin/env python3
# shared-mechanism: sshlg-skills/member-gates-test-v1
# diverges: none
# Copies: telegram-dev, xr-dev, web3d-dev; change and verify the family together.
"""Real validator plants for the portable member gate contract; no network."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile

BOARD = '''# Board\n\n| ID | Finding | State |\n|---|---|---|\n| GATE-01 | Board grammar | open |\n| GATE-02 | Release guard | open |\n'''


def run(root):
    env = dict(os.environ)
    env.pop('TGDEV_ROOT', None)
    p = subprocess.run([sys.executable, str(root / 'test/validate.py')], cwd=root,
                       env=env, text=True, capture_output=True)
    return p.returncode, p.stdout + p.stderr


def self_test(root):
    root = Path(root)
    defects = [
        ('missing board', 'board', lambda _: None, 'board missing'),
        ('pipe shifts a row', 'board', lambda t: t.replace('Board grammar', 'Board | grammar'), 'board row width'),
        ('duplicate plain ID', 'board', lambda t: t.replace('GATE-02', 'GATE-01'), 'board duplicate ID'),
        ('duplicate formatted ID', 'board', lambda t: t.replace('GATE-02', '[**GATE-01**](#proof)'), 'board duplicate ID'),
        ('missing ID header', 'board', lambda t: t.replace('| ID |', '| Key |'), 'board row without ID header'),
        ('no declared rows', 'board', lambda t: '\n'.join(l for l in t.splitlines() if 'GATE-' not in l), 'board has no declared rows'),
        ('separator absent', 'board', lambda t: t.replace('|---|---|---|\n',''), 'board header needs'),
        ('separator after data', 'board', lambda t: t.replace('|---|---|---|\n','')+'\n|---|---|---|\n', 'board header needs'),
        ('Row header duplicate declaration', 'board', lambda t: t+'\n| Row | State |\n|---|---|\n| GATE-01 | open |\n', 'board Row header unsupported'),
        ('Row header unique declaration', 'board', lambda t: t+'\n| Row | State |\n|---|---|\n| GATE-03 | open |\n', 'board Row header unsupported'),
        ('ancestry command removed', 'release', lambda t: t.replace('git merge-base --is-ancestor', 'git merge-base-removed --is-ancestor'), 'release ancestry guard'),
        ('ancestry command commented', 'release', lambda t: t.replace('if ! git merge-base', '# if ! git merge-base'), 'release ancestry guard'),
        ('shallow release checkout', 'release', lambda t: t.replace('fetch-depth: 0', 'fetch-depth: 1'), 'release full-history checkout'),
        ('depth in a different job', 'release', lambda t: t.replace('fetch-depth: 0', 'fetch-depth: 1') + '\n  decoy:\n    steps:\n      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 0\n', 'release full-history checkout'),
        ('ancestry step disabled', 'release', lambda t: t.replace('      - name: The tag must be reachable', '      - if: false\n        name: The tag must be reachable'), 'release ancestry step conditional'),
        ('ancestry step failure ignored', 'release', lambda t: t.replace('      - name: The tag must be reachable', '      - continue-on-error: true\n        name: The tag must be reachable'), 'release ancestry failure ignored'),
        ('ancestry refusal removed', 'release', lambda t: re.sub(r'(if ! git merge-base[^\n]+\n.*?\n\s*)exit 1', r'\1exit 0', t, count=1, flags=re.S), 'release ancestry guard has no refusing exit'),
        ('release job failure ignored', 'release', lambda t: t.replace('  release:\n', '  release:\n    continue-on-error: true\n', 1), 'release ancestry failure ignored'),
        ('checkout disabled', 'release', lambda t: t.replace('      - uses: actions/checkout@v4', '      - if: false\n        uses: actions/checkout@v4', 1), 'release full-history checkout'),
        ('checkout depth moved to env', 'release', lambda t: t.replace('        with:\n          ref:', '        env:\n          ref:', 1), 'release full-history checkout'),
        ('duplicate release job', 'release', lambda t: t + '\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo bypass\n', 'release ancestry guard'),
        ('early successful exit', 'release', lambda t: t.replace('          if ! git merge-base', '          exit 0\n          if ! git merge-base', 1), 'release ancestry guard'),
        ('duplicate checkout depth', 'release', lambda t: t.replace('          fetch-depth: 0', '          fetch-depth: 0\n          fetch-depth: 1', 1), 'release full-history checkout'),
        ('duplicate ancestry run', 'release', lambda t: t.replace('      - name: Structural validator', '        run: echo bypass\n\n      - name: Structural validator', 1), 'release ancestry guard'),
        ('early success in refusal branch', 'release', lambda t: t.replace('            exit 1\n          fi\n          echo "$(git rev-parse', '            exit 0\n            exit 1\n          fi\n          echo "$(git rev-parse', 1), 'release ancestry guard'),
        ('shell swallows failure', 'release', lambda t: t.replace('      - name: The tag must be reachable', '      - shell: bash {0} || true\n        name: The tag must be reachable', 1), 'release ancestry guard'),
        ('inline duplicate release', 'release', lambda t: t+'\n  release: {}\n', 'release ancestry guard'),
        ('inline duplicate steps', 'release', lambda t: t.replace('    steps:\n','    steps: []\n    steps:\n',1), 'release ancestry guard'),
        ('inline duplicate checkout options', 'release', lambda t: t.replace('        with:\n','        with: {}\n        with:\n',1), 'release full-history checkout'),
        ('merged ancestry options', 'release', lambda t: t.replace('      - name: The tag must be reachable', '      - <<: {continue-on-error: true}\n        name: The tag must be reachable',1), 'merge keys'),
    ]
    for quote in ('"', "'"):
        defects.extend([
            (f'{quote} quoted release override', 'release', lambda t, q=quote: t+f'\n  {q}release{q}:\n    uses: ./.github/workflows/validate.yml\n', 'quoted mapping keys'),
            (f'{quote} quoted run override', 'release', lambda t, q=quote: t.replace('      - name: Structural validator', f'        {q}run{q}: echo bypass\n\n      - name: Structural validator',1), 'quoted mapping keys'),
            (f'{quote} quoted depth override', 'release', lambda t, q=quote: t.replace('          fetch-depth: 0',f'          fetch-depth: 0\n          {q}fetch-depth{q}: 1',1), 'quoted mapping keys'),
            (f'{quote} quoted steps override', 'release', lambda t, q=quote: t+f'\n    {q}steps{q}: []\n', 'quoted mapping keys'),
        ])
    failures = []
    count = 0
    # One owned temporary parent; each small copy is removed before the next.
    with tempfile.TemporaryDirectory(prefix='member-gates-') as temporary:
        for label, kind, mutate, expect in defects:
            dst = Path(temporary) / 'repo'
            shutil.copytree(root, dst, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '.agent-sync'))
            try:
                board = dst / 'docs/evidence/backlog.md'
                board.parent.mkdir(parents=True, exist_ok=True)
                board.write_text(BOARD)
                baseline, out = run(dst)
                if baseline:
                    failures.append(f'{label}: clean fixture failed: {out}')
                    continue
                target = board if kind == 'board' else dst / '.github/workflows/release.yml'
                before = target.read_text()
                after = mutate(before)
                if before == after:
                    failures.append(f'{label}: plant changed nothing')
                    continue
                if after is None:
                    target.unlink()
                else:
                    target.write_text(after)
                status, out = run(dst)
                count += 1
                if not status or expect not in out:
                    failures.append(f'{label}: expected refusal {expect!r}; status={status}: {out}')
            finally:
                shutil.rmtree(dst)
        for label, content, release_patch in [
            ('escaped pipe', BOARD.replace('Board grammar', r'Board \| grammar'), None),
            ('bold and linked IDs', BOARD.replace('GATE-01', '**GATE-01**').replace('GATE-02', '[GATE-02](#proof)'), None),
            ('different table widths', BOARD + '\n## Second\n\n| ID | State |\n|---|---|\n| GATE-03 | open |\n', None),
            ('explicit failure reporting', BOARD, lambda t: t.replace('      - uses: actions/checkout@v4', '      - continue-on-error: false\n        uses: actions/checkout@v4', 1)),
        ]:
            dst = Path(temporary) / 'repo'
            shutil.copytree(root, dst, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '.agent-sync'))
            try:
                board = dst / 'docs/evidence/backlog.md'
                board.parent.mkdir(parents=True, exist_ok=True)
                board.write_text(content)
                if release_patch:
                    release = dst / '.github/workflows/release.yml'
                    release.write_text(release_patch(release.read_text()))
                status, out = run(dst)
                count += 1
                if status:
                    failures.append(f'{label}: valid control refused: {out}')
            finally:
                shutil.rmtree(dst)
    for failure in failures:
        print('FAIL: ' + failure)
    print(f'member gates: {count} process controls, {len(failures)} failures')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(self_test(Path(__file__).resolve().parent.parent))
