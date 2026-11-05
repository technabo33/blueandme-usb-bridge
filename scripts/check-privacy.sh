#!/usr/bin/env bash
# Generically scan published source for machine identifiers, not any real user's values.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
from pathlib import Path
import re, sys
root = Path('.')
mac = re.compile(r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b')
ip = re.compile(r'\b(?:10\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b')
user_path = re.compile(r'/home/[A-Za-z0-9_-]+/')
identifiers = []
for path in sorted(root.rglob('*')):
    if not path.is_file() or any(p in {'.git','__pycache__'} for p in path.parts) or path.suffix in {'.pyc','.img'}:
        continue
    if path.name == 'check-privacy.sh':
        continue
    try:
        s = path.read_text('utf-8')
    except UnicodeError:
        continue
    for found in mac.findall(s):
        if found.upper() not in {'AA:BB:CC:DD:EE:FF','00:00:00:00:00:00'}:
            identifiers.append((str(path),'MAC'))
    for found in ip.findall(s):
        identifiers.append((str(path),'private-IP'))
    for found in user_path.findall(s):
        if found != '/home/usuario/' and found != '/home/user/':
            identifiers.append((str(path),'user-home-path'))
if identifiers:
    for path, reason in identifiers:
        print('REVISAO NECESSARIA:', path, reason, file=sys.stderr)
    sys.exit(1)
print('Verificacao publica: nenhum MAC real, IP privado ou home de utilizador detetado.')
PY
