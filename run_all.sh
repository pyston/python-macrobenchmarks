set -e

if [ -z "$1" ]; then
    echo "Usage: $0 python_executable"
    exit 1
fi

BINARY=$1

ENV=/tmp/macrobenchmark_env
./run_benchmarks.sh --python $BINARY --venv $ENV --benchmarks flaskblogging --clean
# XXX Convert results to verbose "time" output.
for bench in djangocms mypy_bench pylint_bench pycparser_bench pytorch_alexnet_inference gunicorn aiohttp thrift_bench gevent_bench_hub; do
    #/usr/bin/time --verbose --output=results/${bench}.out $ENV/bin/python $(dirname $0)/benchmarks/${bench}.py
    ./run_benchmarks.sh --python $BINARY --venv $ENV --benchmarks $bench --no-clean
    # XXX Convert results to verbose "time" output.
done
