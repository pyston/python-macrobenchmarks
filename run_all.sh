set -e

if [ -z "$1" ]; then
    echo "Usage: $0 python_executable"
    exit 1
fi

BINARY=$1

set -u
set -x

mkdir -p results

ENV=/tmp/macrobenchmark_env
for bench in flaskblogging djangocms mypy_bench pylint_bench pycparser_bench pytorch_alexnet_inference gunicorn aiohttp thrift_bench; do
    rm -rf $ENV
    virtualenv -p $BINARY $ENV
    $ENV/bin/pip install -r benchmarks/${bench}_requirements.txt
    /usr/bin/time --verbose --output=results/${bench}.out $ENV/bin/python benchmarks/${bench}.py
done
