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

ENV=/tmp/macrobenchmark_env
#time $ENV/bin/python benchmarks/mypy_bench.py 50
#time $ENV/bin/python benchmarks/mypy_bench.py 50
#time $ENV/bin/python benchmarks/mypy_bench.py 50
./run_benchmarks.sh --python $BINARY --venv $ENV --with-mypyc --clean
# XXX Convert results to verbose "time" output.
./run_benchmarks.sh --python $BINARY --venv $ENV --with-mypyc --skip-setup
# XXX Convert results to verbose "time" output.
./run_benchmarks.sh --python $BINARY --venv $ENV --with-mypyc --skip-setup
# XXX Convert results to verbose "time" output.
