set -e

if [ -z "$1" ]; then
    echo "Usage: $0 python_executable"
    exit 1
fi

BINARY=$1

set -u
set -x

#python3 -m pip install pyperformance
python3 -m pyperformance run \
    --manifest $(dirname $0)/benchmarks/MANIFEST \
    --python $BINARY \
    --output results.json
