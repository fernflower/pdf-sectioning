#!/bin/bash
set -e -u

SRC_DIR="$(cd "$(dirname $0)"; pwd)"
ENV_DIR="$SRC_DIR/env"
XUNIT_FILE="$SRC_DIR/tests.xml"

if [ ! -e "$ENV_DIR" ]; then
    virtualenv --system-site-packages "$ENV_DIR"
fi
"$ENV_DIR"/bin/pip install -U -r "$SRC_DIR/requirements.txt"

PYTHONPATH="$SRC_DIR" "$ENV_DIR"/bin/nosetests -v --with-xunit --xunit-file="$XUNIT_FILE" "$SRC_DIR"/tests/*.py
