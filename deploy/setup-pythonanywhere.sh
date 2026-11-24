#!/usr/bin/env bash
# Run in a PythonAnywhere Bash console after cloning this repository.
set -euo pipefail
cd "$(dirname "$0")/.."
root=$(pwd -P)
python_bin=${PYTHON_BIN:-python3.11}
"$python_bin" -m venv "$root/.venv"
"$root/.venv/bin/python" -m pip install -r requirements.txt
"$root/.venv/bin/python" - <<'PY'
from app import app
with app.test_client() as client:
    assert client.get('/').status_code == 200, 'Feed did not start'
PY
printf '\nWeb → Add a new web app → Manual configuration. Select Python %s.\n' "$("$python_bin" -c 'import sys;print("%s.%s"%sys.version_info[:2])')"
printf 'Virtualenv: %s/.venv\nWSGI configuration file: replace its contents with these lines, save, then click Reload:\n\n' "$root"
"$python_bin" -c 'import os;print("import sys\nsys.path.insert(0, %r)\nfrom app import app as application" % os.getcwd())'
