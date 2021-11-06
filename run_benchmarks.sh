#!/usr/bin/env bash

set -e

function divider() {
    local title=$1
    echo
    echo '##################################################'
    echo "# $title"
    echo '##################################################'
    echo
}

function verbose() {
    (
    set -x
    "$@"
    )
}

function rotate() {
    local force='no'
    if [ "$1" = '--force' ]; then
        shift
        force='yes'
    fi
    local oldfile=$1
    local newfile=$oldfile.bak
    if [ -e $newfile ]; then
        if [ $force = 'no' ]; then
            >&2 echo "ERROR: $newfile already exists"
            exit 1
        fi
        verbose rm $newfile
    fi
    verbose mv $oldfile $newfile
}

now=$(date --utc +'%Y%m%d-%H%M%S')


# Extract values from env vars.
pyperformance=pyperformance
clone_pp='no'
if [ -n "$PYPERFORMANCE" ]; then
    pyperformance=$PYPERFORMANCE
    if [ ! -e $pyperformance ]; then
        clone_pp='yes'
    fi
fi


set -u


# Parse the command-line.
target_python=
venv=
reset_venv='no'
manifest=
outfile=
benchmarks=
mypy='no'
clean=
skip_setup='no'
argv=()
while [ $# -gt 0 ]; do
    arg=$1
    shift
    case "$arg" in
        -p|--python)
            target_python=$1
            shift
            ;;
        --venv)
            venv=$1
            shift
            ;;
        --manifest)
            manifest=$1
            shift
            ;;
        -o|--output)
            outfile=$1
            shift
            ;;
        -b|--benchmarks)
            benchmarks=$1
            shift
            ;;
        --with-mypyc)
            mypy='yes'
            if [ $# -gt 0 ]; then
                case $1 in
                    -*)
                        ;;
                    *)
                        mypy=$1
                        shift
                        ;;
                esac
            fi
            ;;
        --clean)
            if [ "$skip_setup" = 'yes' ]; then
                >&2 echo "ERROR: got --clean and --skip-setup"
                exit 1
            fi
            clean='yes'
            ;;
        --no-clean)
            clean='no'
            ;;
        --skip-setup)
            if [ "$clean" = 'yes' ]; then
                >&2 echo "ERROR: got --clean and --skip-setup"
                exit 1
            fi
            skip_setup='yes'
            clean='no'
            ;;
        *)
            argv+=("$arg")
            ;;
    esac
done

if [ -z "$target_python" ]; then
    target_python=$venv/bin/python3
    if [ -z "$venv" -o ! -e "$target_python" ]; then
        >&2 echo "ERROR: missing -p/--python arg"
        exit 1
    fi
elif [ -z "$venv" ]; then
    venv=venv/pyston-python-macrobenchmarks
    reset_venv='yes'
elif [ ! -e "$venv" ]; then
    reset_venv='yes'
    >&2 echo "WARNING: requested venv does not exist but will be created"
elif [ "$(realpath "$venv/bin/python3")" != "$target_python" ]; then
    reset_venv='yes'
    >&2 echo "WARNING: requested venv is outdated and will be reset"
fi
if [ -z "$manifest" ]; then
    manifest=benchmarks/MANIFEST
fi
if [ -z "$outfile" ]; then
    outdir=results
    outfile=$outdir/results-$now.json
elif [ -d $outfile ]; then
    outdir=$outfile
    outfile=$outdir/results-$now.json
else
    outdir=$(dirname "$outfile")
    if [ -z "$outdir" ]; then
        outdir='.'
        outfile=./$outfile
    fi
fi
if [ -z "$benchmarks" ]; then
    if [ "$mypy" != "no" ]; then
        benchmarks='mypyc'
    else
        benchmarks='default'
    fi
else
    case $benchmarks in
        *mypyc*)
            if [ "$mypy" = 'no' ]; then
                mypy='yes'
            fi
            ;;
        *mypy*)
            benchmarks=${benchmarks/mypy/mypyc}
            ;;
    esac
fi
MYPY_REPO_ROOT=/tmp/mypy
if [ -z "$mypy" -o "$mypy" = 'yes' ]; then
    mypy=MYPY_REPO_ROOT
    reset_mypy='yes'
elif [ "$mypy" == 'no' ]; then
    mypy=
    reset_mypy='no'
elif [ ! -e "$mypy" ]; then
    reset_mypy='yes'
else
    reset_mypy='no'
fi
if [ "$clean" = 'yes' ]; then
    if [ "$skip_setup" != 'no' ]; then
        >&2 echo "ERROR: got --clean and --skip-setup"
        exit 1
    fi
    reset_mypy='yes'
    reset_venv='yes'
fi


# Set up the execution environment.
if [ $skip_setup = 'no' ]; then
    if [ $reset_venv = 'yes' ]; then
        divider "creating the top-level venv at $venv"
        if [ -e "$venv" ]; then
            #verbose rm -rf $venv
            rotate --force "$venv"
        fi
        verbose "$target_python" -m venv "$venv"
    fi
    divider "ensuring setuptools is up-to-date in $venv"
    verbose "$venv/bin/pip" install --upgrade setuptools

    if [ $clone_pp = 'yes' ]; then
        divider "preparing pyperformance at $pyperformance"
        if [ -e "$pyperformance" ]; then
            rotate "$pyperformance"
        fi
        verbose git clone https://github.com/python/pyperformance "$pyperformance"
    fi
    if [ "$pyperformance" = 'pyperformance' ]; then
        divider "installing pyperformance from PyPI"
        verbose "$venv/bin/pip" install --upgrade "$pyperformance"
    else
        divider "installing pyperformance into $venv from $pyperformance"
        verbose "$venv/bin/pip" install --force-reinstall "$pyperformance"
    fi

    if [ -n "$mypy" ]; then
        if [ $reset_mypy = 'yes' ]; then
            divider "getting a fresh copy of the mypy repo"
            if [ -e "$mypy" ]; then
                #verbose rm -rf $mypy
                rotate "$mypy"
            fi
            verbose git clone --depth 1 --branch v0.790 https://github.com/python/mypy/ "$mypy"
            pushd "$mypy"
            verbose git submodule update --init mypy/typeshed
            popd
        fi
        pushd "$mypy"
        divider "installing the mypy requirements into $venv"
        verbose "$venv/bin/pip" install -r mypy-requirements.txt
        divider "building mypyc and installing it in $venv"
        verbose "$venv/bin/python3" setup.py --use-mypyc install
        popd
    fi

    divider "other setup"
    verbose mkdir -p "$outdir"
fi


# Run the benchmarks.
divider "running the benchmarks"
verbose "$venv/bin/python3" -m pyperformance run \
    --venv "$venv" \
    --manifest "$manifest" \
    --benchmarks "$benchmarks" \
    --output "$outfile" \
    "${argv[@]}"
