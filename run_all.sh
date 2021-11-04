set -e

if [ -z "$1" ]; then
    echo "Usage: $0 python_executable"
    exit 1
fi

BINARY=$1

set -u

ENV=/tmp/macrobenchmark_env
rm -rf $ENV
export PYPERFORMANCE=
for bench in flaskblogging djangocms mypy_bench pylint_bench pycparser_bench pytorch_alexnet_inference gunicorn aiohttp thrift_bench gevent_bench_hub; do
    ./run_benchmarks.sh --python $BINARY --venv $ENV --benchmarks $bench
    # XXX Convert results to verbose "time" output.
done
