set -e

if [ -z "$2" ]; then
    echo "Usage: $0 python_baseline python_comparison"
    exit 1
fi

PYTHON1=$1
PYTHON2=$2

set -u
set -x

mkdir -p results

ENV1=/tmp/benchmark_env1
ENV2=/tmp/benchmark_env2

$PYTHON1 -m venv $ENV1
$PYTHON2 -m venv $ENV2
$ENV1/bin/pip install pyperformance==1.0.5
$ENV2/bin/pip install pyperformance==1.0.5

$ENV1/bin/pyperformance run --manifest $(realpath $(dirname $0))/benchmarks/WEB_MANIFEST -o macrobenchmarks-baseline.json
$ENV1/bin/pyperformance run -o pyperformance-baseline.json

$ENV2/bin/pyperformance run --manifest $(realpath $(dirname $0))/benchmarks/WEB_MANIFEST -o macrobenchmarks-comparison.json
$ENV2/bin/pyperformance run -o pyperformance-comparison.json

$ENV1/bin/pyperf compare_to pyperformance-baseline.json pyperformance-comparison.json
$ENV1/bin/pyperf compare_to macrobenchmarks-baseline.json macrobenchmarks-comparison.json
