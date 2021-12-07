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
for bench in flaskblogging djangocms mypy pylint pycparser pytorch_alexnet_inference gunicorn aiohttp thrift gevent_hub kinto; do
    case $bench in
        gevent_hub)
            outname=gevent_bench_hub
            ;;
        mypy|pylint|pycparser|thrift|kinto)
            outname=${bench}_bench
            ;;
        *)
            outname=$bench
            ;;
    esac

    rm -rf $ENV
    $BINARY -m venv $ENV
    $ENV/bin/pip install pyperf==2.2.0
    $ENV/bin/pip install -r $(dirname $0)/benchmarks/bm_${bench}/requirements.txt
    /usr/bin/time --verbose --output=results/${outname}.out $ENV/bin/python $(dirname $0)/benchmarks/bm_${bench}/run_benchmark.py --legacy
done
