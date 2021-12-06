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
virtualenv -p $BINARY $ENV

rm -rf /tmp/mypy
git clone --depth 1 --branch v0.790 https://github.com/python/mypy/ /tmp/mypy
cd /tmp/mypy

$ENV/bin/pip install pyperf==2.2.0
$ENV/bin/pip install -r mypy-requirements.txt
$ENV/bin/pip install --upgrade setuptools
git submodule update --init mypy/typeshed
$ENV/bin/python setup.py --use-mypyc install

cd -
time $ENV/bin/python benchmarks/bm_mypy/run_benchmark.py --legacy 50
time $ENV/bin/python benchmarks/bm_mypy/run_benchmark.py --legacy 50
time $ENV/bin/python benchmarks/bm_mypy/run_benchmark.py --legacy 50

