set -e

if [ -z "$1" ]; then
    echo "Usage: $0 python_executable"
    exit 1
fi

BINARY=$1

set -u
set -x

mkdir -p results

ENV=/tmp/benchmark_env

$BINARY -m venv $ENV
$ENV/bin/pip install pyperformance==1.0.5

$ENV/bin/pyperformance run --manifest $(realpath $(dirname $0))/benchmarks/WEB_MANIFEST -o macrobenchmarks.json -b flaskblogging
$ENV/bin/pyperformance run -o pyperformance.json -b richards
