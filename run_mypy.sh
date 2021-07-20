# mypy is special in that they distribute a C extension only for CPython,
# and while it looks like you are supposed to be able to do
# MYPY_USE_MYPYC pip install --no-binary mypy
# to compile the C extension yourself, I get an error when I try that.
# So instead, clone their repo and build it from there.

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 python_executable"
    exit 1
fi

BINARY=$1

set -u
set -x

ENV=/tmp/macrobenchmark_env
rm -rf $ENV
python3 -m venv -p $BINARY $ENV
PYTHON=$ENV/bin/python

#$PYTHON -m pip install pyperformance

rm -rf /tmp/mypy
git clone --depth 1 --branch v0.790 https://github.com/python/mypy/ /tmp/mypy
pushd /tmp/mypy
$PYTHON -m pip install -r mypy-requirements.txt
$PYTHON -m pip install --upgrade setuptools
git submodule update --init mypy/typeshed
$PYTHON setup.py --use-mypyc install
popd

OPTS=" \
    --manifest $(dirname $0)/benchmarks/MANIFEST \
    --venv $ENV \
    --benchmarks mypy \
"
# XXX Run 50 loops each instead of the default 20.
$PYTHON -m pyperformance run $OPTS \
    #--output results.json
$PYTHON -m pyperformance run $OPTS \
    #--append results.json
$PYTHON -m pyperformance run $OPTS \
    #--append results.json
