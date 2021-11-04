#!/usr/bin/env bash

set -e

function verbose() {
    (
    set -x
    "$@"
    )
}

now=$(date --utc +'%Y%m%d-%H%M%S')
outdir=results


# Extract values from env vars.
pyperformance=pyperformance
clone_pp='no'
if [ -n "$PYPERFORMANCE" ]; then
    pyperformance=$PYPERFORMANCE
    if [ ! -e $pyperformance ]; then
        clone_pp='yes'
    fi
fi
if [ -z "$WITH_MYPYC" ] || [ "$WITH_MYPYC" = 'no' ] || [ "$WITH_MYPYC" -eq 0 ]; then
    mypy=
    reset_mypy='no'
elif [ "$WITH_MYPYC" = 'yes' ] || [ "$WITH_MYPYC" -eq 1 ]; then
    mypy=/tmp/mypy
    reset_mypy='yes'
elif [ -e "$WITH_MYPYC" ]; then
    mypy=$WITH_MYPYC
    reset_mypy='no'
else
    mypy=$WITH_MYPYC
    reset_mypy='yes'
fi

set -u


# Parse the command-line.
target_python=
reset_venv='no'
venv=
prev=
for arg in "$@"; do
    if [ "$prev" = "-p" -o "$prev" = "--python" ]; then
        target_python=$arg
    elif [ "$prev" = "--venv" ]; then
        venv=$arg
    fi
    prev=$arg
done
if [ -z "$target_python" ]; then
    if [ -z "$venv" ]; then
        >&2 echo "ERROR: missing -p/--python arg"
        exit 1
    fi
    target_python=$venv/bin/python3
fi
if [ -z "$venv" ]; then
    reset_venv='yes'
    venv=venv/pyston-python-macrobenchmarks
elif [ ! -e "$venv" ]; then
    reset_venv='yes'
fi


# Set up the execution environment.
if [ $reset_venv = 'yes' ]; then
    verbose rm -rf $venv
    verbose $target_python -m venv $venv
fi
if [ $clone_pp = 'yes' ]; then
    verbose git clone https://github.com/python/pyperformance "$pyperformance"
fi
verbose $venv/bin/pip install --upgrade "$pyperformance"
if [ $reset_mypy = 'yes' ]; then
    verbose rm -rf $mypy
    verbose git clone --depth 1 --branch v0.790 https://github.com/python/mypy/ $mypy

    pushd $mypy
    verbose $venv/bin/pip install -r mypy-requirements.txt
    verbose $venv/bin/pip install --upgrade setuptools
    verbose git submodule update --init mypy/typeshed
    verbose $venv/bin/python setup.py --use-mypyc install
    popd
fi
verbose mkdir -p $outdir


# Run the benchmarks.
verbose $venv/bin/python3 -m pyperformance run \
    --venv $venv \
    --manifest benchmarks/MANIFEST \
    --output $outdir/results-$now.json \
    "$@"
